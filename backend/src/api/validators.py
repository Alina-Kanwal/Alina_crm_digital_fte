"""
Validation and error handling for incoming messages in Digital FTE AI Customer Success Agent.
Provides input validation, sanitization, and error handling for API endpoints.
"""

import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel, validator, ValidationError
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


# Pydantic models for request validation
class WebFormSubmission(BaseModel):
    """Model for validating web form submissions."""
    name: Optional[str] = None
    email: str
    subject: Optional[str] = None
    message: str

    @validator('email')
    def validate_email(cls, v):
        """Validate email format."""
        if not v:
            raise ValueError('Email is required')
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower().strip()

    @validator('name')
    def validate_name(cls, v):
        """Validate name field."""
        if v is not None:
            v = v.strip()
            if len(v) > 100:
                raise ValueError('Name is too long (maximum 100 characters)')
            # Allow only letters, spaces, hyphens, and apostrophes
            if v and not re.match(r"^[a-zA-Z\s\-']+$", v):
                raise ValueError('Name contains invalid characters')
        return v

    @validator('message')
    def validate_message(cls, v):
        """Validate message field."""
        if not v or not v.strip():
            raise ValueError('Message is required')
        v = v.strip()
        if len(v) > 5000:
            raise ValueError('Message is too long (maximum 5000 characters)')
        return v

    @validator('subject')
    def validate_subject(cls, v):
        """Validate subject field."""
        if v is not None:
            v = v.strip()
            if len(v) > 200:
                raise ValueError('Subject is too long (maximum 200 characters)')
        return v


class EmailInquiry(BaseModel):
    """Model for validating email inquiries."""
    id: str
    sender: str
    subject: Optional[str] = None
    body: str
    timestamp: Optional[str] = None

    @validator('sender')
    def validate_sender(cls, v):
        """Validate sender email."""
        if not v:
            raise ValueError('Sender email is required')
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid sender email format')
        return v.lower().strip()

    @validator('body')
    def validate_body(cls, v):
        """Validate body content."""
        if not v or not v.strip():
            raise ValueError('Email body is required')
        v = v.strip()
        if len(v) > 10000:  # Reasonable limit for email
            raise ValueError('Email body is too long (maximum 10000 characters)')
        return v

    @validator('subject')
    def validate_subject(cls, v):
        """Validate subject field."""
        if v is not None:
            v = v.strip()
            if len(v) > 200:
                raise ValueError('Subject is too long (maximum 200 characters)')
        return v


class WhatsAppInquiry(BaseModel):
    """Model for validating WhatsApp inquiries."""
    id: str
    sender: str
    body: str
    timestamp: Optional[str] = None
    num_media: Optional[str] = "0"

    @validator('sender')
    def validate_sender(cls, v):
        """Validate sender phone number."""
        if not v:
            raise ValueError('Sender phone number is required')
        # Remove whatsapp: prefix if present
        clean_number = v.replace('whatsapp:', '') if v.startswith('whatsapp:') else v
        # Validate phone number format
        phone_pattern = r'^[\+]?[1-9][\d\s\-\(\)]{7,}$'
        if not re.match(phone_pattern, clean_number):
            raise ValueError('Invalid phone number format')
        # Return cleaned number
        return re.sub(r'[\s\-\(\)]', '', clean_number)

    @validator('body')
    def validate_body(cls, v):
        """Validate body content."""
        if not v:
            raise ValueError('Message body is required')
        v = v.strip()
        if len(v) > 1000:  # WhatsApp messages should be short
            raise ValueError('Message is too long for WhatsApp (maximum 1000 characters)')
        return v

    @validator('num_media')
    def validate_num_media(cls, v):
        """Validate number of media attachments."""
        try:
            num = int(v) if v else 0
            if num < 0:
                raise ValueError('Number of media attachments cannot be negative')
            if num > 10:  # Reasonable limit
                raise ValueError('Too many media attachments (maximum 10)')
            return str(num)
        except ValueError:
            raise ValueError('Number of media attachments must be a valid integer')


