"""
Escalation rate monitoring and alerting service.
Monitors escalation rates and triggers alerts when thresholds are exceeded.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from src.services.escalation.tracker import EscalationTracker

logger = logging.getLogger(__name__)


class EscalationMonitor:
    """
    Service for monitoring escalation rates and generating alerts.

    Alert thresholds:
    - WARNING: Escalation rate > 20% (target exceeded)
    - CRITICAL: Escalation rate > 25% (alert threshold)
    """

    def __init__(self):
        """Initialize escalation monitor."""
        self.tracker = EscalationTracker()
        self.warning_threshold = self.tracker.target_rate  # 20%
        self.critical_threshold = 0.25  # 25%

        # Alert history to prevent spam
        self.alert_history = {}
        self.alert_cooldown_minutes = 60  # Minimum time between similar alerts

        logger.info(
            f"Escalation monitor initialized: "
            f"warning={self.warning_threshold*100}%, "
            f"critical={self.critical_threshold*100}%"
        )

    async def check_and_alert(
        self,
        escalation_rate_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Check escalation rate and generate alerts if needed.

        Args:
            escalation_rate_data: Optional pre-calculated escalation rate data

        Returns:
            Dictionary containing alert status and details
        """
        try:
            # Get escalation rate if not provided
            if not escalation_rate_data:
                escalation_rate_data = await self.tracker.calculate_escalation_rate()

            if not escalation_rate_data['success']:
                return {
                    'success': False,
                    'error': 'Failed to calculate escalation rate'
                }

            escalation_rate = escalation_rate_data['escalation_rate']
            escalation_percentage = escalation_rate_data['escalation_percentage']

            # Determine alert level
            alert_level = None
            alert_message = None

            if escalation_rate > self.critical_threshold:
                alert_level = 'CRITICAL'
                alert_message = (
                    f"CRITICAL: Escalation rate ({escalation_percentage:.1f}%) "
                    f"exceeds critical threshold ({self.critical_threshold*100}%). "
                    f"Immediate attention required."
                )
            elif escalation_rate > self.warning_threshold:
                alert_level = 'WARNING'
                alert_message = (
                    f"WARNING: Escalation rate ({escalation_percentage:.1f}%) "
                    f"exceeds target ({self.warning_threshold*100}%). "
                    f"Review escalation patterns."
                )
            else:
                # No alert needed
                return {
                    'success': True,
                    'alert_triggered': False,
                    'escalation_rate': escalation_rate,
                    'escalation_percentage': escalation_percentage
                }

            # Check if this alert was recently sent (avoid spam)
            alert_key = f"{alert_level}_{escalation_percentage:.0f}"
            last_alert_time = self.alert_history.get(alert_key)

            if last_alert_time:
                time_since_last_alert = datetime.now() - last_alert_time
                if time_since_last_alert.total_seconds() < (self.alert_cooldown_minutes * 60):
                    logger.info(f"Alert cooldown active for {alert_key}")
                    return {
                        'success': True,
                        'alert_triggered': True,
                        'alert_level': alert_level,
                        'status': 'cooldown',
                        'escalation_rate': escalation_rate,
                        'escalation_percentage': escalation_percentage
                    }

            # Send alert
            await self._send_alert(alert_level, alert_message, escalation_rate_data)

            # Record alert in history
            self.alert_history[alert_key] = datetime.now()

            logger.warning(f"Escalation alert triggered: {alert_level}")

            return {
                'success': True,
                'alert_triggered': True,
                'alert_level': alert_level,
                'alert_message': alert_message,
                'escalation_rate': escalation_rate,
                'escalation_percentage': escalation_percentage
            }

        except Exception as e:
            logger.error(f"Error checking and alerting: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _send_alert(
        self,
        alert_level: str,
        message: str,
        context: Dict[str, Any]
    ) -> Dict[str, bool]:
        """
        Send escalation alert to configured channels.

        Args:
            alert_level: Alert level (WARNING, CRITICAL)
            message: Alert message
            context: Context information

        Returns:
            Dictionary with send status
        """
        try:
            # In production, would integrate with notification services
            # For now, just log with level
            if alert_level == 'CRITICAL':
                logger.critical(message)
            elif alert_level == 'WARNING':
                logger.warning(message)

            # Would also send to:
            # - Slack/Teams notifications
            # - Email alerts
            # - PagerDuty/OpsGenie for critical
            # - Dashboard updates

            return {
                'success': True,
                'alert_level': alert_level,
                'sent_at': datetime.now().isoformat(),
                'channels': ['log']  # Would include email, slack, etc.
            }

        except Exception as e:
            logger.error(f"Error sending alert: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def generate_escalation_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive escalation monitoring report.

        Returns:
            Dictionary containing full report
        """
        try:
            # Get current metrics
            current_rate = await self.tracker.calculate_escalation_rate()

            # Get trends
            trends = await self.tracker.get_escalation_trends(periods=7)

            # Get current alert status
            alert_status = await self.check_and_alert(current_rate)

            # Build report
            report = {
                'generated_at': datetime.now().isoformat(),
                'summary': {
                    'current_rate': current_rate.get('escalation_percentage', 0),
                    'target_met': current_rate.get('target_met', False),
                    'target_percentage': current_rate.get('target_percentage', 20),
                    'gap_percentage': current_rate.get('gap_percentage', 0),
                    'alert_status': alert_status.get('alert_triggered', False),
                    'alert_level': alert_status.get('alert_level', None)
                },
                'current_metrics': current_rate,
                'trends': trends,
                'alert_status': alert_status,
                'recommendations': self._generate_recommendations(
                    current_rate,
                    trends,
                    alert_status
                )
            }

            logger.info("Escalation monitoring report generated")

            return report

        except Exception as e:
            logger.error(f"Error generating escalation report: {e}")
            return {
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }

    def _generate_recommendations(
        self,
        current_rate: Dict[str, Any],
        trends: Dict[str, Any],
        alert_status: Dict[str, Any]
    ) -> List[str]:
        """
        Generate recommendations based on escalation metrics.

        Args:
            current_rate: Current escalation rate data
            trends: Trend data
            alert_status: Alert status

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Check if target is not met
        if not current_rate.get('target_met', False):
            gap = current_rate.get('gap_percentage', 0)
            recommendations.append(
                f"⚠️ CRITICAL: Escalation rate ({current_rate.get('escalation_percentage', 0):.1f}%) "
                f"is above target ({current_rate.get('target_percentage', 20)}%). "
                f"Gap: {gap:.1f} percentage points."
            )

        # Check trend
        if trends.get('trend_direction') == 'declining':
            recommendations.append(
                "📉 Trend: Escalation rate is increasing. "
                "Investigate AI agent responses and knowledge base coverage."
            )
        elif trends.get('trend_direction') == 'improving':
            recommendations.append(
                "📈 Trend: Escalation rate is improving. "
                "Continue current approach."
            )

        # Check alert status
        if alert_status.get('alert_triggered', False):
            alert_level = alert_status.get('alert_level', '')
            recommendations.append(
                f"🚨 Alert: {alert_level} level escalation alert triggered. "
                f"Review escalation patterns and agent responses."
            )

        return recommendations if recommendations else ["✅ All escalation metrics within targets"]
