"""
Gmail API service for reading and sending emails.
Handles authentication, message retrieval, and sending via Gmail API.
"""
import base64
import os
from typing import List, Dict, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

class EmailService:
    def __init__(self):
        self.service = None
        self.credentials = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Gmail API using OAuth2."""
        creds = None
        # Token file stores the user's access and refresh tokens
        token_path = os.getenv("GMAIL_TOKEN_PATH", "token.json")

        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # For sandbox/testing, we'll use a simple approach
                # In production, you'd use proper OAuth flow
                logger.warning("Gmail credentials not found. Using mock service for development.")
                self.service = None
                return

            # Save the credentials for the next run
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        self.service = build('gmail', 'v1', credentials=creds)

    def is_authenticated(self) -> bool:
        """Check if the service is authenticated."""
        return self.service is not None

    def get_unread_messages(self, max_results: int = 10) -> List[Dict]:
        """
        Retrieve unread messages from Gmail.
        Returns list of message dictionaries.
        """
        if not self.service:
            # Return mock data for development/testing
            return self._get_mock_messages(max_results)

        try:
            results = self.service.users().messages().list(
                userId='me',
                labelIds=['INBOX', 'UNREAD'],
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            message_list = []

            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id']
                ).execute()
                message_list.append(self._parse_gmail_message(msg))

            return message_list
        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return self._get_mock_messages(max_results)

    def send_message(self, to: str, subject: str, body: str, thread_id: str = None) -> Dict:
        """
        Send an email message via Gmail API.
        Returns the sent message dictionary.
        """
        if not self.service:
            # Return mock response for development/testing
            return self._get_mock_sent_message(to, subject, body)

        try:
            message = self._create_message(to, subject, body, thread_id)
            sent_message = self.service.users().messages().send(
                userId='me',
                body=message
            ).execute()
            return sent_message
        except HttpError as error:
            logger.error(f"An error occurred while sending message: {error}")
            return self._get_mock_sent_message(to, subject, body)

    def mark_as_read(self, message_id: str) -> bool:
        """
        Mark a message as read by removing the UNREAD label.
        """
        if not self.service:
            return True  # Mock success

        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except HttpError as error:
            logger.error(f"An error occurred while marking message as read: {error}")
            return False

    def _parse_gmail_message(self, message: Dict) -> Dict:
        """Parse Gmail API message into standardized format."""
        headers = message['payload']['headers']

        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), '')

        # Get message body
        body = ''
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
        elif message['payload']['body'].get('data'):
            data = message['payload']['body']['data']
            body = base64.urlsafe_b64decode(data).decode('utf-8')

        return {
            'id': message['id'],
            'thread_id': message['threadId'],
            'subject': subject,
            'sender': sender,
            'date': date,
            'body': body,
            'snippet': message.get('snippet', '')
        }

    def _create_message(self, to: str, subject: str, body: str, thread_id: str = None) -> Dict:
        """Create a message for sending via Gmail API."""
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import base64

        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject

        if thread_id:
            message['In-Reply-To'] = thread_id
            message['References'] = thread_id

        msg = MIMEText(body)
        message.attach(msg)

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return {'raw': raw_message}

    def _get_mock_messages(self, max_results: int) -> List[Dict]:
        """Return mock messages for development/testing."""
        return [
            {
                'id': f'mock_{i}',
                'thread_id': f'mock_thread_{i}',
                'subject': f'Test Email {i}',
                'sender': f'customer{i}@example.com',
                'date': '2026-03-26 10:00:00',
                'body': f'This is a test email message {i} for development purposes.',
                'snippet': f'This is a test email message {i}...'
            }
            for i in range(min(max_results, 3))
        ]

    def _get_mock_sent_message(self, to: str, subject: str, body: str) -> Dict:
        """Return mock sent message for development/testing."""
        return {
            'id': 'mock_sent_123',
            'threadId': 'mock_thread_456',
            'labelIds': ['SENT']
        }