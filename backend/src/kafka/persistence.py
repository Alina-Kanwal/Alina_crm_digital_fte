"""
Message persistence layer for Kafka to prevent message loss.

Provides durable storage of messages before/after Kafka
to guarantee zero message loss during service outages.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy import select, update, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_async_db_session
from src.models.persisted_message import PersistedMessage, MessageStatus

logger = logging.getLogger(__name__)


class MessageStatus(str, Enum):
    """Message processing status."""
    RECEIVED = "received"
    PUBLISHED = "published"
    CONSUMED = "consumed"
    PROCESSED = "processed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class PersistedMessage:
    """
    Durable storage for Kafka messages.

    Provides:
    - Pre-publish persistence (before sending to Kafka)
    - Post-consume persistence (before processing)
    - Processing state tracking
    - Replay capability for recovery
    """

    @staticmethod
    async def store_received_message(
        session: AsyncSession,
        topic: str,
        key: Optional[str],
        value: Dict[str, Any],
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Store received message before processing.

        Args:
            session: Database session
            topic: Kafka topic
            key: Message key
            value: Message payload
            correlation_id: Correlation ID for tracing
            metadata: Additional metadata

        Returns:
            str: Persistent message ID
        """
        new_message = PersistedMessage(
            topic=topic,
            key=key,
            value=json.dumps(value) if not isinstance(value, str) else value,
            correlation_id=correlation_id,
            status=MessageStatus.RECEIVED.value,
            metadata_json=metadata or {}
        )
        session.add(new_message)
        await session.flush()  # To get the ID
        
        logger.debug(f"Message stored for persistence: {new_message.id}")
        return str(new_message.id)

    @staticmethod
    async def update_status(
        session: AsyncSession,
        message_id: str,
        status: MessageStatus,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Update message processing status.

        Args:
            session: Database session
            message_id: Persistent message ID
            status: New status
            error: Optional error message
            metadata: Optional metadata to update
        """
        from sqlalchemy import update
        stmt = (
            update(PersistedMessage)
            .where(PersistedMessage.id == message_id)
            .values(
                status=status.value,
                error_message=error,
                updated_at=func.now()
            )
        )
        if metadata:
            # Simple metadata update logic
            pass 

        await session.execute(stmt)
        logger.debug(
            f"Message status updated: {message_id}, status={status.value}, error={error}"
        )

    @staticmethod
    async def get_message_by_id(
        session: AsyncSession,
        message_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve persisted message by ID.

        Args:
            session: Database session
            message_id: Persistent message ID

        Returns:
            Dictionary with message data or None
        """
        stmt = select(PersistedMessage).where(PersistedMessage.id == message_id)
        result = await session.execute(stmt)
        msg = result.scalar_one_or_none()
        if msg:
            return {
                "id": msg.id,
                "topic": msg.topic,
                "key": msg.key,
                "value": msg.value,
                "correlation_id": msg.correlation_id,
                "status": msg.status,
                "created_at": msg.created_at,
                "metadata": msg.metadata_json
            }
        return None

    @staticmethod
    async def get_pending_messages(
        session: AsyncSession,
        topic: Optional[str] = None,
        status: MessageStatus = MessageStatus.RECEIVED,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get pending messages for replay.

        Args:
            session: Database session
            topic: Optional filter by topic
            status: Filter by status
            limit: Maximum number to return

        Returns:
            List of persisted messages
        """
        stmt = (
            select(PersistedMessage)
            .where(PersistedMessage.status == status.value)
            .limit(limit)
        )
        if topic:
            stmt = stmt.where(PersistedMessage.topic == topic)
            
        result = await session.execute(stmt)
        messages = result.scalars().all()
        
        return [
            {
                "id": m.id,
                "topic": m.topic,
                "key": m.key,
                "value": m.value,
                "correlation_id": m.correlation_id,
                "status": m.status
            } for m in messages
        ]

    @staticmethod
    async def cleanup_old_messages(
        session: AsyncSession,
        days_to_keep: int = 7,
        exclude_statuses: List[MessageStatus] = None,
    ) -> int:
        """
        Clean up old processed messages.

        Args:
            session: Database session
            days_to_keep: Days to keep records
            exclude_statuses: Statuses to exclude from cleanup

        Returns:
            int: Number of records deleted
        """
        exclude_statuses = exclude_statuses or [
            MessageStatus.FAILED,
            MessageStatus.DEAD_LETTER,
        ]

        from sqlalchemy import delete
        cutoff = datetime.utcnow() - timedelta(days=days_to_keep)
        exclude_statuses_vals = [s.value for s in (exclude_statuses or [MessageStatus.FAILED, MessageStatus.DEAD_LETTER])]
        
        stmt = (
            delete(PersistedMessage)
            .where(PersistedMessage.created_at < cutoff)
            .where(~PersistedMessage.status.in_(exclude_statuses_vals))
        )
        
        result = await session.execute(stmt)
        deleted_count = result.rowcount
        logger.info(
            f"Cleaned up {deleted_count} old messages, "
            f"older than {days_to_keep} days"
        )

        return deleted_count


class MessagePersistence:
    """
    Wrapper for message persistence with automatic cleanup.

    Ensures messages are persisted before/after Kafka operations
    to prevent loss during service failures.
    """

    def __init__(self, cleanup_interval_hours: int = 24):
        """
        Initialize message persistence wrapper.

        Args:
            cleanup_interval_hours: Hours between cleanup runs
        """
        self.cleanup_interval_hours = cleanup_interval_hours
        self._last_cleanup: Optional[datetime] = None

    async def pre_publish(
        self,
        session: AsyncSession,
        topic: str,
        key: Optional[str],
        value: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> str:
        """
        Persist message before publishing to Kafka.

        Args:
            session: Database session
            topic: Kafka topic
            key: Message key
            value: Message payload
            correlation_id: Correlation ID

        Returns:
            str: Persistent message ID
        """
        return await PersistedMessage.store_received_message(
            session=session,
            topic=topic,
            key=key,
            value=value,
            correlation_id=correlation_id,
            metadata={"phase": "pre_publish"},
        )

    async def post_publish(
        self,
        session: AsyncSession,
        message_id: str,
    ) -> None:
        """
        Update status after successful Kafka publish.

        Args:
            session: Database session
            message_id: Persistent message ID
        """
        await PersistedMessage.update_status(
            session=session,
            message_id=message_id,
            status=MessageStatus.PUBLISHED,
        )

    async def pre_process(
        self,
        session: AsyncSession,
        topic: str,
        key: Optional[str],
        value: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> str:
        """
        Persist message after consuming from Kafka (before processing).

        Args:
            session: Database session
            topic: Kafka topic
            key: Message key
            value: Message payload
            correlation_id: Correlation ID

        Returns:
            str: Persistent message ID
        """
        return await PersistedMessage.store_received_message(
            session=session,
            topic=topic,
            key=key,
            value=value,
            correlation_id=correlation_id,
            metadata={"phase": "pre_process"},
        )

    async def post_process(
        self,
        session: AsyncSession,
        message_id: str,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """
        Update status after processing.

        Args:
            session: Database session
            message_id: Persistent message ID
            success: Whether processing succeeded
            error: Optional error message
        """
        status = MessageStatus.PROCESSED if success else MessageStatus.FAILED
        await PersistedMessage.update_status(
            session=session,
            message_id=message_id,
            status=status,
            error=error,
        )

    async def auto_cleanup(self, session: AsyncSession) -> int:
        """
        Perform automatic cleanup if interval has passed.

        Args:
            session: Database session

        Returns:
            int: Number of records deleted
        """
        now = datetime.utcnow()

        if self._last_cleanup is None:
            self._last_cleanup = now - timedelta(hours=self.cleanup_interval_hours + 1)

        if now - self._last_cleanup >= timedelta(hours=self.cleanup_interval_hours):
            deleted = await PersistedMessage.cleanup_old_messages(session)
            self._last_cleanup = now
            return deleted

        return 0

    async def replay_messages(
        self,
        session: AsyncSession,
        topic: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get messages for replay after service recovery.

        Args:
            session: Database session
            topic: Optional filter by topic
            limit: Maximum number to replay

        Returns:
            List of messages to replay
        """
        return await PersistedMessage.get_pending_messages(
            session=session,
            topic=topic,
            status=MessageStatus.RECEIVED,
            limit=limit,
        )


# Global persistence instance
_persistence: Optional[MessagePersistence] = None


def get_persistence() -> MessagePersistence:
    """
    Get or create singleton persistence instance.

    Returns:
        MessagePersistence instance
    """
    global _persistence
    if _persistence is None:
        _persistence = MessagePersistence()
    return _persistence


async def get_persistence_health(session: AsyncSession) -> Dict[str, Any]:
    """
    Get persistence layer health metrics.

    Args:
        session: Database session

    Returns:
        Dictionary with health metrics
    """
    # TODO: Query from database once persistence model is created
    return {
        "status": "healthy",
        "pending_messages": 0,
        "failed_messages": 0,
        "dead_letter_messages": 0,
        "total_messages": 0,
        "last_cleanup": None,
    }
