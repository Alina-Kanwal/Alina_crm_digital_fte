"""
Error handling framework for FastAPI application.

Provides centralized error handling with proper HTTP status codes,
structured error responses, and logging.
"""

import asyncio
import logging
import os
from typing import Any, Callable, Dict, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from pydantic import ValidationError

from src.middleware.correlation import get_correlation_id

# Try to import FastAPI types, fallback to mock if not available
try:
    from fastapi import Request, Response
    from fastapi.responses import JSONResponse
    from fastapi.exceptions import RequestValidationError, HTTPException
    from pydantic import ValidationError
    FASTAPI_AVAILABLE = True
except ImportError:
    logger.warning("FastAPI or dependencies not available, using mock types for error handling")
    FASTAPI_AVAILABLE = False

    # Mock FastAPI types
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

    class JSONResponse:
        def __init__(self, status_code: int, content: dict):
            self.status_code = status_code
            self.content = content

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail

    class RequestValidationError(Exception):
        def __init__(self, errors: list):
            self.errors = errors

    class ValidationError(Exception):
        def __init__(self, errors: list):
            self.errors = errors

    class Callable:
        pass

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware:
    """
    Centralized error handling middleware.

    Catches all exceptions and returns standardized error responses.
    """

    def __init__(self, app):
        """
        Initialize error handling middleware.

        Args:
            app: FastAPI application
        """
        self.app = app

    async def __call__(self, scope, receive, send):
        # Handle ASGI interface
        if isinstance(scope, dict) and callable(receive) and callable(send):
            # Import here to avoid circular imports
            from starlette.requests import Request

            request = Request(scope, receive)

            try:
                # Call the next middleware/app in the chain
                await self.app(scope, receive, send)
                return
            except HTTPException as exc:
                # Create a proper ASGI response for HTTP exceptions
                from starlette.responses import Response
                import json

                # Get correlation ID
                correlation_id = self._get_correlation_id_from_scope(scope)

                # Prepare error response
                error_content = {
                    "error": {
                        "type": "http_error",
                        "code": exc.status_code,
                        "message": exc.detail,
                        "correlation_id": correlation_id,
                    }
                }

                response = Response(
                    content=json.dumps(error_content),
                    status_code=exc.status_code,
                    media_type="application/json"
                )

                await response(scope, receive, send)
                return
            except Exception as exc:
                # Create a proper ASGI response for general exceptions
                from starlette.responses import Response
                import json
                import os

                # Get correlation ID
                correlation_id = self._get_correlation_id_from_scope(scope)

                # Don't expose internal error details in production
                is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
                error_message = (
                    "An internal server error occurred"
                    if is_production
                    else str(exc)
                )

                # Prepare error response
                error_content = {
                    "error": {
                        "type": "internal_error",
                        "code": 500,
                        "message": error_message,
                        "correlation_id": correlation_id,
                    }
                }

                response = Response(
                    content=json.dumps(error_content),
                    status_code=500,
                    media_type="application/json"
                )

                await response(scope, receive, send)
                return
        else:
            # Legacy fallback - this should not happen in normal operation
            raise ValueError("Invalid ASGI interface")

    def _get_correlation_id_from_scope(self, scope):
        """Extract correlation ID from ASGI scope."""
        try:
            # Look for correlation ID in scope state or headers
            headers = dict(scope.get("headers", []))
            # Convert byte keys/values to strings
            headers = {k.decode("latin-1") if isinstance(k, bytes) else k:
                      v.decode("latin-1") if isinstance(v, bytes) else v
                      for k, v in headers.items()}

            # Look for correlation ID in headers
            correlation_id = headers.get("x-correlation-id")
            if correlation_id:
                return correlation_id

            # Alternative header names
            correlation_id = headers.get("correlationid")
            if correlation_id:
                return correlation_id

            return "unknown"
        except Exception:
            return "unknown"

    def _handle_http_exception(
        self,
        request,
        exc,
    ):
        """
        Handle FastAPI HTTP exceptions.

        Args:
            request: FastAPI request
            exc: HTTPException

        Returns:
            JSONResponse with error details
        """
        correlation_id = get_correlation_id(request)
        logger.warning(
            f"HTTP exception: {exc.status_code} - {exc.detail}, "
            f"correlation_id={correlation_id}"
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": "http_error",
                    "code": exc.status_code,
                    "message": exc.detail,
                    "correlation_id": correlation_id,
                }
            },
        )

    def _handle_validation_error(
        self,
        request,
        exc,
    ):
        """
        Handle FastAPI request validation errors.

        Args:
            request: FastAPI request
            exc: RequestValidationError

        Returns:
            JSONResponse with validation errors
        """
        correlation_id = get_correlation_id(request)
        logger.warning(
            f"Validation error: {exc.errors()}, correlation_id={correlation_id}"
        )

        # Format validation errors
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })

        return JSONResponse(
            status_code=422,  # Unprocessable Entity
            content={
                "error": {
                    "type": "validation_error",
                    "code": 422,
                    "message": "Request validation failed",
                    "correlation_id": correlation_id,
                    "details": errors,
                }
            },
        )

    def _handle_pydantic_validation_error(
        self,
        request,
        exc,
    ):
        """
        Handle Pydantic validation errors.

        Args:
            request: FastAPI request
            exc: ValidationError

        Returns:
            JSONResponse with validation errors
        """
        correlation_id = get_correlation_id(request)
        logger.warning(
            f"Pydantic validation error: {exc.errors()}, correlation_id={correlation_id}"
        )

        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })

        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "type": "validation_error",
                    "code": 422,
                    "message": "Data validation failed",
                    "correlation_id": correlation_id,
                    "details": errors,
                }
            },
        )

    def _handle_value_error(
        self,
        request,
        exc,
    ):
        """
        Handle ValueError exceptions.

        Args:
            request: FastAPI request
            exc: ValueError

        Returns:
            JSONResponse with error details
        """
        correlation_id = get_correlation_id(request)
        logger.warning(
            f"Value error: {str(exc)}, correlation_id={correlation_id}"
        )

        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "type": "value_error",
                    "code": 400,
                    "message": str(exc),
                    "correlation_id": correlation_id,
                }
            },
        )

    def _handle_key_error(
        self,
        request,
        exc,
    ):
        """
        Handle KeyError exceptions.

        Args:
            request: FastAPI request
            exc: KeyError

        Returns:
            JSONResponse with error details
        """
        correlation_id = get_correlation_id(request)
        logger.warning(
            f"Key error: {str(exc)}, correlation_id={correlation_id}"
        )

        return JSONResponse(
            status_code=404,  # Not Found
            content={
                "error": {
                    "type": "not_found_error",
                    "code": 404,
                    "message": f"Required key not found: {str(exc)}",
                    "correlation_id": correlation_id,
                }
            },
        )

    def _handle_generic_exception(
        self,
        request,
        exc,
    ):
        """
        Handle generic exceptions.

        Args:
            request: FastAPI request
            exc: Exception

        Returns:
            JSONResponse with error details
        """
        correlation_id = get_correlation_id(request)
        logger.error(
            f"Unhandled exception: {type(exc).__name__}: {str(exc)}, "
            f"correlation_id={correlation_id}",
            exc_info=exc,
        )

        # Don't expose internal error details in production
        is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"

        error_message = (
            "An internal server error occurred"
            if is_production
            else str(exc)
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "internal_error",
                    "code": 500,
                    "message": error_message,
                    "correlation_id": correlation_id,
                }
            },
        )


