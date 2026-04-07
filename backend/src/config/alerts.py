"""
Alert thresholds configuration for monitoring and alerting.

Defines thresholds for various metrics and provides
logic to determine if alerts should be triggered.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Types of alerts."""
    HIGH_ERROR_RATE = "high_error_rate"
    HIGH_LATENCY = "high_latency"
    LOW_SUCCESS_RATE = "low_success_rate"
    KAFKA_LAG = "kafka_lag"
    DATABASE_ISSUES = "database_issues"
    AI_FAILURES = "ai_failures"
    CROSS_CHANNEL_MATCH_FAILURE = "cross_channel_match_failure"
    COST_OVERRUN = "cost_overrun"


class AlertThresholds:
    """
    Alert threshold configuration.

    Defines thresholds for various metrics that trigger alerts.
    """

    # HTTP Error Rate thresholds
    ERROR_RATE_WARNING = 0.05  # 5% error rate
    ERROR_RATE_CRITICAL = 0.10  # 10% error rate
    ERROR_RATE_WINDOW_MINUTES = 5  # Rolling 5-minute window

    # HTTP Latency thresholds (in milliseconds)
    LATENCY_WARNING_P95 = 1000  # 1 second
    LATENCY_CRITICAL_P95 = 5000  # 5 seconds
    LATENCY_WARNING_P99 = 3000  # 3 seconds
    LATENCY_CRITICAL_P99 = 10000  # 10 seconds

    # Success Rate thresholds
    SUCCESS_RATE_WARNING = 0.95  # 95% success rate
    SUCCESS_RATE_CRITICAL = 0.90  # 90% success rate

    # Kafka Lag thresholds (number of messages behind)
    KAFKA_LAG_WARNING = 1000
    KAFKA_LAG_CRITICAL = 5000

    # Database Connection thresholds
    DB_CONNECTION_FAILURE_WARNING = 3  # 3 failures in 5 minutes
    DB_CONNECTION_FAILURE_CRITICAL = 5  # 5 failures in 5 minutes

    # AI Failure thresholds
    AI_FAILURE_RATE_WARNING = 0.10  # 10% failure rate
    AI_FAILURE_RATE_CRITICAL = 0.20  # 20% failure rate

    # Cross-Channel Match Failure thresholds
    CROSS_CHANNEL_FAILURE_WARNING = 0.05  # 5% match failure
    CROSS_CHANNEL_FAILURE_CRITICAL = 0.10  # 10% match failure

    # Cost thresholds
    MONTHLY_BUDGET_WARNING = 0.80  # 80% of monthly budget
    MONTHLY_BUDGET_CRITICAL = 0.95  # 95% of monthly budget
    MONTHLY_BUDGET_LIMIT = 1000  # $1000/year = ~$83/month

    # Alert suppression (prevent alert spam)
    ALERT_COOLDOWN_MINUTES = 30  # Minimum time between same alert


