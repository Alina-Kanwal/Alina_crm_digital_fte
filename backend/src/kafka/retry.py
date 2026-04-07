"""
Message acknowledgment and retry mechanisms for Kafka.

Provides reliable message processing with configurable retry policies,
exponential backoff, and idempotency guarantees.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Try to import backoff, fallback to mock if not available
try:
    import backoff
    BACKOFF_AVAILABLE = True
except ImportError:
    logger.warning("backoff not available, using mock backoff")
    BACKOFF_AVAILABLE = False

    # Mock backoff for development/testing
    class mock_backoff:
        class expo:
            pass

        @staticmethod
        def on_exception(*args, **kwargs):
            def decorator(func):
                return func
            return decorator

    backoff = mock_backoff()

from src.kafka.dlq import DLQRetryPolicy


class RetryConfig:
    """
    Configuration for message retry behavior.

    Attributes:
        max_retries: Maximum number of retry attempts
        initial_backoff: Initial backoff in seconds
        max_backoff: Maximum backoff in seconds
        backoff_multiplier: Multiplier for exponential backoff
        jitter: Add randomness to backoff to avoid thundering herd
    """

    DEFAULT = {
        "max_retries": 3,
        "initial_backoff": 1,  # seconds
        "max_backoff": 300,  # 5 minutes
        "backoff_multiplier": 2,
        "jitter": True,
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize retry configuration."""
        self.config = {**self.DEFAULT, **(config or {})}

    @property
    def max_retries(self) -> int:
        return self.config["max_retries"]

    @property
    def initial_backoff(self) -> int:
        return self.config["initial_backoff"]

    @property
    def max_backoff(self) -> int:
        return self.config["max_backoff"]

    @property
    def backoff_multiplier(self) -> float:
        return self.config["backoff_multiplier"]

    @property
    def jitter(self) -> bool:
        return self.config["jitter"]

    def get_backoff(self, attempt: int) -> int:
        """
        Calculate backoff time for given retry attempt.

        Args:
            attempt: Retry attempt number (1-based)

        Returns:
            int: Backoff time in seconds
        """
        base = self.initial_backoff * (self.backoff_multiplier ** (attempt - 1))
        capped = min(base, self.max_backoff)

        # Add jitter if configured
        if self.jitter:
            import random
            jitter_amount = int(capped * 0.1)  # 10% jitter
            capped = random.randint(max(0, capped - jitter_amount), capped + jitter_amount)

        return capped


class MessageAck:
    """
    Message acknowledgment wrapper.

    Provides controlled acknowledgment with retry logic
    and proper error handling.
    """

    def __init__(
        self,
        topic: str,
        partition: int,
        offset: int,
        key: Optional[str],
        correlation_id: Optional[str],
    ):
        """
        Initialize message acknowledgment wrapper.

        Args:
            topic: Topic name
            partition: Partition number
            offset: Message offset
            key: Message key (for idempotency)
            correlation_id: Correlation ID for tracing
        """
        self.topic = topic
        self.partition = partition
        self.offset = offset
        self.key = key
        self.correlation_id = correlation_id
        self._acknowledged = False
        self._retry_count = 0
        self._last_error: Optional[Exception] = None
        self._acknowledged_at: Optional[datetime] = None

    @property
    def is_acknowledged(self) -> bool:
        """Check if message has been acknowledged."""
        return self._acknowledged

    @property
    def retry_count(self) -> int:
        """Get number of retry attempts."""
        return self._retry_count

    @property
    def last_error(self) -> Optional[Exception]:
        """Get last error that occurred."""
        return self._last_error

    def acknowledge(self) -> None:
        """Mark message as successfully acknowledged."""
        self._acknowledged = True
        self._acknowledged_at = datetime.utcnow()
        logger.debug(
            f"Message acknowledged: topic={self.topic}, partition={self.partition}, "
            f"offset={self.offset}, correlation_id={self.correlation_id}"
        )

    def record_error(self, error: Exception) -> None:
        """Record error for message processing."""
        self._last_error = error
        self._retry_count += 1
        logger.warning(
            f"Message error: topic={self.topic}, partition={self.partition}, "
            f"offset={self.offset}, error={error}, retry={self._retry_count}"
        )

    def __repr__(self) -> str:
        return (
            f"MessageAck(topic={self.topic}, partition={self.partition}, "
            f"offset={self.offset}, acknowledged={self._acknowledged}, "
            f"retries={self._retry_count})"
        )


async def process_with_retry(
    message: Dict[str, Any],
    handler: Callable[[Dict[str, Any]], Any],
    retry_config: Optional[RetryConfig] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, Any]:
    """
    Process message with configurable retry logic.

    Args:
        message: Message to process
        handler: Function to call to process message
        retry_config: Retry configuration (uses default if None)
        context: Optional context for error reporting

    Returns:
        Tuple of (success: bool, result: Any or Exception)
    """
    retry_config = retry_config or RetryConfig()
    context = context or {}

    for attempt in range(1, retry_config.max_retries + 1):
        try:
            result = handler(message)
            return True, result

        except Exception as e:
            logger.warning(
                f"Processing attempt {attempt}/{retry_config.max_retries} failed: {e}, "
                f"context={context}"
            )

            # Last attempt failed - give up
            if attempt >= retry_config.max_retries:
                logger.error(
                    f"Processing failed after {retry_config.max_retries} attempts: {e}, "
                    f"context={context}"
                )
                return False, e

            # Calculate backoff time
            backoff = retry_config.get_backoff(attempt)
            logger.info(f"Waiting {backoff}s before retry...")
            await asyncio.sleep(backoff)

    return False, Exception("Max retries exceeded")