# Custom exception classes
class NotFoundError(Exception):
    """Exception raised when a resource is not found."""

    def __init__(self, resource_type: str, resource_id: str):
        """Initialize not found error."""
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(f"{resource_type} not found: {resource_id}")


class ConflictError(Exception):
    """Exception raised when a resource conflict occurs."""

    def __init__(self, message: str):
        """Initialize conflict error."""
        super().__init__(message)


class BusinessRuleError(Exception):
    """Exception raised when business rules are violated."""

    def __init__(self, rule_name: str, details: str):
        """Initialize business rule error."""
        self.rule_name = rule_name
        self.details = details
        super().__init__(f"Business rule '{rule_name}' violated: {details}")


class ExternalServiceError(Exception):
    """Exception raised when external service calls fail."""

    def __init__(self, service_name: str, details: str):
        """Initialize external service error."""
        self.service_name = service_name
        self.details = details
        super().__init__(f"External service '{service_name}' error: {details}")


# FastAPI exception handlers for custom exceptions
async def not_found_exception_handler(
    request: Request,
    exc: NotFoundError,
) -> JSONResponse:
    """Handle NotFoundError exceptions."""
    correlation_id = get_correlation_id(request)
    logger.warning(
        f"Not found: {exc.resource_type} - {exc.resource_id}, "
        f"correlation_id={correlation_id}"
    )

    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "type": "not_found",
                "code": 404,
                "message": str(exc),
                "resource_type": exc.resource_type,
                "resource_id": exc.resource_id,
                "correlation_id": correlation_id,
            }
        },
    )


async def conflict_exception_handler(
    request: Request,
    exc: ConflictError,
) -> JSONResponse:
    """Handle ConflictError exceptions."""
    correlation_id = get_correlation_id(request)
    logger.warning(
        f"Conflict: {str(exc)}, correlation_id={correlation_id}"
    )

    return JSONResponse(
        status_code=409,
        content={
            "error": {
                "type": "conflict",
                "code": 409,
                "message": str(exc),
                "correlation_id": correlation_id,
            }
        },
    )


async def business_rule_exception_handler(
    request: Request,
    exc: BusinessRuleError,
) -> JSONResponse:
    """Handle BusinessRuleError exceptions."""
    correlation_id = get_correlation_id(request)
    logger.warning(
        f"Business rule violation: {exc.rule_name} - {exc.details}, "
        f"correlation_id={correlation_id}"
    )

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "type": "business_rule_violation",
                "code": 422,
                "message": exc.details,
                "rule": exc.rule_name,
                "correlation_id": correlation_id,
            }
        },
    )


async def external_service_exception_handler(
    request: Request,
    exc: ExternalServiceError,
) -> JSONResponse:
    """Handle ExternalServiceError exceptions."""
    correlation_id = get_correlation_id(request)
    logger.error(
        f"External service error: {exc.service_name} - {exc.details}, "
        f"correlation_id={correlation_id}"
    )

    return JSONResponse(
        status_code=503,  # Service Unavailable
        content={
            "error": {
                "type": "external_service_error",
                "code": 503,
                "message": f"External service '{exc.service_name}' is unavailable",
                "service": exc.service_name,
                "details": exc.details,
                "correlation_id": correlation_id,
            }
        },
    )
