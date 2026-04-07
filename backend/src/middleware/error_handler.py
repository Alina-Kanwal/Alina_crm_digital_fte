"""
Error handling middleware for the Digital FTE agent.
"""
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import traceback
from src.core.exceptions import DigitalFTEException

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to catch and handle exceptions globally.
    """
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except DigitalFTEException as exc:
            logger.error(f"Digital FTE Exception: {exc.detail}")
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": exc.detail},
                headers=exc.headers
            )
        except Exception as exc:
            logger.error(f"Unhandled exception: {str(exc)}")
            logger.error(traceback.format_exc())
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"}
            )