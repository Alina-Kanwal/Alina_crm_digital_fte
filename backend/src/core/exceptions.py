"""
Custom exceptions for the Digital FTE agent.
"""
from fastapi import HTTPException
from typing import Optional

class DigitalFTEException(HTTPException):
    """
    Base exception for Digital FTE agent.
    """
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[dict] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class ValidationError(DigitalFTEException):
    """Raised when input validation fails."""
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)

class NotFoundError(DigitalFTEException):
    """Raised when a resource is not found."""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail)

class UnauthorizedError(DigitalFTEException):
    """Raised when authentication fails."""
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(status_code=401, detail=detail)

class ForbiddenError(DigitalFTEException):
    """Raised when access is forbidden."""
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=403, detail=detail)

class RateLimitError(DigitalFTEException):
    """Raised when rate limit is exceeded."""
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(status_code=429, detail=detail)

class ExternalServiceError(DigitalFTEException):
    """Raised when external service calls fail."""
    def __init__(self, detail: str):
        super().__init__(status_code=503, detail=detail)

class ConfigurationError(DigitalFTEException):
    """Raised when configuration is invalid."""
    def __init__(self, detail: str):
        super().__init__(status_code=500, detail=detail)