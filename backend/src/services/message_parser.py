"""
Message parsing and normalization service.
Converts messages from different channels (email, WhatsApp, webform) into a common format.
"""
import re
import html
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MessageParser:
    """Service to parse and normalize incoming messages from various customer channels."""

    def __init__(self):
        pass

    async def parse_and_normalize(self, raw_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and normalize a message from any supported channel.
        
        Args:
            raw_message: The raw message payload from the source channel.
            
        Returns:
            A normalized dictionary containing:
            - body: The main content of the message.
            - sender: The sender identifier (email or phone).
            - subject: The subject or title of the inquiry.
            - channel: The source channel.
            - timestamp: Standardized ISO timestamp.
        """
        try:
            # Determine channel from raw message metadata or structure
            channel = raw_message.get('channel', 'webform').lower()
            
            normalized = {
                'raw': raw_message,
                'channel': channel,
                'timestamp': datetime.utcnow().isoformat()
            }

            if channel == 'email':
                normalized.update(self._parse_email(raw_message))
            elif channel == 'whatsapp':
                normalized.update(self._parse_whatsapp(raw_message))
            elif channel == 'webform':
                normalized.update(self._parse_webform(raw_message))
            else:
                # Generic fallback
                normalized.update({
                    'body': raw_message.get('body', raw_message.get('text', '')),
                    'sender': raw_message.get('sender', raw_message.get('from', 'unknown')),
                    'subject': raw_message.get('subject', 'Customer Inquiry')
                })

            # Common cleanups
            normalized['body'] = self._clean_content(normalized.get('body', ''))
            normalized['subject'] = self._clean_content(normalized.get('subject', 'Customer Inquiry'))
            
            logger.debug(f"Normalized message from {channel}: {normalized['subject']}")
            return normalized

        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            raise ValueError(f"Could not parse message: {str(e)}")

    def _parse_email(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Specific parsing logic for Gmail/Email."""
        return {
            'body': raw.get('body', raw.get('snippet', '')),
            'sender': raw.get('sender', raw.get('from', '')),
            'subject': raw.get('subject', 'Email Inquiry')
        }

    def _parse_whatsapp(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Specific parsing logic for Twilio/WhatsApp."""
        return {
            'body': raw.get('body', raw.get('msg', '')),
            'sender': raw.get('sender', raw.get('phone', '')),
            'subject': 'WhatsApp Message'
        }

    def _parse_webform(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Specific parsing logic for the React web form."""
        return {
            'body': raw.get('body', raw.get('message', '')),
            'sender': raw.get('sender', raw.get('email', '')),
            'subject': raw.get('subject', 'Web Form Submission')
        }

    def _clean_content(self, text: str) -> str:
        """Strip HTML tags and unescape content."""
        if not text:
            return ""
        # Remove HTML tags
        clean = re.compile('<.*?>')
        text = re.sub(clean, '', text)
        return html.unescape(text).strip()