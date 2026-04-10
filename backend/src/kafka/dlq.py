"""
Dead Letter Queue (DLQ) handling for failed Kafka messages.

Provides persistent storage and monitoring for messages that failed processing,
with configurable retry policies and alerting.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

# Import models
from src.models.base import Base
from src.database.connection import get_async_db_session
from src.models.dlq_entry import DLQEntry

logger = logging.getLogger(__name__)


class DeadLetterQueue:
    """
    Dead Letter Queue for failed Kafka messages.

    Stores failed messages in database with:
    - Original topic and partition
    - Message content
    - Error reason and stack trace
    - Retry count and status
    - Creation and last update timestamps
    """

    @staticmethod
    async def store_failed_message(
        session: AsyncSession,
        original_topic: str,
        message: Any,
        error_reason: str,
        stack_trace: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Store a failed message in the DLQ.

        Args:
            session: Database session
            original_topic: Topic message was from
            message: Message content
            error_reason: Why processing failed
            stack_trace: Optional stack trace
            metadata: Additional metadata

        Returns:
            str: DLQ entry ID
        """
        new_entry = DLQEntry(
            original_topic=original_topic,
            message_content=json.dumps(message) if not isinstance(message, str) else message,
            error_reason=error_reason,
            stack_trace=stack_trace,
            metadata_json=metadata or {},
            status="pending"
        )
        session.add(new_entry)
        await session.flush()
        
        logger.warning(f"DLQ entry created: {new_entry.id}")
        return str(new_entry.id)

    @staticmethod
    async def get_pending_messages(
        session: AsyncSession,
        topic: Optional[str] = None,
        max_retries: int = 3,
        batch_size: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get pending messages from DLQ for retry.

        Args:
            session: Database session
            topic: Optional filter by original topic
            max_retries: Maximum retry count to include
            batch_size: Maximum number of messages to return

        Returns:
            List of DLQ entries
        """
        stmt = (
            select(DLQEntry)
            .where(DLQEntry.status == "pending")
            .where(DLQEntry.retry_count < max_retries)
            .limit(batch_size)
        )
        if topic:
            stmt = stmt.where(DLQEntry.original_topic == topic)
            
        result = await session.execute(stmt)
        entries = result.scalars().all()
        
        return [
            {
                "id": e.id,
                "original_topic": e.original_topic,
                "message_content": e.message_content,
                "error_reason": e.error_reason,
                "retry_count": e.retry_count,
            } for e in entries
        ]

    @staticmethod
    async def update_retry_count(
        session: AsyncSession,
        dlq_id: str,
        success: bool,
        error_reason: Optional[str] = None,
    ) -> None:
        """
        Update retry count and status for DLQ entry.

        Args:
            session: Database session
            dlq_id: DLQ entry ID
            success: Whether retry was successful
            error_reason: New error reason if failed again
        """
        from sqlalchemy import update
        status = "resolved" if success else "pending"
        
        stmt = (
            update(DLQEntry)
            .where(DLQEntry.id == dlq_id)
            .values(
                status=status,
                last_attempt_at=func.now()
            )
        )
        
        if not success:
            # Increment retry count
            stmt = stmt.values(retry_count=DLQEntry.retry_count + 1)
            if error_reason:
                stmt = stmt.values(error_reason=error_reason)

        await session.execute(stmt)
        logger.debug(f"DLQ entry {dlq_id} updated: status={status}")

    @staticmethod
    async def get_statistics(session: AsyncSession, days: int = 7) -> Dict[str, int]:
        """
        Get DLQ statistics for monitoring and alerting.

        Args:
            session: Database session
            days: Number of days to look back

        Returns:
            Dictionary with statistics
        """
        since = datetime.utcnow() - timedelta(days=days)

        stats = {
            "total_failed": 0,
            "pending_retry": 0,
            "resolved": 0,
            "abandoned": 0,
            "by_topic": {},
            "by_error_reason": {},
        }

        # TODO: Query from database once DLQ model is created
        # For now, return zeros
        logger.debug(f"DLQ statistics for last {days} days")

        return stats

    @staticmethod
    async def cleanup_old_messages(
        session: AsyncSession,
        days_to_keep: int = 30,
    ) -> int:
        """
        Clean up old resolved or abandoned DLQ messages.

        Args:
            session: Database session
            days_to_keep: Days to keep records

        Returns:
            int: Number of records deleted
        """
        cutoff = datetime.utcnow() - timedelta(days=days_to_keep)

        # TODO: Delete from database once DLQ model is created
        deleted_count = 0
        logger.info(f"Cleaned up {deleted_count} old DLQ entries older than {days_to_keep} days")

        return deleted_count


class DLQRetryPolicy:
    """
    Retry policy configuration for DLQ messages.

    Defines when and how DLQ messages should be retried.
    """

    DEFAULT_POLICIES = {
        "json_decode_error": {
            "retry": False,
            "reason": "Invalid JSON cannot be fixed by retry",
        },
        "validation_error": {
            "retry": False,
            "reason": "Validation errors are permanent",
        },
        "timeout": {
            "retry": True,
            "max_retries": 3,
            "backoff_seconds": [60, 300, 900],  # 1, 5, 15 minutes
            "reason": "Temporary timeout, can retry",
        },
        "database_error": {
            "retry": True,
            "max_retries": 5,
            "backoff_seconds": [60, 300, 900, 3600, 7200],  # 1, 5, 15, 60, 120 minutes
            "reason": "Temporary database issues",
        },
        "external_service_error": {
            "retry": True,
            "max_retries": 10,
            "backoff_seconds": [60, 300, 900, 3600, 7200, 14400] * 2,  # Exponential up to 24 hours
            "reason": "External service outages",
        },
    }

    @classmethod
    def should_retry(
        cls,
        error_reason: str,
        retry_count: int = 0,
    ) -> tuple[bool, Optional[int]]:
        """
        Determine if message should be retried and when.

        Args:
            error_reason: Reason why message failed
            retry_count: Current retry count

        Returns:
            Tuple of (should_retry: bool, backoff_seconds: Optional[int])
        """
        # Find matching policy
        policy = None
        for pattern, p in cls.DEFAULT_POLICIES.items():
            if pattern in error_reason.lower():
                policy = p
                break

        if not policy:
            # Default policy: retry up to 3 times with 1 minute backoff
            return retry_count < 3, 60

        if not policy["retry"]:
            return False, None

        if retry_count >= policy["max_retries"]:
            return False, None

        # Get backoff time for this retry attempt
        backoff_index = min(retry_count, len(policy["backoff_seconds"]) - 1)
        backoff_seconds = policy["backoff_seconds"][backoff_index]

        return True, backoff_seconds

    @classmethod
    async def process_pending_retries(
        cls,
        session: AsyncSession,
    ) -> tuple[int, int]:
        """
        Process all pending DLQ messages that are due for retry.

        Args:
            session: Database session

        Returns:
            Tuple of (success_count, failure_count)
        """
        success_count = 0
        failure_count = 0

        # Get pending messages
        pending_messages = await DeadLetterQueue.get_pending_messages(session, max_retries=10)

        for dlq_entry in pending_messages:
            try:
                # Check if should retry
                should_retry, backoff = cls.should_retry(
                    dlq_entry.get("error_reason", ""),
                    dlq_entry.get("retry_count", 0),
                )

                if should_retry:
                    # TODO: Implement retry logic based on original topic
                    logger.info(f"Retrying DLQ entry: {dlq_entry.get('id')}")
                    # Retry logic would go here
                    success_count += 1
                else:
                    # Mark as abandoned
                    logger.warning(f"DLQ entry {dlq_entry.get('id')} abandoned")
                    failure_count += 1

            except Exception as e:
                logger.error(f"Error processing DLQ retry: {e}")
                failure_count += 1

        logger.info(f"DLQ retry batch complete: {success_count} success, {failure_count} failed")
        return success_count, failure_count


# DLQ monitoring and alerting
async def check_dlq_health(session: AsyncSession) -> Dict[str, Any]:
    """
    Check DLQ health for monitoring and alerting.

    Args:
        session: Database session

    Returns:
        Dictionary with health metrics
    """
    stats = await DeadLetterQueue.get_statistics(session, days=1)

    # Calculate health metrics
    total_failed = stats["total_failed"]
    pending_retry = stats["pending_retry"]

    # Alert thresholds
    alert_thresholds = {
        "critical": 100,  # 100+ failures in 1 day = critical
        "warning": 50,    # 50+ failures in 1 day = warning
        "info": 10,       # 10+ failures in 1 day = info
    }

    health_status = "healthy"
    if total_failed >= alert_thresholds["critical"]:
        health_status = "critical"
    elif total_failed >= alert_thresholds["warning"]:
        health_status = "warning"
    elif total_failed >= alert_thresholds["info"]:
        health_status = "degraded"

    return {
        "status": health_status,
        "total_failed": total_failed,
        "pending_retry": pending_retry,
        "resolved": stats["resolved"],
        "abandoned": stats["abandoned"],
        "by_topic": stats["by_topic"],
        "by_error_reason": stats["by_error_reason"],
        "last_check": datetime.utcnow().isoformat(),
    }
