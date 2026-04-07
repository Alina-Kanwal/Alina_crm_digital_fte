"""
Kafka configuration, topics, and components for Digital FTE system.

This module defines:
- Kafka topics configuration
- Producer and consumer wrappers
- Dead letter queue handling
- Retry mechanisms
- Message persistence layer
"""

# Import Kafka components
from src.kafka.producer import (
    KafkaProducerWrapper,
    get_producer,
)

from src.kafka.consumer import (
    KafkaConsumerWrapper,
    CustomerMessageConsumer,
    AgentResponseConsumer,
    EscalationConsumer,
    MetricsConsumer,
)

from src.kafka.dlq import (
    DeadLetterQueue,
    DLQRetryPolicy,
    check_dlq_health,
)

from src.kafka.retry import (
    RetryConfig,
    MessageAck,
    IdempotentProcessor,
    get_idempotent_processor,
    process_message_with_acks,
    process_message_idempotently,
    process_with_retry,
)

from src.kafka.persistence import (
    MessageStatus,
    PersistedMessage,
    MessagePersistence,
    get_persistence,
    get_persistence_health,
)

# Define topics directly to avoid circular imports
KAFKA_TOPICS = {
    "customer-messages": "customer-messages",
    "agent-responses": "agent-responses",
    "escalations": "escalations",
    "metrics": "metrics"
}

CONSUMER_CONFIG = {
    "bootstrap_servers": "localhost:9092",
    "group_id": "digital-fte-consumers",
    "auto_offset_reset": "earliest",
    "enable_auto_commit": True
}

PRODUCER_CONFIG = {
    "bootstrap_servers": "localhost:9092",
    "acks": "all",
    "retries": 3
}

__all__ = [
    # Configuration
    "KAFKA_TOPICS",
    "CONSUMER_CONFIG",
    "PRODUCER_CONFIG",
    # Producer
    "KafkaProducerWrapper",
    "get_producer",
    # Consumer
    "KafkaConsumerWrapper",
    "CustomerMessageConsumer",
    "AgentResponseConsumer",
    "EscalationConsumer",
    "MetricsConsumer",
    # DLQ
    "DeadLetterQueue",
    "DLQRetryPolicy",
    "check_dlq_health",
    # Retry
    "RetryConfig",
    "MessageAck",
    "IdempotentProcessor",
    "get_idempotent_processor",
    "process_message_with_acks",
    "process_message_idempotently",
    "process_with_retry",
    # Persistence
    "MessageStatus",
    "PersistedMessage",
    "MessagePersistence",
    "get_persistence",
    "get_persistence_health",
]
