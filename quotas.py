"""
Usage Quotas System for Agentic RAG
====================================

Tracks and enforces user usage quotas for:
- Queries per day
- Uploads per day
- Storage usage
"""

from datetime import datetime, timedelta
from functools import wraps
from flask import session, jsonify
import structlog

logger = structlog.get_logger(__name__)


class QuotaManager:
    """Manages user quotas and enforces limits"""

    def __init__(self, supabase_client, config):
        """
        Initialize quota manager

        Args:
            supabase_client: Supabase client instance
            config: Application configuration
        """
        self.supabase = supabase_client
        self.config = config

    def get_user_quotas(self, user_id, role='user'):
        """
        Get quota limits for a user

        Args:
            user_id: User ID
            role: User role (admin or user)

        Returns:
            Dict with quota limits
        """
        if role == 'admin':
            return {
                'queries_per_day': self.config.QUOTA_ADMIN_QUERIES_PER_DAY,
                'uploads_per_day': self.config.QUOTA_ADMIN_UPLOADS_PER_DAY,
                'storage_mb': self.config.QUOTA_ADMIN_STORAGE_MB
            }
        else:
            return {
                'queries_per_day': self.config.QUOTA_QUERIES_PER_DAY,
                'uploads_per_day': self.config.QUOTA_UPLOADS_PER_DAY,
                'storage_mb': self.config.QUOTA_STORAGE_MB
            }

    def get_current_usage(self, user_id):
        """
        Get current usage for a user

        Args:
            user_id: User ID

        Returns:
            Dict with current usage stats
        """
        if not self.supabase:
            return {
                'queries_today': 0,
                'uploads_today': 0,
                'storage_used_mb': 0
            }

        try:
            today = datetime.now().date()

            # Get queries today
            queries_response = self.supabase.rpc('get_user_queries_count', {
                'p_user_id': user_id,
                'p_date': today.isoformat()
            }).execute()

            queries_today = queries_response.data or 0

            # Get uploads today
            uploads_response = self.supabase.rpc('get_user_uploads_count', {
                'p_user_id': user_id,
                'p_date': today.isoformat()
            }).execute()

            uploads_today = uploads_response.data or 0

            # Get storage usage
            storage_response = self.supabase.rpc('get_user_storage_usage', {
                'p_user_id': user_id
            }).execute()

            storage_bytes = storage_response.data or 0
            storage_mb = round(storage_bytes / (1024 * 1024), 2)

            return {
                'queries_today': queries_today,
                'uploads_today': uploads_today,
                'storage_used_mb': storage_mb
            }

        except Exception as e:
            logger.error("error_getting_usage", user_id=user_id, error=str(e))
            return {
                'queries_today': 0,
                'uploads_today': 0,
                'storage_used_mb': 0
            }

    def check_quota(self, user_id, role, quota_type):
        """
        Check if user has quota remaining

        Args:
            user_id: User ID
            role: User role
            quota_type: Type of quota to check ('query', 'upload', 'storage')

        Returns:
            (bool, dict) - (can_proceed, quota_info)
        """
        quotas = self.get_user_quotas(user_id, role)
        usage = self.get_current_usage(user_id)

        quota_info = {
            'quotas': quotas,
            'usage': usage,
            'remaining': {}
        }

        # Calculate remaining quotas
        quota_info['remaining'] = {
            'queries': quotas['queries_per_day'] - usage['queries_today'],
            'uploads': quotas['uploads_per_day'] - usage['uploads_today'],
            'storage_mb': quotas['storage_mb'] - usage['storage_used_mb']
        }

        # Check specific quota
        if quota_type == 'query':
            can_proceed = usage['queries_today'] < quotas['queries_per_day']
        elif quota_type == 'upload':
            can_proceed = usage['uploads_today'] < quotas['uploads_per_day']
        elif quota_type == 'storage':
            can_proceed = usage['storage_used_mb'] < quotas['storage_mb']
        else:
            can_proceed = True

        return can_proceed, quota_info

    def increment_usage(self, user_id, quota_type, amount=1):
        """
        Increment usage counter

        Args:
            user_id: User ID
            quota_type: Type of quota ('query', 'upload')
            amount: Amount to increment (default 1)

        Returns:
            bool - Success status
        """
        if not self.supabase:
            return True

        try:
            if quota_type == 'query':
                self.supabase.rpc('increment_query_count', {
                    'p_user_id': user_id,
                    'p_count': amount
                }).execute()
            elif quota_type == 'upload':
                self.supabase.rpc('increment_upload_count', {
                    'p_user_id': user_id,
                    'p_count': amount
                }).execute()

            logger.info("quota_incremented", user_id=user_id, quota_type=quota_type, amount=amount)
            return True

        except Exception as e:
            logger.error("error_incrementing_quota", user_id=user_id, quota_type=quota_type, error=str(e))
            return False


