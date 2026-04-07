"""
Comprehensive input validation using Pydantic.

Per Constitution Security requirements:
- Prevent SQL injection attacks
- Validate all incoming data
- Sanitize user input
- Implement strict type checking
- Custom validators for business logic
"""
import logging
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import re
from html import escape

from pydantic import BaseModel, Field, validator, EmailStr, HttpUrl, constr
from pydantic import ValidationError


logger = logging.getLogger(__name__)


class ChannelType(str, Enum):
    """Enumeration of supported channels."""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"


class InquiryStatus(str, Enum):
    """Enumeration of inquiry statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    """Enumeration of ticket priorities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class SentimentType(str, Enum):
    """Enumeration of sentiment types."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


# ============================================================================
# Base Validators
# ============================================================================

def sanitize_string(value: str) -> str:
    """
    Sanitize string input to prevent XSS attacks.

    Args:
        value: Input string

    Returns:
        Sanitized string
    """
    if not value:
        return value

    # HTML escape
    sanitized = escape(value)

    # Remove potentially dangerous patterns
    dangerous_patterns = [
        r'<script.*?>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',  # Event handlers like onclick=
        r'<iframe.*?>.*?</iframe>',
        r'<object.*?>.*?</object>',
        r'<embed.*?>.*?</embed>'
    ]

    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)

    return sanitized


def validate_sql_safe(value: str) -> str:
    """
    Validate string is safe from SQL injection attempts.

    Args:
        value: Input string

    Returns:
        Validated string

    Raises:
        ValueError: If SQL injection patterns detected
    """
    if not value:
        return value

    sql_injection_patterns = [
        r"(\s|^)(union|select|insert|update|delete|drop|alter|create|exec)\s",
        r"(--|#|/\*|\*/|;)",
        r"(\s|^)(or|and)\s+\d+\s*=\s*\d+",
        r"(\s|^)(or|and)\s+['\"]\w+['\"]\s*=\s*['\"]\w+['\"]",
        r"'.*'.*'.*'",  # Multiple single quotes
        r'\.\./',  # Path traversal
        r'\\',  # Backslash (potential escape)
    ]

    for pattern in sql_injection_patterns:
        if re.search(pattern, value, flags=re.IGNORECASE):
            raise ValueError("Input contains potentially malicious patterns")

    return value


def validate_email_domain(email: str) -> str:
    """
    Validate email domain is from allowed list (optional).

    Args:
        email: Email address

    Returns:
        Validated email

    Raises:
        ValueError: If domain not allowed
    """
    # Optional: Implement domain allowlist
    allowed_domains = []  # Add allowed domains if needed

    if allowed_domains:
        domain = email.split('@')[-1].lower()
        if domain not in allowed_domains:
            raise ValueError(f"Email domain '{domain}' is not allowed")

    return email


def validate_phone_number(phone: str) -> str:
    """
    Validate phone number format.

    Args:
        phone: Phone number

    Returns:
        Validated phone number

    Raises:
        ValueError: If phone number format invalid
    """
    # Remove all non-numeric characters
    cleaned = re.sub(r'[^\d]', '', phone)

    # Validate length (should be 10-15 digits)
    if not (10 <= len(cleaned) <= 15):
        raise ValueError("Phone number must be 10-15 digits")

    return cleaned


def validate_url_safe(url: str) -> str:
    """
    Validate URL is safe and doesn't contain malicious redirects.

    Args:
        url: URL string

    Returns:
        Validated URL

    Raises:
        ValueError: If URL is malicious
    """
    malicious_patterns = [
        r'javascript:',
        r'data:',
        r'vbscript:',
        r'<.*?>',
        r'on\w+\s*=',
    ]

    url_lower = url.lower()
    for pattern in malicious_patterns:
        if re.search(pattern, url_lower):
            raise ValueError("URL contains potentially malicious patterns")

    return url


# ============================================================================
# Request Models
# ============================================================================

class BaseValidator(BaseModel):
    """Base validator with common fields."""

    @validator('*', pre=True)
    def sanitize_strings(cls, v):
        """Sanitize all string fields."""
        if isinstance(v, str):
            return sanitize_string(v)
        return v


class CreateInquiryRequest(BaseValidator):
    """Request model for creating an inquiry."""

    customer_email: EmailStr
    customer_name: constr(min_length=2, max_length=100)
    customer_phone: Optional[constr(min_length=10, max_length=15)] = None
    channel: ChannelType
    message: constr(min_length=10, max_length=10000)
    subject: Optional[constr(min_length=5, max_length=200)] = None
    priority: Optional[TicketPriority] = TicketPriority.MEDIUM

    @validator('customer_email')
    def validate_email(cls, v):
        """Validate email domain."""
        return validate_email_domain(v)

    @validator('customer_name')
    def validate_name(cls, v):
        """Validate name format."""
        if not re.match(r'^[a-zA-Z\s\-\.]+$', v):
            raise ValueError("Name contains invalid characters")
        return v

    @validator('customer_phone')
    def validate_phone(cls, v):
        """Validate phone number."""
        if v:
            return validate_phone_number(v)
        return v

    @validator('message')
    def validate_message(cls, v):
        """Validate message is SQL-safe."""
        return validate_sql_safe(v)


class UpdateInquiryRequest(BaseValidator):
    """Request model for updating an inquiry."""

    status: Optional[InquiryStatus] = None
    priority: Optional[TicketPriority] = None
    resolution_notes: Optional[constr(max_length=5000)] = None
    assigned_to: Optional[constr(max_length=100)] = None


class SendMessageRequest(BaseValidator):
    """Request model for sending a message."""

    inquiry_id: int
    message: constr(min_length=10, max_length=10000)
    is_internal: bool = False
    channel: Optional[ChannelType] = None

    @validator('message')
    def validate_message(cls, v):
        """Validate message is SQL-safe."""
        return validate_sql_safe(v)


class EscalateInquiryRequest(BaseValidator):
    """Request model for escalating an inquiry."""

    inquiry_id: int
    reason: constr(min_length=10, max_length=1000)
    severity: constr(min_length=5, max_length=50) = "high"
    escalate_to: constr(max_length=100) = "human_agent"

    @validator('reason')
    def validate_reason(cls, v):
        """Validate reason is SQL-safe."""
        return validate_sql_safe(v)


class ManualEscalationRequest(BaseValidator):
    """Request model for manual escalation."""

    ticket_id: int
    agent_id: constr(max_length=100)
    reason: constr(min_length=10, max_length=1000)


class ReportRequest(BaseValidator):
    """Request model for generating reports."""

    report_type: constr(regex=r'^(daily|weekly|monthly|executive_summary)$')
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_sentiment: bool = True
    include_escalations: bool = True
    format: constr(regex=r'^(json|csv|pdf)$') = "json"


class SearchRequest(BaseValidator):
    """Request model for searching inquiries."""

    query: constr(min_length=3, max_length=500)
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    channel: Optional[ChannelType] = None
    status: Optional[InquiryStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


# ============================================================================
# Response Models
# ============================================================================

class InquiryResponse(BaseModel):
    """Response model for inquiry data."""

    id: int
    customer_email: str
    customer_name: str
    customer_phone: Optional[str] = None
    channel: ChannelType
    message: str
    subject: Optional[str] = None
    status: InquiryStatus
    priority: TicketPriority
    created_at: datetime
    updated_at: Optional[datetime] = None
    escalation_count: int = 0
    sentiment: Optional[SentimentType] = None


class MessageResponse(BaseModel):
    """Response model for message data."""

    id: int
    inquiry_id: int
    message: str
    sender: str
    channel: Optional[ChannelType] = None
    is_internal: bool = False
    created_at: datetime


class ErrorResponse(BaseModel):
    """Response model for errors."""

    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class RateLimitResponse(BaseModel):
    """Response model for rate limit exceeded."""

    error: str
    limit: int
    period: int
    reset: int
    remaining: int
    message: str


# ============================================================================
# Validation Utilities
# ============================================================================

class ValidationError(Exception):
    """Custom validation error."""

    def __init__(self, message: str, field: str = None):
        """
        Initialize validation error.

        Args:
            message: Error message
            field: Field that failed validation
        """
        self.message = message
        self.field = field
        super().__init__(message)


def validate_request(
    request_model: type[BaseModel],
    data: Dict[str, Any]
) -> BaseModel:
    """
    Validate request data against a Pydantic model.

    Args:
        request_model: Pydantic model class
        data: Request data

    Returns:
        Validated Pydantic model instance

    Raises:
        ValidationError: If validation fails
    """
    try:
        return request_model(**data)

    except ValidationError as e:
        # Convert Pydantic errors to our custom format
        errors = {}
        for error in e.errors():
            field = '.'.join(str(loc) for loc in error['loc'])
            errors[field] = error['msg']
            logger.warning(f"Validation error for field {field}: {error['msg']}")

        raise ValidationError(
            message="Request validation failed",
            field=str(errors)
        )


def sanitize_input(
    data: Union[str, Dict, List]
) -> Union[str, Dict, List]:
    """
    Sanitize input data recursively.

    Args:
        data: Input data (string, dict, or list)

    Returns:
        Sanitized data
    """
    if isinstance(data, str):
        return sanitize_string(data)

    elif isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}

    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]

    else:
        return data
