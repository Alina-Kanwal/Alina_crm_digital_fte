"""
Human agent notification system for Digital FTE AI Customer Success Agent.
Notifies human support agents when escalations occur.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from src.database.connection import SessionLocal
from src.models.support_ticket import SupportTicket
from src.models.customer import Customer
from src.models.conversation_thread import ConversationThread

logger = logging.getLogger(__name__)


class HumanAgentNotifier:
    """
    Service for notifying human agents of escalations.

    Provides context to human agents including:
    - Full conversation history
    - Escalation reason and trigger
    - Customer information
    - Ticket priority and assignment
    """

    def __init__(self):
        """Initialize human agent notifier."""
        self.notification_methods = ['email', 'slack', 'dashboard']
        logger.info("Human agent notifier initialized")

    async def notify_escalation(
        self,
        escalation_data: Dict[str, Any],
        notification_methods: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Notify human agents of an escalation.

        Args:
            escalation_data: Dictionary containing escalation details
            notification_methods: List of notification methods (default: all)

        Returns:
            Dictionary containing notification status for each method
        """
        try:
            if notification_methods is None:
                notification_methods = self.notification_methods

            # Get conversation context
            context = await self._get_escalation_context(escalation_data)

            # Build notification payload
            notification = {
                'escalation_id': escalation_data.get('escalation_id'),
                'customer_id': escalation_data.get('customer_id'),
                'trigger': escalation_data.get('trigger'),
                'severity': escalation_data.get('severity'),
                'reason': escalation_data.get('reason'),
                'message': escalation_data.get('message'),
                'conversation_history': context.get('history', []),
                'customer_info': context.get('customer', {}),
                'priority': self._calculate_priority(escalation_data),
                'assigned_to': escalation_data.get('assigned_to'),
                'created_at': datetime.now().isoformat()
            }

            # Send notifications through each method
            results = {}

            for method in notification_methods:
                if method == 'email':
                    results['email'] = await self._send_email_notification(notification)
                elif method == 'slack':
                    results['slack'] = await self._send_slack_notification(notification)
                elif method == 'dashboard':
                    results['dashboard'] = await self._update_dashboard(notification)

            # Log notification
            success_count = sum(1 for r in results.values() if r.get('success', False))

            logger.info(
                f"Escalation notification sent: escalation_id={escalation_data.get('escalation_id')}, "
                f"methods={notification_methods}, success={success_count}/{len(notification_methods)}"
            )

            return {
                'success': success_count > 0,
                'escalation_id': escalation_data.get('escalation_id'),
                'notification_results': results,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error notifying escalation: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def _get_escalation_context(
        self,
        escalation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get conversation context for escalation notification.

        Args:
            escalation_data: Escalation details

        Returns:
            Dictionary containing context information
        """
        try:
            db = SessionLocal()

            context = {'history': [], 'customer': {}}

            # Get customer information
            customer_id = escalation_data.get('customer_id')
            if customer_id:
                customer = db.query(Customer).filter(
                    Customer.id == customer_id
                ).first()

                if customer:
                    context['customer'] = {
                        'id': customer.id,
                        'email': customer.email,
                        'phone': customer.phone,
                        'name': customer.name
                    }

            # Get conversation history
            thread_id = escalation_data.get('thread_id')
            if thread_id:
                # This would retrieve messages from the conversation thread
                # For now, just mark as having history
                context['history'] = [
                    {
                        'direction': 'incoming',
                        'content': escalation_data.get('message', ''),
                        'timestamp': datetime.now().isoformat()
                    }
                ]

            db.close()
            return context

        except Exception as e:
            logger.error(f"Error getting escalation context: {e}")
            return {'history': [], 'customer': {}}

    def _calculate_priority(
        self,
        escalation_data: Dict[str, Any]
    ) -> int:
        """
        Calculate ticket priority based on escalation severity.

        Args:
            escalation_data: Escalation details

        Returns:
            Priority level (1=critical, 2=high, 3=medium, 4=low)
        """
        severity = escalation_data.get('severity', 'low').lower()

        if severity == 'critical':
            return 1  # Profanity, legal matters
        elif severity == 'high':
            return 2  # Refunds, repeated issues
        elif severity == 'medium':
            return 3  # Pricing, negative sentiment
        else:
            return 4  # Low priority

    async def _send_email_notification(
        self,
        notification: Dict[str, Any]
    ) -> Dict[str, bool]:
        """
        Send email notification to human agents.

        Args:
            notification: Notification payload

        Returns:
            Dictionary with success status and details
        """
        try:
            # In production, this would integrate with email service
            # For now, just log
            logger.info(
                f"Email notification would be sent: "
                f"escalation_id={notification['escalation_id']}, "
                f"priority={notification['priority']}, "
                f"reason={notification['reason']}"
            )

            return {
                'success': True,
                'method': 'email',
                'recipient': 'support-team@example.com',  # Would be configured
                'subject': f"Escalation: {notification['escalation_id']}",
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return {
                'success': False,
                'method': 'email',
                'error': str(e)
            }

    async def _send_slack_notification(
        self,
        notification: Dict[str, Any]
    ) -> Dict[str, bool]:
        """
        Send Slack notification to human agents.

        Args:
            notification: Notification payload

        Returns:
            Dictionary with success status and details
        """
        try:
            # In production, this would integrate with Slack API
            # For now, just log
            logger.info(
                f"Slack notification would be sent: "
                f"escalation_id={notification['escalation_id']}, "
                f"priority={notification['priority']}"
            )

            return {
                'success': True,
                'method': 'slack',
                'channel': '#support-escalations',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            return {
                'success': False,
                'method': 'slack',
                'error': str(e)
            }

    async def _update_dashboard(
        self,
        notification: Dict[str, Any]
    ) -> Dict[str, bool]:
        """
        Update support dashboard with escalation.

        Args:
            notification: Notification payload

        Returns:
            Dictionary with success status and details
        """
        try:
            # In production, this would update dashboard/API
            # For now, just log
            logger.info(
                f"Dashboard updated with escalation: "
                f"escalation_id={notification['escalation_id']}, "
                f"assigned_to={notification.get('assigned_to')}"
            )

            return {
                'success': True,
                'method': 'dashboard',
                'ticket_id': notification['escalation_id'],
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
            return {
                'success': False,
                'method': 'dashboard',
                'error': str(e)
            }