# Global quota manager instance
_quota_manager = None


def init_quota_manager(supabase_client, config):
    """Initialize global quota manager"""
    global _quota_manager
    _quota_manager = QuotaManager(supabase_client, config)
    return _quota_manager


def get_quota_manager():
    """Get global quota manager instance"""
    return _quota_manager


# Decorator for quota enforcement
def require_quota(quota_type):
    """
    Decorator to enforce quotas on endpoints

    Args:
        quota_type: Type of quota to check ('query', 'upload', 'storage')

    Usage:
        @app.route('/query', methods=['POST'])
        @require_quota('query')
        def query_endpoint():
            # ... handle query
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not _quota_manager:
                # Quota system not initialized, allow request
                return f(*args, **kwargs)

            user_id = session.get('user_id')
            user_role = session.get('user_role', 'user')

            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401

            # Check quota
            can_proceed, quota_info = _quota_manager.check_quota(user_id, user_role, quota_type)

            if not can_proceed:
                logger.warning(
                    "quota_exceeded",
                    user_id=user_id,
                    quota_type=quota_type,
                    quota_info=quota_info
                )

                return jsonify({
                    'error': f'{quota_type.capitalize()} quota exceeded',
                    'quota_info': quota_info
                }), 429  # Too Many Requests

            # Increment usage after successful check
            result = f(*args, **kwargs)

            # Only increment if request was successful (2xx status)
            if hasattr(result, 'status_code'):
                if 200 <= result.status_code < 300:
                    _quota_manager.increment_usage(user_id, quota_type)
            else:
                # Non-response return, assume success
                _quota_manager.increment_usage(user_id, quota_type)

            return result

        return decorated_function
    return decorator


# Flask route helpers
def get_quota_info_route():
    """
    Get quota information for current user

    Returns:
        JSON response with quota info
    """
    if not _quota_manager:
        return jsonify({'error': 'Quota system not initialized'}), 500

    user_id = session.get('user_id')
    user_role = session.get('user_role', 'user')

    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    quotas = _quota_manager.get_user_quotas(user_id, user_role)
    usage = _quota_manager.get_current_usage(user_id)

    remaining = {
        'queries': quotas['queries_per_day'] - usage['queries_today'],
        'uploads': quotas['uploads_per_day'] - usage['uploads_today'],
        'storage_mb': quotas['storage_mb'] - usage['storage_used_mb']
    }

    return jsonify({
        'success': True,
        'user_id': user_id,
        'quotas': quotas,
        'usage': usage,
        'remaining': remaining,
        'percentage_used': {
            'queries': round((usage['queries_today'] / quotas['queries_per_day']) * 100, 2) if quotas['queries_per_day'] > 0 else 0,
            'uploads': round((usage['uploads_today'] / quotas['uploads_per_day']) * 100, 2) if quotas['uploads_per_day'] > 0 else 0,
            'storage': round((usage['storage_used_mb'] / quotas['storage_mb']) * 100, 2) if quotas['storage_mb'] > 0 else 0
        }
    })
