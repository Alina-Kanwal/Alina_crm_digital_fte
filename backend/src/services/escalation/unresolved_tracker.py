"""
Repeated unresolved query tracker for Digital FTE AI Customer Success Agent.
Tracks customer issues that haven't been resolved after multiple interactions.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import and_, desc
from src.database.connection import SessionLocal
from src.models.support_ticket import SupportTicket
from src.models.message import Message

logger = logging.getLogger(__name__)


class UnresolvedTracker:
    """
    Service for tracking repeated unresolved customer queries.

    Per Constitution Principle XII:
    "Escalation triggers after 3 interactions on the same topic
    without resolution OR when customer expresses dissatisfaction in
    2 consecutive interactions"
    """

    def __init__(self):
        """Initialize unresolved query tracker."""
        self.repeated_threshold = 3  # Escalate after 3 attempts
        self.time_window_days = 7  # Consider interactions within 7 days
        logger.info(
            f"Unresolved tracker initialized: "
            f"threshold={self.repeated_threshold}, "
            f"window={self.time_window_days} days"
        )

    async def check_repeated_unresolved(
        self,
        customer_id: int,
        topic: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Check if a customer has repeated unresolved queries.

        Args:
            customer_id: The customer ID
            topic: Optional topic to filter by

        Returns:
            Dictionary containing:
            - is_repeated: Boolean indicating if repeated unresolved detected
            - count: Number of interactions on same topic
            - threshold: Threshold for escalation
            - details: Additional context
        """
        try:
            db = SessionLocal()

            # Get recent interactions in time window
            window_start = datetime.now() - timedelta(days=self.time_window_days)

            # Count unresolved interactions
            if topic:
                # Filter by specific topic
                interactions = db.query(Message).join(
                    SupportTicket,
                    Message.thread_id == SupportTicket.id
                ).filter(
                    SupportTicket.customer_id == customer_id,
                    SupportTicket.status.in_(['open', 'in_progress']),
                    SupportTicket.created_at >= window_start,
                    SupportTicket.title.ilike(f'%{topic}%')
                ).all()
            else:
                # Count all unresolved interactions
                interactions = db.query(Message).join(
                    SupportTicket,
                    Message.thread_id == SupportTicket.id
                ).filter(
                    SupportTicket.customer_id == customer_id,
                    SupportTicket.status.in_(['open', 'in_progress']),
                    SupportTicket.created_at >= window_start
                ).all()

            db.close()

            interaction_count = len(interactions)
            is_repeated = interaction_count >= self.repeated_threshold

            if is_repeated:
                logger.warning(
                    f"Repeated unresolved detected: customer_id={customer_id}, "
                    f"interactions={interaction_count}, threshold={self.repeated_threshold}"
                )

            return {
                'is_repeated': is_repeated,
                'count': interaction_count,
                'threshold': self.repeated_threshold,
                'details': {
                    'time_window_days': self.time_window_days,
                    'topic': topic,
                    'window_start': window_start.isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Error checking repeated unresolved: {e}")
            return {
                'is_repeated': False,
                'count': 0,
                'threshold': self.repeated_threshold,
                'error': str(e)
            }

    async def track_issue_resolution(
        self,
        ticket_id: int,
        resolved: bool = True,
        resolution_notes: Optional[str] = None
    ) -> bool:
        """
        Track when an issue is resolved to reset repeated counter.

        Args:
            ticket_id: The support ticket ID
            resolved: Whether the issue was resolved
            resolution_notes: Optional resolution notes

        Returns:
            True if successful
        """
        try:
            db = SessionLocal()

            ticket = db.query(SupportTicket).filter(
                SupportTicket.id == ticket_id
            ).first()

            if ticket:
                ticket.status = 'resolved' if resolved else 'closed'
                ticket.resolved_at = datetime.now()
                if resolution_notes:
                    ticket.resolution_summary = resolution_notes

                db.commit()

                logger.info(
                    f"Issue resolution tracked: ticket_id={ticket_id}, "
                    f"resolved={resolved}"
                )
                return True

            db.close()
            return False

        except Exception as e:
            logger.error(f"Error tracking issue resolution: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    async def get_customers_with_repeated_issues(
        self,
        limit: int = 20
    ) -> List[Dict[str, any]]:
        """
        Get list of customers with repeated unresolved issues.

        Args:
            limit: Maximum number of customers to return

        Returns:
            List of customer dictionaries with repeated issue information
        """
        try:
            db = SessionLocal()

            window_start = datetime.now() - timedelta(days=self.time_window_days)

            # Get customers with >= threshold unresolved interactions
            # This is a simplified query - in production would use topic clustering
            subquery = db.query(
                SupportTicket.customer_id,
                func.count(SupportTicket.id).label('ticket_count')
            ).filter(
                SupportTicket.status.in_(['open', 'in_progress']),
                SupportTicket.created_at >= window_start
            ).group_by(
                SupportTicket.customer_id
            ).having(
                func.count(SupportTicket.id) >= self.repeated_threshold
            ).subquery()

            customers = db.query(SupportTicket).join(
                subquery,
                SupportTicket.customer_id == subquery.c.customer_id
            ).limit(limit).all()

            db.close()

            results = []
            for ticket in customers:
                results.append({
                    'customer_id': ticket.customer_id,
                    'ticket_count': ticket.ticket_count,
                    'status': ticket.status,
                    'created_at': ticket.created_at.isoformat() if ticket.created_at else None
                })

            if len(results) > 0:
                logger.info(f"Found {len(results)} customers with repeated unresolved issues")

            return results

        except Exception as e:
            logger.error(f"Error getting customers with repeated issues: {e}")
            return []

    async def generate_repeated_issues_report(self) -> Dict[str, any]:
        """
        Generate report of customers with repeated unresolved issues.

        Returns:
            Dictionary containing report data
        """
        try:
            customers = await self.get_customers_with_repeated_issues()

            return {
                'generated_at': datetime.now().isoformat(),
                'threshold': self.repeated_threshold,
                'time_window_days': self.time_window_days,
                'customers_with_repeated_issues': len(customers),
                'customer_details': customers,
                'recommendation': (
                    f"Consider reviewing {len(customers)} customers with "
                    f"{self.repeated_threshold}+ unresolved interactions"
                )
            }

        except Exception as e:
            logger.error(f"Error generating repeated issues report: {e}")
            return {
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }
