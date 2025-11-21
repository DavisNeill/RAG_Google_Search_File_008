"""
Configuration Module for Agentic RAG System
============================================

Centralized configuration for all system components including:
- Rate Limiting
- Caching
- Logging
- WebSockets
- Usage Quotas
"""

import os
from datetime import timedelta

class Config:
    """Base configuration"""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB

    # API Keys
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

    # Upload Configuration
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {
        'txt', 'pdf', 'doc', 'docx', 'xlsx', 'pptx', 'csv', 'json', 'md',
        'py', 'js', 'java', 'cpp', 'html', 'xml', 'ipynb'
    }

    # ============================================================================
    # TIER 1: Rate Limiting Configuration
    # ============================================================================

    # Redis Configuration (for rate limiting and caching)
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

    # Rate Limit Settings
    RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'True').lower() == 'true'
    RATELIMIT_STORAGE_URL = REDIS_URL
    RATELIMIT_STRATEGY = 'fixed-window'  # or 'moving-window'
    RATELIMIT_HEADERS_ENABLED = True

    # Default Rate Limits (can be overridden per endpoint)
    RATELIMIT_DEFAULT = "200 per hour"  # General endpoints
    RATELIMIT_AUTH = "10 per minute"     # Auth endpoints (login, signup)
    RATELIMIT_QUERY = "60 per hour"      # Query endpoints (expensive)
    RATELIMIT_UPLOAD = "20 per hour"     # Upload endpoints
    RATELIMIT_ADMIN = "1000 per hour"    # Admin endpoints (higher limit)

    # ============================================================================
    # TIER 1: Logging Configuration
    # ============================================================================

    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = 'json'  # or 'text'
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT = 5

    # Sentry Configuration (optional)
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    SENTRY_ENVIRONMENT = os.environ.get('SENTRY_ENVIRONMENT', 'production')

    # ============================================================================
    # TIER 2: Caching Configuration
    # ============================================================================

    CACHE_TYPE = 'redis'  # or 'simple' for in-memory (dev only)
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    CACHE_KEY_PREFIX = 'agentic_rag_'

    # Cache TTL for different operations
    CACHE_QUERY_TTL = 300          # 5 minutes for query results
    CACHE_DOCUMENT_LIST_TTL = 60   # 1 minute for document lists
    CACHE_USER_LIST_TTL = 120      # 2 minutes for user lists
    CACHE_ANALYTICS_TTL = 600      # 10 minutes for analytics

    # ============================================================================
    # TIER 2: WebSocket Configuration
    # ============================================================================

    SOCKETIO_ASYNC_MODE = 'eventlet'  # or 'threading', 'gevent'
    SOCKETIO_CORS_ALLOWED_ORIGINS = os.environ.get('SOCKETIO_CORS_ORIGINS', '*')
    SOCKETIO_PING_TIMEOUT = 60
    SOCKETIO_PING_INTERVAL = 25

    # ============================================================================
    # TIER 2: Usage Quotas Configuration
    # ============================================================================

    # Default quotas (can be overridden per user)
    QUOTA_QUERIES_PER_DAY = int(os.environ.get('QUOTA_QUERIES_PER_DAY', 100))
    QUOTA_UPLOADS_PER_DAY = int(os.environ.get('QUOTA_UPLOADS_PER_DAY', 10))
    QUOTA_STORAGE_MB = int(os.environ.get('QUOTA_STORAGE_MB', 500))

    # Admin quotas (higher limits)
    QUOTA_ADMIN_QUERIES_PER_DAY = 10000
    QUOTA_ADMIN_UPLOADS_PER_DAY = 1000
    QUOTA_ADMIN_STORAGE_MB = 50000  # 50 GB

    # ============================================================================
    # TIER 3: Document Versioning Configuration
    # ============================================================================

    VERSIONING_ENABLED = os.environ.get('VERSIONING_ENABLED', 'True').lower() == 'true'
    VERSIONING_MAX_VERSIONS = int(os.environ.get('VERSIONING_MAX_VERSIONS', 10))
    VERSIONING_RETENTION_DAYS = int(os.environ.get('VERSIONING_RETENTION_DAYS', 90))


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

    # Use in-memory cache for development (no Redis needed)
    CACHE_TYPE = 'simple'

    # Relaxed rate limits for development
    RATELIMIT_ENABLED = False

    # Verbose logging
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

    # Strict rate limits
    RATELIMIT_ENABLED = True

    # Production logging
    LOG_LEVEL = 'INFO'

    # Require environment variables
    @classmethod
    def init_app(cls, app):
        """Validate production configuration"""
        required_vars = ['GEMINI_API_KEY', 'SUPABASE_URL', 'SUPABASE_KEY', 'SECRET_KEY']
        missing = [var for var in required_vars if not os.environ.get(var)]

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True

    # Disable rate limiting for tests
    RATELIMIT_ENABLED = False

    # Use in-memory cache
    CACHE_TYPE = 'simple'

    # Lower quotas for testing
    QUOTA_QUERIES_PER_DAY = 10
    QUOTA_UPLOADS_PER_DAY = 5


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
