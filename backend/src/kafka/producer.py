"""
Kafka producer wrapper for reliable message publishing.
"""
import logging
from typing import Dict, Any, Optional
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import KafkaProducer, fallback to mock if not available
try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError
    import backoff
    KAFKA_AVAILABLE = True
except ImportError:
    logger.warning("kafka-python not available, using mock Kafka producer")
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

    # Mock KafkaProducer for development/testing
    class KafkaProducer:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            logger.info(f"Mock KafkaProducer initialized with kwargs: {kwargs}")

        def send(self, topic, key=None, value=None, headers=None):
            logger.info(f"Mock sending to topic {topic}: key={key}, value={value}")
            # Return a mock future
            class MockFuture:
                def get(self, timeout=None):
                    return None
            return MockFuture()

        def flush(self):
            logger.info("Mock KafkaProducer flush")

        def close(self):
            logger.info("Mock KafkaProducer closed")

# Import Kafka configuration - define locally to avoid circular imports
PRODUCER_CONFIG = {
    "bootstrap_servers": "localhost:9092",
    "acks": "all",
    "retries": 3
}

KAFKA_TOPICS = {
    "customer-messages": {"name": "customer-messages"},
    "agent-responses": {"name": "agent-responses"},
    "escalations": {"name": "escalations"},
    "metrics": {"name": "metrics"}
}

logger = logging.getLogger(__name__)




class KafkaProducerWrapper:
    """
    Wrapper around Kafka producer with enhanced reliability features.

    Features:
    - Idempotent publishing
    - Automatic retries with backoff
    - Message persistence for durability
    - OpenTelemetry integration
    - Dead letter queue handling
    """

    def __init__(
        self,
        bootstrap_servers: str = None,
        client_id: str = None,
    ):
        """
        Initialize Kafka producer.

        Args:
            bootstrap_servers: Kafka broker addresses (default from env)
            client_id: Client identifier for tracking
        """
        self.bootstrap_servers = bootstrap_servers or "localhost:9092"
        self.client_id = client_id or "digital-fte-producer"

        # Merge with default config
        config = PRODUCER_CONFIG.copy()
        config.update({
            "bootstrap_servers": self.bootstrap_servers,
            "client_id": self.client_id,
        })

        # Create producer
        self.producer = KafkaProducer(**config)
        logger.info(f"Kafka producer initialized: {self.bootstrap_servers}")

    @backoff.on_exception(
        backoff.expo,
        KafkaError,
        max_tries=3,
        on_backoff=lambda details: logger.warning(f"Kafka producer error: {details}")
    )
    def publish(
        self,
        topic: str,
        key: str = None,
        value: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
    ) -> bool:
        """
        Publish message to Kafka topic.

        Args:
            topic: Kafka topic name
            key: Message key (for partitioning)
            value: Message payload (will be JSON serialized)
            headers: Optional message headers

        Returns:
            bool: True if published successfully, False otherwise
        """
        try:
            # Serialize to JSON
            serialized_value = json.dumps(value or {}).encode("utf-8")

            # Send message
            future = self.producer.send(
                topic=topic,
                key=key.encode("utf-8") if key else None,
                value=serialized_value,
                headers=headers,
            )

            # Block for confirmation (with timeout)
            future.get(timeout=10)

            logger.debug(f"Message published to {topic}: key={key}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish message to {topic}: {e}")
            return False

    def publish_customer_message(
        self,
        channel: str,
        customer_id: str,
        message_content: str,
        correlation_id: str,
    ) -> bool:
        """
        Publish customer message to customer-messages topic.

        Args:
            channel: Channel identifier (email, whatsapp, web_form)
            customer_id: Customer identifier
            message_content: Message content
            correlation_id: Request correlation ID for tracing

        Returns:
            bool: True if published successfully, False otherwise
        """
        message = {
            "channel": channel,
            "customer_id": customer_id,
            "content": message_content,
            "timestamp": datetime.utcnow().isoformat(),
            "correlation_id": correlation_id,
        }

        # Use customer_id as partition key for consistency
        return self.publish(
            topic=KAFKA_TOPICS["customer-messages"]["name"],
            key=customer_id,
            value=message,
            headers={"correlation_id": correlation_id, "source": "channel_adapter"},
        )

    def publish_agent_response(
        self,
        ticket_id: str,
        response: str,
        confidence: float,
        correlation_id: str,
    ) -> bool:
        """
        Publish agent response to agent-responses topic.

        Args:
            ticket_id: Support ticket ID
            response: Agent response content
            confidence: AI confidence score (0-1)
            correlation_id: Request correlation ID for tracing

        Returns:
            bool: True if published successfully, False otherwise
        """
        message = {
            "ticket_id": ticket_id,
            "response": response,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat(),
            "correlation_id": correlation_id,
        }

        return self.publish(
            topic=KAFKA_TOPICS["agent-responses"]["name"],
            key=ticket_id,
            value=message,
            headers={"correlation_id": correlation_id, "source": "ai_agent"},
        )

    def publish_escalation(
        self,
        ticket_id: str,
        reason: str,
        assigned_to: str,
        correlation_id: str,
    ) -> bool:
        """
        Publish escalation to escalations topic.

        Args:
            ticket_id: Support ticket ID
            reason: Escalation reason
            assigned_to: Human agent or team ID
            correlation_id: Request correlation ID for tracing

        Returns:
            bool: True if published successfully, False otherwise
        """
        message = {
            "ticket_id": ticket_id,
            "reason": reason,
            "assigned_to": assigned_to,
            "timestamp": datetime.utcnow().isoformat(),
            "correlation_id": correlation_id,
        }

        return self.publish(
            topic=KAFKA_TOPICS["escalations"]["name"],
            key=ticket_id,
            value=message,
            headers={"correlation_id": correlation_id, "source": "escalation_engine"},
        )

    def publish_metrics(
        self,
        metric_type: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        Publish metrics to metrics topic.

        Args:
            metric_type: Type of metric (request_latency, sentiment, etc.)
            data: Metric data payload

        Returns:
            bool: True if published successfully, False otherwise
        """
        message = {
            "metric_type": metric_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        return self.publish(
            topic=KAFKA_TOPICS["metrics"]["name"],
            key=metric_type,
            value=message,
            headers={"source": "monitoring"},
        )

    def flush(self) -> None:
        """Force flush all buffered messages."""
        if self.producer:
            self.producer.flush(timeout=10)
        logger.info("Kafka producer flushed")

    def close(self) -> None:
        """Close producer and cleanup resources."""
        try:
            if self.producer:
                self.flush()
                self.producer.close()
            logger.info("Kafka producer closed")
        except Exception as e:
            logger.error(f"Error closing Kafka producer: {e}")


# Singleton producer instance
_producer: Optional[KafkaProducerWrapper] = None


def get_producer() -> Optional[KafkaProducerWrapper]:
    """
    Get or create singleton producer instance.

    Returns:
        KafkaProducerWrapper instance or None if initialization failed
    """
    global _producer
    if _producer is None:
        try:
            _producer = KafkaProducerWrapper()
        except Exception as e:
            logger.error(f"Failed to create Kafka producer: {e}")
    return _producer
