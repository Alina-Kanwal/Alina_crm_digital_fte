"""
Twilio WhatsApp API integration module for Digital FTE AI Customer Success Agent.
Handles receiving, processing, and sending WhatsApp messages via Twilio Sandbox.
"""

import logging
from typing import Dict, Any, Optional
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service for handling Twilio WhatsApp API operations."""

    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        """
        Initialize WhatsApp service with Twilio credentials.

        Args:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            from_number: Twilio WhatsApp number (format: 'whatsapp:+14155238886')
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.client = Client(account_sid, auth_token)
        logger.info("Twilio WhatsApp service initialized")

    async def parse_incoming_message(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse incoming WhatsApp message from Twilio webhook.

        Args:
            form_data: Form data from Twilio webhook request

        Returns:
            Parsed message dictionary
        """
        try:
            # Extract message details from Twilio webhook format
            message_sid = form_data.get('MessageSid', '')
            from_number = form_data.get('From', '')  # Format: whatsapp:+1234567890
            to_number = form_data.get('To', '')      # Format: whatsapp:+14155238886
            body = form_data.get('Body', '')
            num_media = form_data.get('NumMedia', '0')

            # Remove 'whatsapp:' prefix from phone numbers
            customer_number = from_number.replace('whatsapp:', '') if from_number.startswith('whatsapp:') else from_number

            parsed_message = {
                'message_sid': message_sid,
                'from_number': customer_number,
                'to_number': to_number.replace('whatsapp:', '') if to_number.startswith('whatsapp:') else to_number,
                'body': body.strip(),
                'num_media': int(num_media),
                'timestamp': form_data.get('Timestamp', ''),
                'message_type': 'text' if int(num_media) == 0 else 'media'
            }

            logger.info(f"Parsed incoming WhatsApp message from {customer_number}: {body[:50]}...")
            return parsed_message

        except Exception as e:
            logger.error(f"Error parsing incoming WhatsApp message: {e}")
            return {
                'error': str(e),
                'raw_data': form_data
            }

    async def send_message(self, to_number: str, message_body: str) -> Dict[str, Any]:
        """
        Send a WhatsApp message via Twilio.

        Args:
            to_number: Recipient phone number (without 'whatsapp:' prefix)
            message_body: Message content to send

        Returns:
            Dictionary with message SID and status
        """
        try:
            # Format recipient number for WhatsApp
            to_whatsapp = f'whatsapp:{to_number}'

            message = self.client.messages.create(
                body=message_body,
                from_=self.from_number,
                to=to_whatsapp
            )

            logger.info(f"WhatsApp message sent to {to_number}. SID: {message.sid}")
            return {
                'message_sid': message.sid,
                'status': message.status,
                'to': to_number,
                'error': None
            }

        except Exception as e:
            logger.error(f"Failed to send WhatsApp message to {to_number}: {e}")
            return {
                'message_sid': None,
                'status': 'failed',
                'to': to_number,
                'error': str(e)
            }

    async def get_message_status(self, message_sid: str) -> Dict[str, Any]:
        """
        Get the status of a sent WhatsApp message.

        Args:
            message_sid: Twilio message SID

        Returns:
            Dictionary with message status details
        """
        try:
            message = self.client.messages(message_sid).fetch()

            return {
                'message_sid': message.sid,
                'status': message.status,
                'error_code': message.error_code,
                'error_message': message.error_message
            }

        except Exception as e:
            logger.error(f"Error getting message status for {message_sid}: {e}")
            return {
                'message_sid': message_sid,
                'status': 'error',
                'error': str(e)
            }


# Factory function for dependency injection
def create_whatsapp_service(account_sid: str, auth_token: str, from_number: str) -> WhatsAppService:
    """Factory function to create WhatsAppService instance."""
    return WhatsAppService(account_sid, auth_token, from_number)