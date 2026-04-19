"""
Request correlation ID middleware for distributed tracing.

Generates and manages correlation IDs for request tracking
across all services and components.
"""

import uuid
import logging
from typing import Callable, Optional
from fastapi import Request, Response

logger = logging.getLogger(__name__)


CORRELATION_HEADER = "X-Correlation-ID"


from starlette.middleware.base import BaseHTTPMiddleware

class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to manage correlation IDs for request tracing.

    Features:
    - Generate new correlation ID if not present
    - Preserve existing correlation ID
    - Add correlation ID to request state
    - Add correlation ID to response headers
    - Log correlation ID for debugging
    """

    def __init__(self, app):
        """
        Initialize correlation ID middleware.

        Args:
            app: FastAPI application
        """
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """
        Process request and add correlation ID.

        Args:
            request: Incoming request
            call_next: Next middleware or route handler

        Returns:
            Response from downstream
        """
        # Extract or generate correlation ID
        correlation_id = request.headers.get(CORRELATION_HEADER)

        if not correlation_id:
            correlation_id = str(uuid.uuid4())
            logger.debug(f"Generated new correlation ID: {correlation_id}")
        else:
            logger.debug(f"Using existing correlation ID: {correlation_id}")

        # Store in request state
        request.state.correlation_id = correlation_id

        # Add to context for logging
        from src.middleware.logging import set_correlation_id
        set_correlation_id(correlation_id)

        # Add to OpenTelemetry context if available
        try:
            from opentelemetry import trace
            current_span = trace.get_current_span()
            if current_span:
                current_span.set_attribute("correlation.id", correlation_id)
        except (ImportError, AttributeError):
            pass

        logger.info(
            f"Request started: {request.method} {request.url.path}, "
            f"correlation_id={correlation_id}"
        )

        # Process request
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers[CORRELATION_HEADER] = correlation_id

        logger.debug(
            f"Request completed: {request.method} {request.url.path}, "
            f"status={response.status_code}, correlation_id={correlation_id}"
        )

        return response


def get_correlation_id(request: Request) -> str:
    """
    Get correlation ID from request.

    Args:
        request: FastAPI request

    Returns:
        str: Correlation ID
    """
    # Handle case where request.state might be a function or None
    if hasattr(request, 'state') and request.state is not None:
        if hasattr(request.state, "correlation_id"):
            return request.state.correlation_id

    # Fallback to header
    return request.headers.get(CORRELATION_HEADER, "unknown")


def generate_correlation_id() -> str:
    """
    Generate a new correlation ID.

    Returns:
        str: UUID-based correlation ID
    """
    return str(uuid.uuid4())
