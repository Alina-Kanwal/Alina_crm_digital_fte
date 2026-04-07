"""
Metrics collection infrastructure using Prometheus.

Provides centralized metrics definition, collection, and exposition
for monitoring application performance and business metrics.
"""

import logging
import time
from typing import Dict, Any, Callable, Optional
from functools import wraps
from datetime import datetime

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    make_asgi_app,
    start_http_server,
)

logger = logging.getLogger(__name__)

# Metrics namespace
METRICS_NAMESPACE = "digital_fte"

# HTTP Request Metrics
http_requests_total = Counter(
    f"{METRICS_NAMESPACE}_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
    namespace=METRICS_NAMESPACE,
)

http_request_duration_seconds = Histogram(
    f"{METRICS_NAMESPACE}_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    namespace=METRICS_NAMESPACE,
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

http_requests_in_progress = Gauge(
    f"{METRICS_NAMESPACE}_http_requests_in_progress",
    "HTTP requests currently in progress",
    ["method", "endpoint"],
    namespace=METRICS_NAMESPACE,
)

# Database Metrics
db_query_duration_seconds = Histogram(
    f"{METRICS_NAMESPACE}_db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
    namespace=METRICS_NAMESPACE,
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
)

db_pool_size = Gauge(
    f"{METRICS_NAMESPACE}_db_pool_size",
    "Database pool size",
    namespace=METRICS_NAMESPACE,
)

db_connections_active = Gauge(
    f"{METRICS_NAMESPACE}_db_connections_active",
    "Active database connections",
    namespace=METRICS_NAMESPACE,
)

# Kafka Metrics
kafka_messages_published_total = Counter(
    f"{METRICS_NAMESPACE}_kafka_messages_published_total",
    "Total Kafka messages published",
    ["topic"],
    namespace=METRICS_NAMESPACE,
)

kafka_messages_consumed_total = Counter(
    f"{METRICS_NAMESPACE}_kafka_messages_consumed_total",
    "Total Kafka messages consumed",
    ["topic"],
    namespace=METRICS_NAMESPACE,
)

kafka_consumer_lag = Gauge(
    f"{METRICS_NAMESPACE}_kafka_consumer_lag",
    "Kafka consumer lag (messages behind)",
    ["topic", "partition", "consumer_group"],
    namespace=METRICS_NAMESPACE,
)

# AI Agent Metrics
agent_requests_total = Counter(
    f"{METRICS_NAMESPACE}_agent_requests_total",
    "Total AI agent requests",
    ["model", "operation"],
    namespace=METRICS_NAMESPACE,
)

agent_response_duration_seconds = Histogram(
    f"{METRICS_NAMESPACE}_agent_response_duration_seconds",
    "AI agent response duration in seconds",
    ["model", "operation"],
    namespace=METRICS_NAMESPACE,
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

agent_confidence_histogram = Histogram(
    f"{METRICS_NAMESPACE}_agent_confidence_score",
    "AI agent confidence score distribution",
    ["model", "operation"],
    namespace=METRICS_NAMESPACE,
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)

agent_escalations_total = Counter(
    f"{METRICS_NAMESPACE}_agent_escalations_total",
    "Total agent escalations",
    ["reason"],
    namespace=METRICS_NAMESPACE,
)

# Business Metrics
tickets_created_total = Counter(
    f"{METRICS_NAMESPACE}_tickets_created_total",
    "Total tickets created",
    ["channel"],
    namespace=METRICS_NAMESPACE,
)

tickets_resolved_total = Counter(
    f"{METRICS_NAMESPACE}_tickets_resolved_total",
    "Total tickets resolved",
    ["resolution_type"],
    namespace=METRICS_NAMESPACE,
)

sentiment_records_total = Counter(
    f"{METRICS_NAMESPACE}_sentiment_records_total",
    "Total sentiment records",
    ["sentiment"],
    namespace=METRICS_NAMESPACE,
)

cross_channel_matches_total = Counter(
    f"{METRICS_NAMESPACE}_cross_channel_matches_total",
    "Total cross-channel customer identifications",
    ["status"],  # success, failure
    namespace=METRICS_NAMESPACE,
)

# System Metrics
system_info = Info(
    f"{METRICS_NAMESPACE}_build_info",
    "System information",
    namespace=METRICS_NAMESPACE,
)

system_info.info({
    "version": "1.0.0",
    "environment": "production",  # Will be dynamic
    "build_date": datetime.utcnow().isoformat(),
})


def track_http_request(
    method: str,
    endpoint: str,
):
    """
    Decorator to track HTTP request metrics.

    Args:
        method: HTTP method
        endpoint: Request endpoint

    Returns:
        Decorator function
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Track in-progress request
            http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

            start_time = time.time()
            status_code = 500  # Default to 500

            try:
                result = await func(*args, **kwargs)
                # Try to get status code from response
                if hasattr(result, "status_code"):
                    status_code = result.status_code

                return result

            except Exception as e:
                # Status already set to 500
                raise

            finally:
                duration = time.time() - start_time

                # Record request completed
                http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()

                # Record metrics
                http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=str(status_code),
                ).inc()

                http_request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint,
                ).observe(duration)

        return wrapper

    return decorator


def track_db_query(operation: str, table: str):
    """
    Decorator to track database query metrics.

    Args:
        operation: Query operation type
        table: Database table name

    Returns:
        Decorator function
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                return result

            finally:
                duration = time.time() - start_time
                db_query_duration_seconds.labels(
                    operation=operation,
                    table=table,
                ).observe(duration)

        return wrapper

    return decorator


def track_agent_request(model: str, operation: str):
    """
    Decorator to track AI agent request metrics.

    Args:
        model: AI model name
        operation: Agent operation type

    Returns:
        Decorator function
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                return result

            finally:
                duration = time.time() - start_time

                agent_requests_total.labels(model=model, operation=operation).inc()
                agent_response_duration_seconds.labels(model=model, operation=operation).observe(duration)

        return wrapper

    return decorator


def record_agent_confidence(model: str, operation: str, confidence: float) -> None:
    """
    Record AI agent confidence score.

    Args:
        model: AI model name
        operation: Agent operation type
        confidence: Confidence score (0-1)
    """
    agent_confidence_histogram.labels(model=model, operation=operation).observe(confidence)


def record_ticket_created(channel: str) -> None:
    """
    Record ticket creation.

    Args:
        channel: Channel identifier
    """
    tickets_created_total.labels(channel=channel).inc()


def record_ticket_resolved(resolution_type: str) -> None:
    """
    Record ticket resolution.

    Args:
        resolution_type: Type of resolution
    """
    tickets_resolved_total.labels(resolution_type=resolution_type).inc()


def record_sentiment(sentiment: str) -> None:
    """
    Record sentiment analysis.

    Args:
        sentiment: Sentiment classification
    """
    sentiment_records_total.labels(sentiment=sentiment).inc()


def record_cross_channel_match(status: str) -> None:
    """
    Record cross-channel customer identification.

    Args:
        status: Match status (success/failure)
    """
    cross_channel_matches_total.labels(status=status).inc()


def record_escalation(reason: str) -> None:
    """
    Record agent escalation.

    Args:
        reason: Escalation reason
    """
    agent_escalations_total.labels(reason=reason).inc()


def update_db_pool_stats(pool_stats: Dict[str, Any]) -> None:
    """
    Update database pool statistics.

    Args:
        pool_stats: Pool statistics from database
    """
    db_pool_size.set(pool_stats.get("pool_size", 0))
    db_connections_active.set(pool_stats.get("checked_out", 0))


# Create ASGI app for metrics exposure
metrics_app = make_asgi_app()


if __name__ == "__main__":
    # Start metrics server (for development)
    start_http_server(metrics_app, 8001)
    logger.info("Prometheus metrics server started on port 8001")
