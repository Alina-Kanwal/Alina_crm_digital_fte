"""
Conversation management service.
Handles conversation history and context across channels for individual customers.
Includes comprehensive logging with correlation IDs for traceability.
"""
import logging
import uuid
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from src.services.database import SessionLocal
from src.models.conversation_thread import ConversationThread
from src.models.message import Message
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ConversationManager:
    """Service to manage conversation threads and message history."""

    def __init__(self, history_limit: int = 50, context_window: int = 10):
        """
        Initialize the conversation manager.

        Args:
            history_limit: Maximum messages to keep in history
            context_window: Number of recent messages to include in context
        """
        self.history_limit = history_limit
        self.context_window = context_window
        logger.info(f"Conversation manager initialized (history_limit={history_limit})")

    async def get_conversation_history(self, 
                                     thread_id: str, 
                                     correlation_id: Optional[str] = None) -> List[Dict]:
        """
        Retrieve conversation history for a thread.

        Args:
            thread_id: The conversation thread identifier (UUID)
            correlation_id: Optional correlation ID for tracing

        Returns:
            List of message dictionaries in chronological order
        """
        tag = f"[{correlation_id}] " if correlation_id else ""
        logger.debug(f"{tag}Retrieving history for thread: {thread_id}")

        db = SessionLocal()
        try:
            # Get the conversation thread
            thread = db.query(ConversationThread).filter(ConversationThread.id == thread_id).first()
            if not thread:
                logger.warning(f"{tag}Conversation thread not found: {thread_id}")
                return []

            # Get messages for this thread
            messages = db.query(Message).filter(
                Message.thread_id == thread.id
            ).order_by(Message.timestamp.asc()).limit(self.history_limit).all()

            # Convert to list of dictionaries
            history = [msg.to_dict() for msg in messages]

            logger.info(f"{tag}Retrieved {len(history)} messages for thread {thread_id}")
            return history

        except Exception as e:
            logger.error(f"{tag}Error retrieving conversation history: {e}")
            return []
        finally:
            db.close()

    async def create_conversation_thread(self, 
                                        customer_id: str, 
                                        channel: str, 
                                        subject: Optional[str] = None,
                                        correlation_id: Optional[str] = None) -> Optional[Dict]:
        """
        Create a new conversation thread for a customer.

        Args:
            customer_id: Customer ID
            channel: Communication channel
            subject: Subject or topic (optional)
            correlation_id: Optional correlation ID

        Returns:
            New thread info or None
        """
        tag = f"[{correlation_id}] " if correlation_id else ""
        logger.info(f"{tag}Creating new {channel} thread for customer {customer_id}")

        db = SessionLocal()
        try:
            thread_id = str(uuid.uuid4())
            new_thread = ConversationThread(
                id=thread_id,
                customer_id=customer_id,
                channel=channel,
                subject=subject,
                status="active",
                channel_history=[channel],
                started_at=datetime.utcnow(),
                last_updated_at=datetime.utcnow()
            )
            db.add(new_thread)
            db.commit()
            
            # Use the explicit ID to return the dict instead of trusting refresh on SQLite
            result = new_thread.to_dict()
            logger.info(f"{tag}Created thread ID: {thread_id}")
            return result

        except Exception as e:
            logger.error(f"{tag}Error creating conversation thread: {e}", exc_info=True)
            db.rollback()
            return None
        finally:
            db.close()

    async def add_message_to_conversation(self,
                                        thread_id: str,
                                        content: str,
                                        direction: str,
                                        channel: str,
                                        sentiment: Optional[str] = None,
                                        sentiment_score: Optional[float] = None,
                                        correlation_id: Optional[str] = None,
                                        metadata: Optional[Dict] = None) -> bool:
        """
        Add a message to a conversation thread and update thread metadata.

        Args:
            thread_id: The conversation thread ID
            content: Message body
            direction: incoming or outgoing
            channel: Communication channel
            sentiment: (Optional) Sentiment class
            sentiment_score: (Optional) Score -1.0 to 1.0
            correlation_id: (Optional) Trace ID
            metadata: (Optional) Message metadata

        Returns:
            True if successful
        """
        tag = f"[{correlation_id}] " if correlation_id else ""
        logger.debug(f"{tag}Adding {direction} message to thread {thread_id}")

        db = SessionLocal()
        try:
            # Check if thread exists
            thread = db.query(ConversationThread).filter(ConversationThread.id == thread_id).first()
            if not thread:
                logger.error(f"{tag}Cannot add message, thread not found: {thread_id}")
                return False

            # Create new message
            new_msg = Message(
                thread_id=thread_id,
                content=content,
                direction=direction,
                channel=channel,
                sentiment=sentiment,
                sentiment_score=sentiment_score,
                timestamp=datetime.utcnow(),
                message_metadata=metadata or {}
            )
            db.add(new_msg)

            # Update thread activity
            thread.last_updated_at = datetime.utcnow()
            thread.message_count += 1
            if channel not in thread.channel_history:
                thread.channel_history = list(thread.channel_history) + [channel]

            db.commit()
            logger.info(f"{tag}Added message to thread {thread_id} (count: {thread.message_count})")
            return True

        except Exception as e:
            logger.error(f"{tag}Error adding message to conversation: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    async def get_customer_conversations(self, 
                                        customer_id: str, 
                                        limit: int = 5,
                                        correlation_id: Optional[str] = None) -> List[Dict]:
        """
        Get all conversation threads for a customer.

        Args:
            customer_id: Customer ID
            limit: Max threads
            correlation_id: Trace ID

        Returns:
            List of thread dictionaries
        """
        tag = f"[{correlation_id}] " if correlation_id else ""
        logger.debug(f"{tag}Retrieving threads for customer {customer_id}")

        db = SessionLocal()
        try:
            threads = db.query(ConversationThread).filter(
                ConversationThread.customer_id == customer_id
            ).order_by(ConversationThread.last_updated_at.desc()).limit(limit).all()

            return [t.to_dict() for t in threads]
        except Exception as e:
            logger.error(f"{tag}Error getting threads for customer: {e}")
            return []
        finally:
            db.close()

    async def find_active_thread_by_customer_and_channel(self,
                                                       customer_id: str,
                                                       channel: str,
                                                       correlation_id: Optional[str] = None) -> Optional[Dict]:
        """
        Find an existing active thread for a customer and channel within a window (e.g. 24h).

        Args:
            customer_id: Customer ID
            channel: Communication channel
            correlation_id: Trace ID

        Returns:
            Existing thread dict or None
        """
        tag = f"[{correlation_id}] " if correlation_id else ""
        logger.debug(f"{tag}Searching for active {channel} thread for customer {customer_id}")

        db = SessionLocal()
        try:
            # Search for active thread updated in last 24h
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            thread = db.query(ConversationThread).filter(
                ConversationThread.customer_id == customer_id,
                ConversationThread.channel == channel,
                ConversationThread.status == "active",
                ConversationThread.last_updated_at >= cutoff_time
            ).order_by(ConversationThread.last_updated_at.desc()).first()

            if thread:
                return thread.to_dict()
            return None
        except Exception as e:
            logger.error(f"{tag}Error finding active thread: {e}")
            return None
        finally:
            db.close()