"""
WebSocket Support for Real-Time Updates
========================================

Provides real-time communication for:
- Query progress updates
- Document upload status
- System notifications
- Live analytics
"""

from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request, session
import structlog

logger = structlog.get_logger(__name__)

# Global SocketIO instance
socketio = None


def init_socketio(app):
    """
    Initialize SocketIO with the Flask app

    Args:
        app: Flask application instance

    Returns:
        SocketIO instance
    """
    global socketio

    socketio = SocketIO(
        app,
        cors_allowed_origins="*",  # Configure based on your needs
        async_mode='eventlet',
        logger=False,
        engineio_logger=False,
        ping_timeout=60,
        ping_interval=25
    )

    # Register event handlers
    register_events(socketio)

    logger.info("WebSocket initialized")
    return socketio


def register_events(socketio_instance):
    """Register WebSocket event handlers"""

    @socketio_instance.on('connect')
    def handle_connect():
        """Handle client connection"""
        user_id = session.get('user_id', 'anonymous')
        client_id = request.sid

        logger.info("websocket_connected", user_id=user_id, client_id=client_id)

        # Join user-specific room
        if user_id != 'anonymous':
            join_room(f'user_{user_id}')

        emit('connected', {
            'status': 'connected',
            'client_id': client_id,
            'message': 'Successfully connected to WebSocket'
        })

    @socketio_instance.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        user_id = session.get('user_id', 'anonymous')
        client_id = request.sid

        logger.info("websocket_disconnected", user_id=user_id, client_id=client_id)

        # Leave user-specific room
        if user_id != 'anonymous':
            leave_room(f'user_{user_id}')

    @socketio_instance.on('join_admin_room')
    def handle_join_admin():
        """Allow admins to join admin room for system-wide notifications"""
        user_role = session.get('user_role', 'user')

        if user_role == 'admin':
            join_room('admin')
            emit('room_joined', {'room': 'admin'})
            logger.info("admin_joined_room", user_id=session.get('user_id'))
        else:
            emit('error', {'message': 'Admin access required'})

    @socketio_instance.on('ping')
    def handle_ping():
        """Handle ping from client"""
        emit('pong', {'timestamp': datetime.now().isoformat()})


def get_socketio():
    """Get global SocketIO instance"""
    return socketio


# Helper functions for emitting events

def emit_query_progress(user_id, query_id, progress_data):
    """
    Emit query processing progress to user

    Args:
        user_id: User ID
        query_id: Query identifier
        progress_data: Progress information dict
    """
    if not socketio:
        return

    try:
        socketio.emit(
            'query_progress',
            {
                'query_id': query_id,
                **progress_data
            },
            room=f'user_{user_id}'
        )

        logger.info(
            "query_progress_emitted",
            user_id=user_id,
            query_id=query_id,
            stage=progress_data.get('stage')
        )

    except Exception as e:
        logger.error("error_emitting_query_progress", error=str(e))


def emit_upload_progress(user_id, upload_id, progress_data):
    """
    Emit file upload progress to user

    Args:
        user_id: User ID
        upload_id: Upload identifier
        progress_data: Progress information dict
    """
    if not socketio:
        return

    try:
        socketio.emit(
            'upload_progress',
            {
                'upload_id': upload_id,
                **progress_data
            },
            room=f'user_{user_id}'
        )

        logger.info(
            "upload_progress_emitted",
            user_id=user_id,
            upload_id=upload_id,
            percent=progress_data.get('percent')
        )

    except Exception as e:
        logger.error("error_emitting_upload_progress", error=str(e))


def emit_notification(user_id, notification_data):
    """
    Emit notification to user

    Args:
        user_id: User ID
        notification_data: Notification dict (type, title, message, etc.)
    """
    if not socketio:
        return

    try:
        socketio.emit(
            'notification',
            notification_data,
            room=f'user_{user_id}'
        )

        logger.info(
            "notification_emitted",
            user_id=user_id,
            notification_type=notification_data.get('type')
        )

    except Exception as e:
        logger.error("error_emitting_notification", error=str(e))


def emit_admin_alert(alert_data):
    """
    Emit alert to all admins

    Args:
        alert_data: Alert information dict
    """
    if not socketio:
        return

    try:
        socketio.emit(
            'admin_alert',
            alert_data,
            room='admin'
        )

        logger.info(
            "admin_alert_emitted",
            alert_type=alert_data.get('type')
        )

    except Exception as e:
        logger.error("error_emitting_admin_alert", error=str(e))


def emit_system_status(status_data):
    """
    Emit system status update to all connected clients

    Args:
        status_data: System status dict
    """
    if not socketio:
        return

    try:
        socketio.emit(
            'system_status',
            status_data,
            broadcast=True
        )

        logger.info("system_status_emitted", status=status_data.get('status'))

    except Exception as e:
        logger.error("error_emitting_system_status", error=str(e))


def emit_analytics_update(user_id, analytics_data):
    """
    Emit live analytics update to user

    Args:
        user_id: User ID
        analytics_data: Analytics information dict
    """
    if not socketio:
        return

    try:
        socketio.emit(
            'analytics_update',
            analytics_data,
            room=f'user_{user_id}'
        )

        logger.info("analytics_update_emitted", user_id=user_id)

    except Exception as e:
        logger.error("error_emitting_analytics_update", error=str(e))


# Context managers for progress tracking

class QueryProgressTracker:
    """Context manager for tracking query progress with WebSocket updates"""

    def __init__(self, user_id, query_id):
        self.user_id = user_id
        self.query_id = query_id

    def __enter__(self):
        self.update("started", "Query processing started", 0)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.update("completed", "Query completed successfully", 100)
        else:
            self.update("error", f"Query failed: {str(exc_val)}", 0, error=True)

    def update(self, stage, message, percent, error=False):
        """Update progress"""
        emit_query_progress(
            self.user_id,
            self.query_id,
            {
                'stage': stage,
                'message': message,
                'percent': percent,
                'error': error
            }
        )


class UploadProgressTracker:
    """Context manager for tracking upload progress with WebSocket updates"""

    def __init__(self, user_id, upload_id, total_files):
        self.user_id = user_id
        self.upload_id = upload_id
        self.total_files = total_files
        self.current_file = 0

    def __enter__(self):
        self.update("started", "Upload started", 0)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.update("completed", "Upload completed successfully", 100)
        else:
            self.update("error", f"Upload failed: {str(exc_val)}", 0, error=True)

    def update_file(self, filename, percent):
        """Update progress for current file"""
        overall_percent = ((self.current_file + (percent / 100)) / self.total_files) * 100

        self.update(
            "uploading",
            f"Uploading {filename}",
            round(overall_percent, 2),
            current_file=self.current_file + 1,
            total_files=self.total_files
        )

    def next_file(self):
        """Move to next file"""
        self.current_file += 1

    def update(self, stage, message, percent, error=False, **kwargs):
        """Update progress"""
        emit_upload_progress(
            self.user_id,
            self.upload_id,
            {
                'stage': stage,
                'message': message,
                'percent': percent,
                'error': error,
                **kwargs
            }
        )


# Import datetime at the top of the file
from datetime import datetime


if __name__ == "__main__":
    print("WebSocket support module - Use with Flask-SocketIO")
