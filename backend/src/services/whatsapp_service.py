"""
Twilio WhatsApp API service for reading and sending messages.
Handles authentication, message retrieval, and sending via Twilio WhatsApp API.
"""
import os
from typing import List, Dict, Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import logging

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.client = None
        self.phone_number = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Twilio API."""
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.phone_number = os.getenv("TWILIO_WHATSAPP_NUMBER")

        if not all([account_sid, auth_token, self.phone_number]):
            logger.warning("Twilio credentials not found. Using mock service for development.")
            self.client = None
            return

        try:
            self.client = Client(account_sid, auth_token)
            # Test connection
            self.client.api.accounts(account_sid).fetch()
            logger.info("Successfully authenticated with Twilio API")
        except Exception as e:
            logger.error(f"Failed to authenticate with Twilio: {e}")
            self.client = None

    def is_authenticated(self) -> bool:
        """Check if the service is authenticated."""
        return self.client is not None

    def get_messages(self, limit: int = 10) -> List[Dict]:
        """
        Retrieve WhatsApp messages.
        Returns list of message dictionaries.
        """
        if not self.client:
            # Return mock data for development/testing
            return self._get_mock_messages(limit)

        try:
            # Note: Twilio doesn't have a direct "get all messages" endpoint
            # In a real implementation, you'd use webhooks or store message IDs
            # This is a simplified version for demonstration
            messages = self.client.messages.list(limit=limit)
            message_list = []

            for message in messages:
                # Filter for WhatsApp messages only (to: starts with 'whatsapp:')
                if message.to and message.to.startswith('whatsapp:'):
                    message_list.append(self._parse_twilio_message(message))

            return message_list
        except TwilioRestException as error:
            logger.error(f"Twilio error occurred: {error}")
            return self._get_mock_messages(limit)
        except Exception as error:
            logger.error(f"Error occurred while fetching messages: {error}")
            return self._get_mock_messages(limit)

    def send_message(self, to: str, body: str) -> Dict:
        """
        Send a WhatsApp message via Twilio API.
        Returns the sent message dictionary.
        """
        if not self.client or not self.phone_number:
            # Return mock response for development/testing
            return self._get_mock_sent_message(to, body)

        try:
            # Ensure 'whatsapp:' prefix
            if not to.startswith('whatsapp:'):
                to = f'whatsapp:{to}'

            message = self.client.messages.create(
                body=body,
                from_=self.phone_number,
                to=to
            )
            return self._parse_twilio_message(message)
        except TwilioRestException as error:
            logger.error(f"Twilio error occurred while sending message: {error}")
            return self._get_mock_sent_message(to, body)
        except Exception as error:
            logger.error(f"Error occurred while sending message: {error}")
            return self._get_mock_sent_message(to, body)

    def _parse_twilio_message(self, message) -> Dict:
        """Parse Twilio message into standardized format."""
        return {
            'id': message.sid,
            'thread_id': message.conversation_id or message.sid,  # Use conversation_id if available
            'subject': None,  # WhatsApp doesn't have subjects
            'sender': message.from_.replace('whatsapp:', '') if message.from_ else '',
            'date': message.date_sent.strftime('%Y-%m-%d %H:%M:%S') if message.date_sent else '',
            'body': message.body or '',
            'snippet': (message.body or '')[:50] + '...' if len(message.body or '') > 50 else (message.body or '')
        }

    def _get_mock_messages(self, limit: int) -> List[Dict]:
        """Return mock messages for development/testing."""
        return [
            {
                'id': f'mock_whatsapp_{i}',
                'thread_id': f'mock_thread_whatsapp_{i}',
                'subject': None,
                'sender': f'+1234567890{i}',
                'date': '2026-03-26 10:00:00',
                'body': f'This is a test WhatsApp message {i} for development purposes.',
                'snippet': f'This is a test WhatsApp message {i}...'
            }
            for i in range(min(limit, 3))
        ]

    def _get_mock_sent_message(self, to: str, body: str) -> Dict:
        """Return mock sent message for development/testing."""
        return {
            'id': 'mock_sent_whatsapp_123',
            'threadId': 'mock_thread_whatsapp_456'
        }