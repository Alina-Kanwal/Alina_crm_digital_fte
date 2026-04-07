"""
Gmail API integration module for Digital FTE AI Customer Success Agent.
Handles receiving, parsing, and replying to customer emails via Gmail API.
"""

import asyncio
import base64
import logging
from typing import Dict, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


class GmailService:
    """Service for handling Gmail API operations."""

    def __init__(self, credentials_file: str = 'credentials.json', token_file: str = 'token.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Gmail API using OAuth2."""
        creds = None

        # Load existing token
        try:
            with open(self.token_file, 'r') as token:
                creds = Credentials.from_authorized_user_info(
                    eval(token.read()), SCOPES
                )
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.warning(f"Could not load existing token: {e}")

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Could not refresh token: {e}")
                    creds = None

            if not creds:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open(self.token_file, 'w') as token:
                token.write(str(creds.to_json()))

        try:
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail API service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gmail API service: {e}")
            raise

    async def fetch_unread_messages(self, max_results: int = 10) -> list[Dict[str, Any]]:
        """
        Fetch unread messages from Gmail inbox.

        Args:
            max_results: Maximum number of messages to fetch

        Returns:
            List of message dictionaries with parsed content
        """
        try:
            # Get unread messages
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            logger.info(f"Found {len(messages)} unread messages")

            # Fetch full message details
            detailed_messages = []
            for message in messages:
                msg_detail = self.service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()

                parsed_message = self._parse_message(msg_detail)
                parsed_message['gmail_id'] = message['id']
                detailed_messages.append(parsed_message)

            return detailed_messages

        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            return []
        except Exception as e:
            logger.error(f"Error fetching unread messages: {e}")
            return []

    def _parse_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Gmail message into standardized format.

        Args:
            message: Raw Gmail message object

        Returns:
            Parsed message dictionary
        """
        headers = message['payload'].get('headers', [])

        # Extract headers
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), '')

        # Extract body
        body = self._extract_body(message['payload'])

        return {
            'id': message['id'],
            'thread_id': message['threadId'],
            'subject': subject,
            'sender': sender,
            'date': date,
            'body': body,
            'snippet': message.get('snippet', ''),
            'labels': message.get('labelIds', [])
        }

    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """
        Extract text body from Gmail message payload.

        Args:
            payload: Gmail message payload

        Returns:
            Text body of the message
        """
        body = ""

        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
                elif part['mimeType'] == 'text/html':
                    # Fallback to HTML if no plain text
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
        else:
            # Single part message
            if payload['mimeType'] == 'text/plain':
                data = payload['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')
            elif payload['mimeType'] == 'text/html':
                data = payload['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')

        return body.strip()

    async def send_reply(self, to: str, subject: str, body: str, thread_id: Optional[str] = None) -> bool:
        """
        Send a reply email via Gmail API.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            thread_id: Thread ID to reply to (optional)

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject

            # Add body
            message.attach(MIMEText(body, 'plain'))

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            # Send message
            send_message = {
                'raw': raw_message
            }

            if thread_id:
                send_message['threadId'] = thread_id

            sent_message = self.service.users().messages().send(
                userId='me',
                body=send_message
            ).execute()

            logger.info(f"Reply sent successfully. Message ID: {sent_message['id']}")
            return True

        except HttpError as error:
            logger.error(f"Failed to send reply: {error}")
            return False
        except Exception as e:
            logger.error(f"Error sending reply: {e}")
            return False

    async def mark_as_read(self, message_id: str) -> bool:
        """
        Mark a Gmail message as read.

        Args:
            message_id: Gmail message ID

        Returns:
            True if successful, False otherwise
        """
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()

            logger.info(f"Message {message_id} marked as read")
            return True

        except HttpError as error:
            logger.error(f"Failed to mark message as read: {error}")
            return False
        except Exception as e:
            logger.error(f"Error marking message as read: {e}")
            return False


# Factory function for dependency injection
def create_gmail_service() -> GmailService:
    """Factory function to create GmailService instance."""
    return GmailService()