class IdempotentProcessor:
    """
    Idempotent message processor.

    Ensures that duplicate messages don't cause duplicate effects
    by tracking processed message IDs.
    """

    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize idempotent processor.

        Args:
            ttl_seconds: Time-to-live for processed ID cache
        """
        self.processed_ids: Dict[str, datetime] = {}
        self.ttl_seconds = ttl_seconds

    def is_processed(self, message_id: str) -> bool:
        """
        Check if message has already been processed.

        Args:
            message_id: Unique message identifier

        Returns:
            bool: True if already processed, False otherwise
        """
        if message_id not in self.processed_ids:
            return False

        # Check TTL
        processed_at = self.processed_ids[message_id]
        if datetime.utcnow() - processed_at > timedelta(seconds=self.ttl_seconds):
            # Expired - can process again
            del self.processed_ids[message_id]
            return False

        return True

    def mark_processed(self, message_id: str) -> None:
        """
        Mark message as processed.

        Args:
            message_id: Unique message identifier
        """
        self.processed_ids[message_id] = datetime.utcnow()
        logger.debug(f"Message marked as processed: {message_id}")

    def cleanup_expired(self) -> int:
        """
        Clean up expired processed IDs.

        Returns:
            int: Number of IDs removed
        """
        cutoff = datetime.utcnow() - timedelta(seconds=self.ttl_seconds)
        expired_ids = [
            msg_id
            for msg_id, processed_at in self.processed_ids.items()
            if processed_at < cutoff
        ]

        for msg_id in expired_ids:
            del self.processed_ids[msg_id]

        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired processed IDs")

        return len(expired_ids)


# Global idempotent processor instance
_idempotent_processor: Optional[IdempotentProcessor] = None


def get_idempotent_processor(ttl_seconds: int = 3600) -> IdempotentProcessor:
    """
    Get or create singleton idempotent processor.

    Args:
        ttl_seconds: Time-to-live for processed ID cache

    Returns:
        IdempotentProcessor instance
    """
    global _idempotent_processor
    if _idempotent_processor is None:
        _idempotent_processor = IdempotentProcessor(ttl_seconds=ttl_seconds)
    return _idempotent_processor


async def process_message_idempotently(
    message: Dict[str, Any],
    handler: Callable[[Dict[str, Any]], Any],
    id_field: str = "correlation_id",
    retry_config: Optional[RetryConfig] = None,
) -> Tuple[bool, Any, bool]:
    """
    Process message with idempotency guarantee.

    Args:
        message: Message to process
        handler: Function to call to process message
        id_field: Field name containing unique ID
        retry_config: Retry configuration

    Returns:
        Tuple of (success: bool, result: Any, was_duplicate: bool)
    """
    processor = get_idempotent_processor()

    message_id = message.get(id_field)
    if not message_id:
        logger.warning(f"Message missing ID field '{id_field}', processing without idempotency")
        success, result = await process_with_retry(message, handler, retry_config)
        return success, result, False

    # Check if already processed
    if processor.is_processed(message_id):
        logger.info(f"Message already processed, skipping: {message_id}")
        return True, None, True

    # Process message
    success, result = await process_with_retry(message, handler, retry_config)

    # Mark as processed if successful
    if success:
        processor.mark_processed(message_id)

    return success, result, False


@backoff.on_exception(
    backoff.expo,
    Exception,
    max_tries=3,
    on_backoff=lambda details: logger.warning(f"Message processing backoff: {details}")
)
async def process_message_with_acks(
    message: Dict[str, Any],
    handler: Callable[[Dict[str, Any]], Any],
    retry_config: Optional[RetryConfig] = None,
    ack_callback: Optional[Callable[[MessageAck], None]] = None,
) -> Tuple[bool, Any, MessageAck]:
    """
    Process message with full acknowledgment lifecycle.

    Args:
        message: Message to process
        handler: Function to call to process message
        retry_config: Retry configuration
        ack_callback: Optional callback to call after ack

    Returns:
        Tuple of (success: bool, result: Any, ack: MessageAck)
    """
    # Create ack wrapper
    ack = MessageAck(
        topic=message.get("topic", "unknown"),
        partition=message.get("partition", 0),
        offset=message.get("offset", 0),
        key=message.get("key"),
        correlation_id=message.get("correlation_id"),
    )

    try:
        # Process with retry
        success, result = await process_with_retry(message, handler, retry_config)

        if success:
            # Acknowledge success
            ack.acknowledge()
            if ack_callback:
                await ack_callback(ack)
        else:
            # Record error for DLQ handling
            if result and isinstance(result, Exception):
                ack.record_error(result)

        return success, result, ack

    except Exception as e:
        ack.record_error(e)
        return False, e, ack
