"""
Logging Configuration for Agentic RAG System
============================================

Provides structured logging with:
- JSON formatted logs
- Contextual information (user_id, request_id, etc.)
- Log rotation
- Multiple outputs (console, file, Sentry)
"""

import os
import sys
import logging
import structlog
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from datetime import datetime
from pathlib import Path


def setup_logging(app=None, log_level='INFO', log_file=None):
    """
    Setup structured logging for the application

    Args:
        app: Flask application instance (optional)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)

    Returns:
        Configured logger
    """

    # Create logs directory if it doesn't exist
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure standard library logging
    logging.basicConfig(
        level=numeric_level,
        format='%(message)s',
        stream=sys.stdout
    )

    # Processors for structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add JSON renderer for production
    if os.environ.get('FLASK_ENV') == 'production':
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Use pretty console output for development
        processors.append(structlog.dev.ConsoleRenderer())

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Setup file handler with JSON formatting
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(numeric_level)

        # JSON formatter for file logs
        json_formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s',
            timestamp=True
        )
        file_handler.setFormatter(json_formatter)

        # Add to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)

    # Setup Flask app logging if provided
    if app:
        app.logger.setLevel(numeric_level)

        # Add request context processor
        @app.before_request
        def add_request_context():
            """Add request context to logs"""
            from flask import request, g
            import uuid

            # Generate request ID
            g.request_id = str(uuid.uuid4())

            # Bind context to structlog
            structlog.contextvars.clear_contextvars()
            structlog.contextvars.bind_contextvars(
                request_id=g.request_id,
                method=request.method,
                path=request.path,
                remote_addr=request.remote_addr,
                user_agent=request.headers.get('User-Agent', 'Unknown')
            )

        @app.after_request
        def log_request(response):
            """Log request details after processing"""
            from flask import request, g
            logger = structlog.get_logger()

            logger.info(
                "request_completed",
                status_code=response.status_code,
                content_length=response.content_length,
                request_id=getattr(g, 'request_id', 'unknown')
            )
            return response

    return structlog.get_logger()


def get_logger(name=None):
    """
    Get a logger instance

    Args:
        name: Logger name (usually __name__)

    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


# Custom log helpers
def log_query(logger, user_id, question, query_type, duration_ms):
    """Log a RAG query"""
    logger.info(
        "rag_query",
        user_id=user_id,
        question=question[:100],  # Truncate long questions
        query_type=query_type,
        duration_ms=duration_ms
    )


def log_upload(logger, user_id, filename, file_size, success=True, error=None):
    """Log a file upload"""
    logger.info(
        "file_upload",
        user_id=user_id,
        filename=filename,
        file_size=file_size,
        success=success,
        error=error
    )


def log_auth(logger, user_id, action, success=True, error=None):
    """Log authentication events"""
    logger.info(
        "auth_event",
        user_id=user_id,
        action=action,
        success=success,
        error=error
    )


def log_admin_action(logger, admin_id, action, target_id, details=None):
    """Log admin actions"""
    logger.info(
        "admin_action",
        admin_id=admin_id,
        action=action,
        target_id=target_id,
        details=details
    )


def log_error(logger, error, context=None):
    """Log errors with context"""
    logger.error(
        "error_occurred",
        error=str(error),
        error_type=type(error).__name__,
        context=context or {},
        exc_info=True
    )


def log_performance(logger, operation, duration_ms, metadata=None):
    """Log performance metrics"""
    logger.info(
        "performance_metric",
        operation=operation,
        duration_ms=duration_ms,
        metadata=metadata or {}
    )


# Sentry integration (optional)
def setup_sentry(app, dsn=None, environment='production'):
    """
    Setup Sentry error tracking

    Args:
        app: Flask application instance
        dsn: Sentry DSN
        environment: Environment name

    Returns:
        Sentry client instance or None
    """
    if not dsn:
        return None

    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        # Configure Sentry logging
        sentry_logging = LoggingIntegration(
            level=logging.INFO,        # Capture info and above as breadcrumbs
            event_level=logging.ERROR  # Send errors as events
        )

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            integrations=[
                FlaskIntegration(),
                sentry_logging,
            ],
            traces_sample_rate=0.1,  # 10% of transactions
            profiles_sample_rate=0.1,  # 10% of profiling
        )

        app.logger.info(f"Sentry initialized for environment: {environment}")
        return sentry_sdk

    except ImportError:
        app.logger.warning("Sentry SDK not installed. Install with: pip install sentry-sdk[flask]")
        return None
    except Exception as e:
        app.logger.error(f"Failed to initialize Sentry: {e}")
        return None


# Performance monitoring decorator
def monitor_performance(operation_name):
    """
    Decorator to monitor function performance

    Usage:
        @monitor_performance("query_processing")
        def process_query(question):
            # ... process query
            return result
    """
    import functools
    import time

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger()
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                log_performance(
                    logger,
                    operation=operation_name,
                    duration_ms=duration_ms,
                    metadata={'success': True}
                )

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000

                log_performance(
                    logger,
                    operation=operation_name,
                    duration_ms=duration_ms,
                    metadata={'success': False, 'error': str(e)}
                )

                raise

        return wrapper
    return decorator


if __name__ == "__main__":
    # Test logging configuration
    logger = setup_logging(log_level='DEBUG')

    logger.info("test_message", key="value", count=42)
    logger.warning("test_warning", status="warning")
    logger.error("test_error", error_code=500)

    # Test custom log helpers
    log_query(logger, "user123", "What is AI?", "FACTUAL", 250)
    log_upload(logger, "user123", "document.pdf", 1024000, success=True)
    log_auth(logger, "user123", "login", success=True)

    print("\nLogging test completed successfully!")
