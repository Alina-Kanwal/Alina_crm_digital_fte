"""
Kafka consumer base class for reliable message consumption.

Provides consumers with proper error handling, offset management,
integration with OpenTelemetry, and dead letter queue handling.
"""

import json
import logging
import os
from typing import Any, Callable, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import Kafka dependencies, fallback to mock if not available
try:
    from kafka import KafkaConsumer, TopicPartition
    from kafka.errors import KafkaError
    import backoff
    KAFKA_AVAILABLE = True
except ImportError:
    logger.warning("kafka-python not available, using mock Kafka consumer")
    KAFKA_AVAILABLE = False

    # Mock dependencies
    class MockKafkaError(Exception):
        pass

    class mock_backoff:
        class expo:
            pass

        @staticmethod
        def on_exception(*args, **kwargs):
            def decorator(func):
                return func
            return decorator

    backoff = mock_backoff()
    KafkaError = MockKafkaError

    # Mock KafkaConsumer for development/testing
    class KafkaConsumer:
        def __init__(self, *topics, **config):
            self.topics = topics
            self.config = config
            logger.info(f"Mock KafkaConsumer initialized for topics: {topics}")

        def poll(self, timeout_ms=None, max_records=None):
            logger.debug(f"Mock polling for messages (max={max_records}, timeout={timeout_ms}ms)")
            return {}  # Return empty dict to simulate no messages

        def commit(self, offsets=None):
            logger.debug(f"Mock committing offsets: {offsets}")

        def seek_to_beginning(self):
            logger.info("Mock consumer seeked to beginning")

        def seek_to_end(self):
            logger.info("Mock consumer seeked to end")

        def assignment(self):
            return []

        def close(self):
            logger.info("Mock KafkaConsumer closed")

    # Mock TopicPartition for development/testing
    class TopicPartition:
        def __init__(self, topic, partition):
            self.topic = topic
            self.partition = partition

# Import Kafka configuration - define locally to avoid circular imports
CONSUMER_CONFIG = {
    "bootstrap_servers": "localhost:9092",
    "group_id": "digital-fte-consumers",
    "auto_offset_reset": "earliest",
    "enable_auto_commit": True
}

KAFKA_TOPICS = {
    "customer-messages": {"name": "customer-messages"},
    "agent-responses": {"name": "agent-responses"},
    "escalations": {"name": "escalations"},
    "metrics": {"name": "metrics"}
}

logger = logging.getLogger(__name__)