class AlertEvaluator:
    """
    Evaluator for checking thresholds and generating alerts.

    Evaluates metrics against thresholds and determines
    if alerts should be triggered.
    """

    def __init__(self):
        """Initialize alert evaluator."""
        self._last_alerts: Dict[str, datetime] = {}

    def should_suppress_alert(self, alert_key: str) -> bool:
        """
        Check if alert should be suppressed due to cooldown.

        Args:
            alert_key: Unique identifier for alert type

        Returns:
            True if should suppress, False otherwise
        """
        if alert_key not in self._last_alerts:
            return False

        last_alert = self._last_alerts[alert_key]
        cooldown = timedelta(minutes=AlertThresholds.ALERT_COOLDOWN_MINUTES)

        if datetime.utcnow() - last_alert < cooldown:
            return True

        return False

    def update_last_alert(self, alert_key: str) -> None:
        """
        Update last alert timestamp.

        Args:
            alert_key: Unique identifier for alert type
        """
        self._last_alerts[alert_key] = datetime.utcnow()

    def evaluate_http_error_rate(
        self,
        total_requests: int,
        error_count: int,
        window_minutes: int = AlertThresholds.ERROR_RATE_WINDOW_MINUTES,
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate HTTP error rate thresholds.

        Args:
            total_requests: Total requests in window
            error_count: Error requests in window
            window_minutes: Window duration

        Returns:
            Alert dictionary or None if no alert
        """
        if total_requests == 0:
            return None

        error_rate = error_count / total_requests
        alert_key = f"http_error_rate_{window_minutes}m"

        if self.should_suppress_alert(alert_key):
            return None

        severity = None
        if error_rate >= AlertThresholds.ERROR_RATE_CRITICAL:
            severity = AlertSeverity.CRITICAL
        elif error_rate >= AlertThresholds.ERROR_RATE_WARNING:
            severity = AlertSeverity.WARNING

        if severity:
            self.update_last_alert(alert_key)
            return {
                "type": AlertType.HIGH_ERROR_RATE,
                "severity": severity,
                "message": f"HTTP error rate {error_rate:.1%} exceeds threshold",
                "metric_value": error_rate,
                "threshold": AlertThresholds.ERROR_RATE_WARNING,
                "window_minutes": window_minutes,
                "timestamp": datetime.utcnow().isoformat(),
            }

        return None

    def evaluate_latency(
        self,
        p95_latency_ms: float,
        p99_latency_ms: float,
    ) -> List[Dict[str, Any]]:
        """
        Evaluate latency thresholds.

        Args:
            p95_latency_ms: 95th percentile latency in ms
            p99_latency_ms: 99th percentile latency in ms

        Returns:
            List of alert dictionaries (may be empty)
        """
        alerts = []

        # Check P95
        if p95_latency_ms >= AlertThresholds.LATENCY_CRITICAL_P95:
            if not self.should_suppress_alert("latency_p95_critical"):
                alerts.append({
                    "type": AlertType.HIGH_LATENCY,
                    "severity": AlertSeverity.CRITICAL,
                    "message": f"P95 latency {p95_latency_ms}ms exceeds critical threshold",
                    "metric_value": p95_latency_ms,
                    "threshold": AlertThresholds.LATENCY_CRITICAL_P95,
                    "percentile": "p95",
                    "timestamp": datetime.utcnow().isoformat(),
                })
                self.update_last_alert("latency_p95_critical")
        elif p95_latency_ms >= AlertThresholds.LATENCY_WARNING_P95:
            if not self.should_suppress_alert("latency_p95_warning"):
                alerts.append({
                    "type": AlertType.HIGH_LATENCY,
                    "severity": AlertSeverity.WARNING,
                    "message": f"P95 latency {p95_latency_ms}ms exceeds warning threshold",
                    "metric_value": p95_latency_ms,
                    "threshold": AlertThresholds.LATENCY_WARNING_P95,
                    "percentile": "p95",
                    "timestamp": datetime.utcnow().isoformat(),
                })
                self.update_last_alert("latency_p95_warning")

        # Check P99
        if p99_latency_ms >= AlertThresholds.LATENCY_CRITICAL_P99:
            if not self.should_suppress_alert("latency_p99_critical"):
                alerts.append({
                    "type": AlertType.HIGH_LATENCY,
                    "severity": AlertSeverity.CRITICAL,
                    "message": f"P99 latency {p99_latency_ms}ms exceeds critical threshold",
                    "metric_value": p99_latency_ms,
                    "threshold": AlertThresholds.LATENCY_CRITICAL_P99,
                    "percentile": "p99",
                    "timestamp": datetime.utcnow().isoformat(),
                })
                self.update_last_alert("latency_p99_critical")
        elif p99_latency_ms >= AlertThresholds.LATENCY_WARNING_P99:
            if not self.should_suppress_alert("latency_p99_warning"):
                alerts.append({
                    "type": AlertType.HIGH_LATENCY,
                    "severity": AlertSeverity.WARNING,
                    "message": f"P99 latency {p99_latency_ms}ms exceeds warning threshold",
                    "metric_value": p99_latency_ms,
                    "threshold": AlertThresholds.LATENCY_WARNING_P99,
                    "percentile": "p99",
                    "timestamp": datetime.utcnow().isoformat(),
                })
                self.update_last_alert("latency_p99_warning")

        return alerts

    def evaluate_kafka_lag(
        self,
        lag: int,
        topic: str,
        partition: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate Kafka consumer lag.

        Args:
            lag: Number of messages behind
            topic: Kafka topic name
            partition: Partition number

        Returns:
            Alert dictionary or None if no alert
        """
        alert_key = f"kafka_lag_{topic}_{partition}"

        if self.should_suppress_alert(alert_key):
            return None

        severity = None
        if lag >= AlertThresholds.KAFKA_LAG_CRITICAL:
            severity = AlertSeverity.CRITICAL
        elif lag >= AlertThresholds.KAFKA_LAG_WARNING:
            severity = AlertSeverity.WARNING

        if severity:
            self.update_last_alert(alert_key)
            return {
                "type": AlertType.KAFKA_LAG,
                "severity": severity,
                "message": f"Kafka lag {lag} messages on {topic}:{partition}",
                "metric_value": lag,
                "threshold": AlertThresholds.KAFKA_LAG_WARNING,
                "topic": topic,
                "partition": partition,
                "timestamp": datetime.utcnow().isoformat(),
            }

        return None

    def evaluate_database_health(
        self,
        is_healthy: bool,
        recent_failures: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate database health.

        Args:
            is_healthy: Whether database is currently healthy
            recent_failures: Number of recent connection failures

        Returns:
            Alert dictionary or None if no alert
        """
        alert_key = "database_health"

        if self.should_suppress_alert(alert_key):
            return None

        severity = None
        message = None

        if not is_healthy:
            severity = AlertSeverity.CRITICAL
            message = "Database is unhealthy"
        elif recent_failures >= AlertThresholds.DB_CONNECTION_FAILURE_CRITICAL:
            severity = AlertSeverity.CRITICAL
            message = f"Database has {recent_failures} recent failures (critical threshold)"
        elif recent_failures >= AlertThresholds.DB_CONNECTION_FAILURE_WARNING:
            severity = AlertSeverity.WARNING
            message = f"Database has {recent_failures} recent failures (warning threshold)"

        if severity:
            self.update_last_alert(alert_key)
            return {
                "type": AlertType.DATABASE_ISSUES,
                "severity": severity,
                "message": message,
                "is_healthy": is_healthy,
                "recent_failures": recent_failures,
                "warning_threshold": AlertThresholds.DB_CONNECTION_FAILURE_WARNING,
                "critical_threshold": AlertThresholds.DB_CONNECTION_FAILURE_CRITICAL,
                "timestamp": datetime.utcnow().isoformat(),
            }

        return None

    def evaluate_ai_failure_rate(
        self,
        total_requests: int,
        failure_count: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate AI agent failure rate.

        Args:
            total_requests: Total AI requests
            failure_count: Failed AI requests

        Returns:
            Alert dictionary or None if no alert
        """
        if total_requests == 0:
            return None

        failure_rate = failure_count / total_requests
        alert_key = "ai_failure_rate"

        if self.should_suppress_alert(alert_key):
            return None

        severity = None
        if failure_rate >= AlertThresholds.AI_FAILURE_RATE_CRITICAL:
            severity = AlertSeverity.CRITICAL
        elif failure_rate >= AlertThresholds.AI_FAILURE_RATE_WARNING:
            severity = AlertSeverity.WARNING

        if severity:
            self.update_last_alert(alert_key)
            return {
                "type": AlertType.AI_FAILURES,
                "severity": severity,
                "message": f"AI failure rate {failure_rate:.1%} exceeds threshold",
                "metric_value": failure_rate,
                "threshold": AlertThresholds.AI_FAILURE_RATE_WARNING,
                "total_requests": total_requests,
                "failure_count": failure_count,
                "timestamp": datetime.utcnow().isoformat(),
            }

        return None

    def evaluate_cross_channel_match(
        self,
        total_attempts: int,
        failure_count: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate cross-channel customer identification failure rate.

        Args:
            total_attempts: Total identification attempts
            failure_count: Failed attempts

        Returns:
            Alert dictionary or None if no alert
        """
        if total_attempts == 0:
            return None

        failure_rate = failure_count / total_attempts
        alert_key = "cross_channel_match_failure"

        if self.should_suppress_alert(alert_key):
            return None

        severity = None
        if failure_rate >= AlertThresholds.CROSS_CHANNEL_FAILURE_CRITICAL:
            severity = AlertSeverity.CRITICAL
        elif failure_rate >= AlertThresholds.CROSS_CHANNEL_FAILURE_WARNING:
            severity = AlertSeverity.WARNING

        if severity:
            self.update_last_alert(alert_key)
            return {
                "type": AlertType.CROSS_CHANNEL_MATCH_FAILURE,
                "severity": severity,
                "message": f"Cross-channel match failure rate {failure_rate:.1%} exceeds threshold",
                "metric_value": failure_rate,
                "threshold": AlertThresholds.CROSS_CHANNEL_FAILURE_WARNING,
                "constitution_requirement": "97%+ cross-channel identification accuracy",
                "timestamp": datetime.utcnow().isoformat(),
            }

        return None

    def evaluate_cost_overrun(
        self,
        monthly_spend: float,
        budget_limit: float = AlertThresholds.MONTHLY_BUDGET_LIMIT,
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate monthly cost overrun.

        Args:
            monthly_spend: Current monthly spend
            budget_limit: Monthly budget limit (default: ~$83)

        Returns:
            Alert dictionary or None if no alert
        """
        spend_ratio = monthly_spend / budget_limit
        alert_key = "cost_overrun"

        if self.should_suppress_alert(alert_key):
            return None

        severity = None
        if spend_ratio >= AlertThresholds.MONTHLY_BUDGET_CRITICAL:
            severity = AlertSeverity.CRITICAL
        elif spend_ratio >= AlertThresholds.MONTHLY_BUDGET_WARNING:
            severity = AlertSeverity.WARNING

        if severity:
            self.update_last_alert(alert_key)
            return {
                "type": AlertType.COST_OVERRUN,
                "severity": severity,
                "message": f"Monthly cost ${monthly_spend:.2f} is {spend_ratio:.1%} of budget",
                "metric_value": monthly_spend,
                "budget_limit": budget_limit,
                "spend_ratio": spend_ratio,
                "constitution_requirement": "$1000/year budget limit",
                "timestamp": datetime.utcnow().isoformat(),
            }

        return None

    def evaluate_all(
        self,
        metrics: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Evaluate all metrics and return any triggered alerts.

        Args:
            metrics: Dictionary of metric values

        Returns:
            List of alert dictionaries
        """
        alerts = []

        # HTTP metrics
        if "http_total_requests" in metrics and "http_error_count" in metrics:
            alert = self.evaluate_http_error_rate(
                total_requests=metrics["http_total_requests"],
                error_count=metrics["http_error_count"],
            )
            if alert:
                alerts.append(alert)

        # Latency metrics
        if "latency_p95_ms" in metrics and "latency_p99_ms" in metrics:
            alerts.extend(self.evaluate_latency(
                p95_latency_ms=metrics["latency_p95_ms"],
                p99_latency_ms=metrics["latency_p99_ms"],
            ))

        # Database metrics
        if "database_healthy" in metrics and "database_recent_failures" in metrics:
            alert = self.evaluate_database_health(
                is_healthy=metrics["database_healthy"],
                recent_failures=metrics["database_recent_failures"],
            )
            if alert:
                alerts.append(alert)

        # Kafka metrics
        if "kafka_lag" in metrics:
            for topic_partition, lag in metrics["kafka_lag"].items():
                topic, partition = topic_partition.split("_")
                alert = self.evaluate_kafka_lag(
                    lag=lag,
                    topic=topic,
                    partition=int(partition),
                )
                if alert:
                    alerts.append(alert)

        # AI metrics
        if "ai_total_requests" in metrics and "ai_failure_count" in metrics:
            alert = self.evaluate_ai_failure_rate(
                total_requests=metrics["ai_total_requests"],
                failure_count=metrics["ai_failure_count"],
            )
            if alert:
                alerts.append(alert)

        # Cross-channel metrics
        if "cross_channel_total_attempts" in metrics and "cross_channel_failures" in metrics:
            alert = self.evaluate_cross_channel_match(
                total_attempts=metrics["cross_channel_total_attempts"],
                failure_count=metrics["cross_channel_failures"],
            )
            if alert:
                alerts.append(alert)

        # Cost metrics
        if "monthly_spend" in metrics:
            alert = self.evaluate_cost_overrun(
                monthly_spend=metrics["monthly_spend"],
            )
            if alert:
                alerts.append(alert)

        return alerts


# Singleton evaluator instance
_evaluator: Optional[AlertEvaluator] = None


def get_alert_evaluator() -> AlertEvaluator:
    """
    Get or create singleton alert evaluator.

    Returns:
        AlertEvaluator instance
    """
    global _evaluator
    if _evaluator is None:
        _evaluator = AlertEvaluator()
    return _evaluator
