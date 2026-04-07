"""
Web form handler module for Digital FTE AI Customer Success Agent.
Handles receiving and processing customer inquiries from web support forms.
"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class WebFormService:
    """Service for handling web form submissions."""

    def __init__(self):
        """Initialize web form service."""
        logger.info("Web form service initialized")

    async def parse_form_submission(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse incoming web form submission.

        Args:
            form_data: Form data from web form submission

        Returns:
            Parsed form submission dictionary
        """
        try:
            # Extract form fields
            name = form_data.get('name', '').strip()
            email = form_data.get('email', '').strip()
            subject = form_data.get('subject', '').strip()
            message = form_data.get('message', '').strip()
            timestamp = form_data.get('timestamp', datetime.utcnow().isoformat())

            # Validate required fields
            if not email:
                raise ValueError("Email is required")

            if not message:
                raise ValueError("Message is required")

            parsed_submission = {
                'name': name,
                'email': email,
                'subject': subject or 'Web Form Submission',
                'message': message,
                'timestamp': timestamp,
                'channel': 'web_form',
                'customer_info': {
                    'name': name,
                    'email': email
                }
            }

            logger.info(f"Parsed web form submission from {email}: {subject[:50]}...")
            return parsed_submission

        except Exception as e:
            logger.error(f"Error parsing web form submission: {e}")
            return {
                'error': str(e),
                'raw_data': form_data
            }

    async def validate_form_data(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate web form submission data.

        Args:
            form_data: Form data to validate

        Returns:
            Validation result dictionary
        """
        errors = []

        # Check required fields
        if not form_data.get('email'):
            errors.append("Email is required")

        if not form_data.get('message'):
            errors.append("Message is required")

        # Validate email format (basic validation)
        email = form_data.get('email', '')
        if email and '@' not in email:
            errors.append("Invalid email format")

        # Validate message length
        message = form_data.get('message', '')
        if len(message) > 5000:  # Reasonable limit
            errors.append("Message is too long (maximum 5000 characters)")

        # Validate name length
        name = form_data.get('name', '')
        if len(name) > 100:
            errors.append("Name is too long (maximum 100 characters)")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'validated_data': form_data if len(errors) == 0 else None
        }

    async def sanitize_input(self, input_text: str) -> str:
        """
        Sanitize user input to prevent injection attacks.

        Args:
            input_text: Raw user input

        Returns:
            Sanitized input text
        """
        if not input_text:
            return ""

        # Remove potential harmful characters
        # In a real implementation, you might use a library like bleach
        sanitized = input_text.strip()

        # Limit length to prevent DoS
        if len(sanitized) > 10000:
            sanitized = sanitized[:10000] + "... [truncated]"

        return sanitized


# Factory function for dependency injection
def create_webform_service() -> WebFormService:
    """Factory function to create WebFormService instance."""
    return WebFormService()