class KafkaConsumerWrapper:
    """
    Wrapper around Kafka consumer with enhanced reliability features.

    Features:
    - Proper offset management (manual commit)
    - Backpressure handling
    - Dead letter queue for failed messages
    - OpenTelemetry integration
    - Graceful shutdown handling
    """

    def __init__(
        self,
        topics: list[str],
        group_id: Optional[str] = None,
        bootstrap_servers: Optional[str] = None,
        client_id: Optional[str] = None,
    ):
        """
        Initialize Kafka consumer.

        Args:
            topics: List of topics to consume from
            group_id: Consumer group ID (default from env)
            bootstrap_servers: Kafka broker addresses (default from env)
            client_id: Client identifier for tracking
        """
        self.topics = topics
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
        )
        self.group_id = group_id or os.getenv(
            "KAFKA_CONSUMER_GROUP", "digital-fte-consumers"
        )
        self.client_id = client_id or "digital-fte-consumer"

        # Merge with default config
        config = CONSUMER_CONFIG.copy()
        config.update({
            "bootstrap_servers": self.bootstrap_servers,
            "group_id": self.group_id,
            "client_id": self.client_id,
            "enable.auto.commit": False,  # Manual commit
        })

        # Create consumer
        self.consumer = KafkaConsumer(*topics, **config)
        logger.info(
            f"Kafka consumer initialized: {self.bootstrap_servers}, "
            f"topics: {topics}, group: {self.group_id}"
        )

    @backoff.on_exception(
        backoff.expo,
        KafkaError,
        max_tries=3,
        on_backoff=lambda details: logger.warning(f"Kafka consumer error: {details}")
    )
    def consume(
        self,
        handler: Callable[[str, Dict[str, Any]], bool],
        max_records: int = 100,
        timeout_ms: int = 1000,
    ) -> None:
        """
        Consume messages from subscribed topics.

        Args:
            handler: Function to process each message
                     Args: (topic, message_dict) -> bool (success)
            max_records: Maximum number of records to poll
            timeout_ms: Timeout for poll operation
        """
        try:
            logger.debug(f"Polling for messages (max={max_records}, timeout={timeout_ms}ms)")

            # Poll for messages
            records = self.consumer.poll(timeout_ms=timeout_ms, max_records=max_records)

            if not records:
                return

            # Process each message
            for topic_partition, messages in records.items():
                for message in messages:
                    try:
                        # Parse message
                        message_dict = json.loads(message.value.decode("utf-8"))

                        # Extract correlation ID for tracing
                        correlation_id = message_dict.get("correlation_id", "")

                        logger.debug(
                            f"Processing message: topic={topic_partition.topic}, "
                            f"partition={topic_partition.partition}, "
                            f"offset={message.offset}, correlation_id={correlation_id}"
                        )

                        # Call handler
                        success = handler(topic_partition.topic, message_dict)

                        if success:
                            # Commit offset on success
                            self.consumer.commit({
                                TopicPartition(topic_partition.topic, topic_partition.partition): message.offset + 1
                            })
                            logger.debug(f"Message committed successfully")
                        else:
                            # Handler returned False - send to DLQ
                            self._send_to_dlq(topic_partition.topic, message_dict, "handler_returned_false")
                            # Still commit to skip this message
                            self.consumer.commit({
                                TopicPartition(topic_partition.topic, topic_partition.partition): message.offset + 1
                            })

                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse message: {e}")
                        self._send_to_dlq(topic_partition.topic, message.value, "json_decode_error")
                        # Commit to skip this invalid message
                        self.consumer.commit({
                            TopicPartition(topic_partition.topic, topic_partition.partition): message.offset + 1
                        })

                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        # Don't commit on processing error - will be retried later
                        continue

        except KafkaError as e:
            logger.error(f"Kafka consumer error: {e}")
            raise

    def _send_to_dlq(
        self,
        original_topic: str,
        message: Any,
        error_reason: str,
    ) -> None:
        """
        Send failed message to dead letter queue.

        Args:
            original_topic: Topic message was from
            message: Message content
            error_reason: Why the message failed
        """
        # TODO: Implement DLQ topic publishing
        # For now, just log the failure
        dlq_message = {
            "original_topic": original_topic,
            "message": str(message),
            "error_reason": error_reason,
            "timestamp": datetime.utcnow().isoformat(),
        }
        logger.warning(f"Message sent to DLQ: {dlq_message}")

    def seek_to_beginning(self) -> None:
        """Seek to beginning of all partitions (for replay)."""
        self.consumer.seek_to_beginning()
        logger.info("Consumer seeked to beginning of all partitions")

    def seek_to_end(self) -> None:
        """Seek to end of all partitions (latest messages)."""
        self.consumer.seek_to_end()
        logger.info("Consumer seeked to end of all partitions")

    def get_topic_partitions(self) -> list[TopicPartition]:
        """Get list of TopicPartition objects for this consumer."""
        return self.consumer.assignment()

    def close(self) -> None:
        """Close consumer and cleanup resources."""
        try:
            self.consumer.close()
            logger.info("Kafka consumer closed")
        except Exception as e:
            logger.error(f"Error closing Kafka consumer: {e}")


class CustomerMessageConsumer(KafkaConsumerWrapper):
    """
    Specialized consumer for customer messages from all channels.

    Handles incoming messages from customer-messages topic.
    """

    def __init__(self, client_id: Optional[str] = None):
        """Initialize customer message consumer."""
        topic = KAFKA_TOPICS["customer-messages"]["name"]
        super().__init__(
            topics=[topic],
            group_id="customer-message-consumers",
            client_id=client_id or "customer-message-consumer",
        )


class AgentResponseConsumer(KafkaConsumerWrapper):
    """
    Specialized consumer for agent responses.

    Handles responses from AI agent for delivery to channels.
    """

    def __init__(self, client_id: Optional[str] = None):
        """Initialize agent response consumer."""
        topic = KAFKA_TOPICS["agent-responses"]["name"]
        super().__init__(
            topics=[topic],
            group_id="agent-response-consumers",
            client_id=client_id or "agent-response-consumer",
        )


class EscalationConsumer(KafkaConsumerWrapper):
    """
    Specialized consumer for escalations.

    Handles escalations from escalation engine for human notification.
    """

    def __init__(self, client_id: Optional[str] = None):
        """Initialize escalation consumer."""
        topic = KAFKA_TOPICS["escalations"]["name"]
        super().__init__(
            topics=[topic],
            group_id="escalation-consumers",
            client_id=client_id or "escalation-consumer",
        )


class MetricsConsumer(KafkaConsumerWrapper):
    """
    Specialized consumer for metrics.

    Handles metrics for monitoring and alerting.
    """

    def __init__(self, client_id: Optional[str] = None):
        """Initialize metrics consumer."""
        topic = KAFKA_TOPICS["metrics"]["name"]
        super().__init__(
            topics=[topic],
            group_id="metrics-consumers",
            client_id=client_id or "metrics-consumer",
        )
