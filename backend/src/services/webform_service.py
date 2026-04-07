"""
Web form handler service for receiving and processing web support form submissions.
"""
import re
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class WebFormService:
    def __init__(self):
        pass

    def parse_form_submission(self, form_data: Dict) -> Dict:
        """
        Parse and validate web form submission.
        Returns standardized message dictionary.
        """
        try:
            # Extract and validate required fields
            name = form_data.get('name', '').strip()
            email = form_data.get('email', '').strip()
            subject = form_data.get('subject', '').strip()
            message = form_data.get('message', '').strip()

            # Basic validation
            if not email:
                raise ValueError("Email is required")
            if not message:
                raise ValueError("Message is required")

            # Email format validation (basic)
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                raise ValueError("Invalid email format")

            # Create standardized message format
            parsed_message = {
                'id': f"webform_{hash(email + message) % 1000000}",  # Simple hash-based ID
                'thread_id': f"webform_thread_{hash(email) % 1000000}",
                'subject': subject if subject else f"Web Form Submission from {name or email}",
                'sender': email,
                'date': self._get_current_timestamp(),
                'body': message,
                'snippet': message[:100] + '...' if len(message) > 100 else message,
                'metadata': {
                    'name': name,
                    'source': 'webform'
                }
            }

            logger.info(f"Parsed web form submission from {email}")
            return parsed_message

        except Exception as e:
            logger.error(f"Error parsing web form submission: {e}")
            raise

    def validate_form_data(self, form_data: Dict) -> Dict:
        """
        Validate form data and return validation results.
        """
        errors = []
        validated_data = {}

        # Validate email
        email = form_data.get('email', '').strip()
        if not email:
            errors.append("Email is required")
        else:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                errors.append("Invalid email format")
            else:
                validated_data['email'] = email

        # Validate message
        message = form_data.get('message', '').strip()
        if not message:
            errors.append("Message is required")
        else:
            validated_data['message'] = message

        # Validate name (optional)
        name = form_data.get('name', '').strip()
        validated_data['name'] = name if name else None

        # Validate subject (optional)
        subject = form_data.get('subject', '').strip()
        validated_data['subject'] = subject if subject else None

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'data': validated_data
        }

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in standard format."""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def create_auto_response(self, parsed_message: Dict) -> Dict:
        """
        Create an auto-response message for web form submissions.
        """
        sender_name = parsed_message.get('metadata', {}).get('name', 'there')
        subject = parsed_message.get('subject', 'your inquiry')

        response_body = f"""Hello {sender_name},

Thank you for contacting us! We have received your inquiry regarding "{subject}" and our team will review it shortly.

We aim to respond to all inquiries within 24 hours. If your matter is urgent, please don't hesitate to reach out via phone.

Best regards,
Customer Support Team"""

        return {
            'to': parsed_message['sender'],
            'subject': f"Re: {subject}",
            'body': response_body
        }