# Validation functions
class MessageValidator:
    """Utility class for validating and sanitizing messages."""

    @staticmethod
    def validate_webform_data(form_data: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]], List[str]]:
        """
        Validate web form submission data.

        Args:
            form_data: Raw form data from request

        Returns:
            Tuple of (is_valid, validated_data, error_messages)
        """
        try:
            validated = WebFormSubmission(**form_data)
            return True, validated.dict(), []
        except ValidationError as e:
            errors = []
            for error in e.errors():
                field = " -> ".join(str(loc) for loc in error['loc'])
                message = error['msg']
                errors.append(f"{field}: {message}")
            return False, None, errors
        except Exception as e:
            return False, None, [f"Validation error: {str(e)}"]

    @staticmethod
    def validate_email_data(email_data: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]], List[str]]:
        """
        Validate email inquiry data.

        Args:
            email_data: Raw email data from request/webhook

        Returns:
            Tuple of (is_valid, validated_data, error_messages)
        """
        try:
            validated = EmailInquiry(**email_data)
            return True, validated.dict(), []
        except ValidationError as e:
            errors = []
            for error in e.errors():
                field = " -> ".join(str(loc) for loc in error['loc'])
                message = error['msg']
                errors.append(f"{field}: {message}")
            return False, None, errors
        except Exception as e:
            return False, None, [f"Validation error: {str(e)}"]

    @staticmethod
    def validate_whatsapp_data(whatsapp_data: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]], List[str]]:
        """
        Validate WhatsApp inquiry data.

        Args:
            whatsapp_data: Raw WhatsApp data from request/webhook

        Returns:
            Tuple of (is_valid, validated_data, error_messages)
        """
        try:
            validated = WhatsAppInquiry(**whatsapp_data)
            return True, validated.dict(), []
        except ValidationError as e:
            errors = []
            for error in e.errors():
                field = " -> ".join(str(loc) for loc in error['loc'])
                message = error['msg']
                errors.append(f"{field}: {message}")
            return False, None, errors
        except Exception as e:
            return False, None, [f"Validation error: {str(e)}"]

    @staticmethod
    def sanitize_input(text: str, max_length: int = 10000) -> str:
        """
        Sanitize input text to prevent injection attacks.

        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            return ""

        # Remove null bytes and other dangerous characters
        sanitized = text.replace('\x00', '').replace('\r', '')

        # Limit length to prevent DoS attacks
        if len(sanitized) > max_length:
            logger.warning(f"Input truncated from {len(sanitized)} to {max_length} characters")
            sanitized = sanitized[:max_length]

        # Remove or escape potentially dangerous patterns
        # Basic XSS prevention
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'on\w+\s*=', '', sanitized, flags=re.IGNORECASE)  # onload, onclick, etc.

        # SQL injection basic protection (parameterized queries are better defense)
        sanitized = re.sub(r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION)\b)', '', sanitized, flags=re.IGNORECASE)

        return sanitized.strip()

    @staticmethod
    def validate_message_length(text: str, channel: str, max_lengths: Dict[str, int] = None) -> Tuple[bool, Optional[str]]:
        """
        Validate message length for specific channel.

        Args:
            text: Message text to validate
            channel: Communication channel
            max_lengths: Optional dictionary of max lengths per channel

        Returns:
            Tuple of (is_valid, error_message)
        """
        if max_lengths is None:
            max_lengths = {
                'email': 10000,
                'whatsapp': 1000,
                'web_form': 5000,
                'gmail': 10000
            }

        max_length = max_lengths.get(channel.lower(), 5000)
        if not text:
            return True, None

        if len(text) > max_length:
            error_msg = f"Message too long for {channel} channel (maximum {max_length} characters)"
            return False, error_msg

        return True, None


# Error handling utilities
class ErrorHandler:
    """Utility class for handling and formatting errors."""

    @staticmethod
    async def handle_validation_error(request: Request, exc: ValidationError) -> JSONResponse:
        """
        Handle Pydantic validation errors.

        Args:
            request: FastAPI request object
            exc: ValidationError exception

        Returns:
            JSONResponse with validation error details
        """
        errors = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error['loc'])
            message = error['msg']
            input_value = error.get('input')
            errors.append({
                "field": field,
                "message": message,
                "input": str(input_value) if input_value is not None else None
            })

        logger.warning(f"Validation error: {errors}")
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation failed",
                "details": errors,
                "type": "validation_error",
                "path": str(request.url)
            }
        )

    @staticmethod
    def handle_http_exception(exc: HTTPException) -> Dict[str, Any]:
        """
        Handle HTTP exceptions.

        Args:
            exc: HTTPException exception

        Returns:
            Dictionary with error details for logging
        """
        return {
            "status_code": exc.status_code,
            "detail": exc.detail,
            "headers": dict(exc.headers) if exc.headers else {}
        }

    @staticmethod
    def create_error_response(status_code: int, message: str,
                            error_type: str = "internal_error",
                            details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a standardized error response.

        Args:
            status_code: HTTP status code
            message: Error message
            error_type: Type of error
            details: Optional additional details

        Returns:
            Dictionary with error response data
        """
        response = {
            "error": message,
            "type": error_type,
            "status_code": status_code
        }

        if details:
            response["details"] = details

        return response

    @staticmethod
    def log_and_raise_http_exception(status_code: int, detail: str,
                                   headers: Optional[Dict[str, str]] = None) -> None:
        """
        Log an error and raise an HTTP exception.

        Args:
            status_code: HTTP status code
            detail: Error detail message
            headers: Optional HTTP headers
        """
        logger.error(f"HTTP {status_code}: {detail}")
        raise HTTPException(status_code=status_code, detail=detail, headers=headers)


# Request middleware for validation
async def validate_request_size(request: Request, call_next):
    """
    Middleware to validate request size and prevent DoS attacks.

    Args:
        request: FastAPI request object
        call_next: Next middleware/function in chain

    Returns:
        Response from next middleware
    """
    # Check content length header
    content_length = request.headers.get('content-length')
    if content_length:
        try:
            length = int(content_length)
            # Limit request size to 10MB to prevent DoS
            if length > 10 * 1024 * 1024:  # 10MB
                logger.warning(f"Request too large: {length} bytes from {request.client.host}")
                raise HTTPException(
                    status_code=413,
                    detail="Request too large. Maximum size is 10MB."
                )
        except ValueError:
            pass  # If content-length is not a valid integer, let the server handle it

    # Process the request
    response = await call_next(request)
    return response


# Sanitization middleware
async def sanitize_request_middleware(request: Request, call_next):
    """
    Middleware to sanitize request data.

    Args:
        request: FastAPI request object
        call_next: Next middleware/function in chain

    Returns:
        Response from next middleware
    """
    # Note: Actual sanitization would happen at the endpoint level
    # This is a placeholder for demonstrating the concept
    response = await call_next(request)
    return response


# Export validation functions for easy importing
__all__ = [
    "WebFormSubmission",
    "EmailInquiry",
    "WhatsAppInquiry",
    "MessageValidator",
    "ErrorHandler",
    "validate_request_size",
    "sanitize_request_middleware"
]