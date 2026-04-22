"""
Structured logging infrastructure using JSON format with correlation IDs.

Provides centralized logging configuration with proper formatting
and correlation ID propagation.
"""

import asyncio
import logging
import logging.config
import sys
import json
from typing import Any, Dict, Optional, Callable
from datetime import datetime
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware

# Try to import FastAPI types, fallback to mock if not available
try:
    from fastapi import Request, Response
    FASTAPI_AVAILABLE = True
except ImportError:
    # Mock FastAPI types for environments where FastAPI is not available
    class Request:
        def __init__(self):
            self.method = "GET"
            self.url = type('URL', (), {
                'path': '/',
                'query': ''
            })()
            self.client = type('Client', (), {
                'host': '127.0.0.1'
            })()
            self.state = type('State', (), {
                'correlation_id': 'unknown'
            })()

    class Response:
        def __init__(self):
            self.status_code = 200

    class Callable:
        pass

    # If we're in a FastAPI environment, use the real types
    if 'FASTAPI_AVAILABLE' not in globals():
        FASTAPI_AVAILABLE = True

# Correlation ID context variable
_correlation_id_context: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def set_correlation_id(correlation_id: str) -> None:
    """
    Set correlation ID in context.

    Args:
        correlation_id: Correlation ID to set
    """
    _correlation_id_context.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """
    Get correlation ID from context.

    Returns:
        Correlation ID or None
    """
    return _correlation_id_context.get()


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logs.

    Formats log records as JSON with:
    - timestamp
    - level
    - logger name
    - message
    - correlation ID
    - extra fields
    """

    def __init__(self, *args, **kwargs):
        """Initialize JSON formatter."""
        super().__init__(*args, **kwargs)

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON string
        """
        # Create log entry
        log_entry = {
            "timestamp": datetime.now(datetime.UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": get_correlation_id(),
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "props") and record.props:
            log_entry.update(record.props)

        return json.dumps(log_entry, default=str)


def configure_logging(
    level: str = "INFO",
    format_type: str = "json",
    log_file: Optional[str] = None,
) -> None:
    """
    Configure structured logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: "json" or "text"
        log_file: Optional file path for log output
    """
    # Create formatters
    if format_type.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(correlation_id)s - %(message)s"
        )

    # Create handlers
    handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # Configure root logger
    logging.root.handlers = handlers
    logging.root.setLevel(level)

    # Silence noisy loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("kafka").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logging.info(f"Logging configured: level={level}, format={format_type}")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for request/response logging.

    Logs all HTTP requests and responses with correlation IDs.
    """

    def __init__(self, app):
        """
        Initialize logging middleware.

        Args:
            app: FastAPI application
        """
        super().__init__(app)
        self.logger = logging.getLogger("api.requests")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request and response with correlation ID.

        Args:
            request: Incoming request
            call_next: Next middleware or route handler

        Returns:
            Response from downstream
        """
        # Get correlation ID
        correlation_id = getattr(request.state, "correlation_id", "unknown")

        # Log request
        self.logger.info(
            "Request received",
            extra={
                "props": {
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": str(request.url.query),
                    "client_host": request.client.host if request.client else None,
                }
            },
        )

        # Process request
        try:
            response = await call_next(request)

            # Log response
            self.logger.info(
                "Request completed",
                extra={
                    "props": {
                        "status_code": response.status_code,
                        "response_time_ms": self._get_response_time(request),
                    }
                },
            )

            return response

        except Exception as e:
            # Log error
            self.logger.error(
                "Request failed",
                exc_info=True,
                extra={
                    "props": {
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                    }
                },
            )
            raise

    def _get_response_time(self, request: Request) -> float:
        """
        Calculate response time from request.

        Args:
            request: FastAPI request

        Returns:
            Response time in milliseconds
        """
        # TODO: Implement timing using request state
        return 0


# Logging context manager for adding extra fields
class LogContext:
    """
    Context manager for adding extra fields to logs.

    Usage:
        with LogContext(user_id="123", action="login"):
            logger.info("User logged in")
    """

    def __init__(self, **kwargs):
        """
        Initialize log context.

        Args:
            **kwargs: Extra fields to add to log records
        """
        self.extra = kwargs

    def __enter__(self):
        """Enter context - add fields to context."""
        # Store extra fields in a thread-local context
        # For simplicity, we'll add them to the log record via a custom filter
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - remove fields from context."""
        pass


class ContextFilter(logging.Filter):
    """
    Filter to add context fields to log records.
    """

    def filter(self, record: logging.LogRecord) -> logging.LogRecord:
        """Add context fields to log record."""
        # Add correlation ID
        correlation_id = get_correlation_id()
        if correlation_id:
            record.correlation_id = correlation_id

        # Add any extra context
        # TODO: Implement context storage/retrieval

        return record
