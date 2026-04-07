"""
Escalation tracking and metrics collection service.
Tracks escalation rates, patterns, and performance.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from src.services.database import SessionLocal
from src.models.support_ticket import SupportTicket

logger = logging.getLogger(__name__)


class EscalationTracker:
    """
    Service for tracking escalations and collecting metrics.

    Per Constitution Principle XII:
    Target escalation rate: <20% of total interactions
    """

    def __init__(self):
        """Initialize escalation tracker."""
        self.target_rate = 0.20  # 20% maximum escalation rate
        self.alert_threshold = 0.25  # Alert if rate exceeds 25%
        logger.info(f"Escalation tracker initialized: target_rate={self.target_rate*100}%")

    async def calculate_escalation_rate(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Calculate escalation rate for a given time period.

        Args:
            start_date: Start date for calculation
            end_date: End date for calculation
            db: Optional database session (for testing)

        Returns:
            Dictionary containing escalation rate metrics
        """
        try:
            # Use provided session or create new one
            if db is None:
                db = SessionLocal()
                should_close = True
            else:
                should_close = False

            # Set default date range (last 24 hours)
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(hours=24)

            # Get total tickets in period
            total_tickets = db.query(SupportTicket).filter(
                SupportTicket.created_at >= start_date,
                SupportTicket.created_at <= end_date
            ).count()

            # Get escalated tickets in period
            escalated_tickets = db.query(SupportTicket).filter(
                SupportTicket.created_at >= start_date,
                SupportTicket.created_at <= end_date,
                SupportTicket.status == 'escalated'
            ).count()

            # Only close db session if we created it
            if should_close:
                db.close()

            # Calculate escalation rate
            escalation_rate = (escalated_tickets / total_tickets) if total_tickets > 0 else 0.0

            # Determine if target is met
            target_met = escalation_rate <= self.target_rate
            alert_triggered = escalation_rate > self.alert_threshold

            logger.info(
                f"Escalation rate calculated: {escalation_rate*100:.2f}% "
                f"({escalated_tickets}/{total_tickets} escalated), "
                f"target_met={target_met}"
            )

            return {
                'success': True,
                'escalation_rate': escalation_rate,
                'escalation_percentage': escalation_rate * 100,
                'total_tickets': total_tickets,
                'escalated_tickets': escalated_tickets,
                'target_met': target_met,
                'target_percentage': self.target_rate * 100,
                'gap_percentage': (escalation_rate - self.target_rate) * 100,
                'alert_triggered': alert_triggered,
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Error calculating escalation rate: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def track_escalation(
        self,
        escalation_data: Dict[str, Any]
    ) -> bool:
        """
        Track an escalation event for metrics collection.

        Args:
            escalation_data: Dictionary containing escalation details

        Returns:
            True if successfully tracked
        """
        try:
            db = SessionLocal()

            # Create or update escalated ticket
            ticket_id = escalation_data.get('ticket_id')

            if ticket_id:
                ticket = db.query(SupportTicket).filter(
                    SupportTicket.id == ticket_id
                ).first()

                if ticket:
                    ticket.status = 'escalated'
                    ticket.assigned_to = escalation_data.get('assigned_to')
                    ticket.priority = escalation_data.get('priority', 2)  # High priority by default
                    ticket.updated_at = datetime.now()

                    db.commit()

                    logger.info(
                        f"Escalation tracked: ticket_id={ticket_id}, "
                        f"trigger={escalation_data.get('trigger')}, "
                        f"reason={escalation_data.get('reason')}"
                    )

                    return True

            db.close()
            return False

        except Exception as e:
            logger.error(f"Error tracking escalation: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    async def get_escalation_trends(
        self,
        periods: int = 7
    ) -> Dict[str, Any]:
        """
        Get escalation trends over multiple time periods.

        Args:
            periods: Number of periods to analyze (default: 7 days)

        Returns:
            Dictionary containing trend data
        """
        try:
            trends = []

            for i in range(periods):
                # Calculate period end date (going backwards)
                period_end = datetime.now() - timedelta(days=i)
                period_start = period_end - timedelta(days=1)

                # Get escalation rate for this period
                rate_data = await self.calculate_escalation_rate(
                    start_date=period_start,
                    end_date=period_end
                )

                if rate_data['success']:
                    trends.append({
                        'period': f"Day {periods - i}",
                        'start': period_start.isoformat(),
                        'end': period_end.isoformat(),
                        'escalation_rate': rate_data['escalation_rate'],
                        'escalation_percentage': rate_data['escalation_percentage'],
                        'target_met': rate_data['target_met']
                    })

            # Calculate trend direction
            if len(trends) >= 2:
                latest = trends[0]['escalation_rate']
                previous = trends[1]['escalation_rate']
                trend = 'improving' if latest < previous else 'declining' if latest > previous else 'stable'
                change = latest - previous
            else:
                trend = 'insufficient_data'
                change = 0.0

            return {
                'success': True,
                'trends': trends,
                'trend_direction': trend,
                'latest_rate': trends[0]['escalation_rate'] if trends else 0.0,
                'latest_percentage': trends[0]['escalation_percentage'] if trends else 0.0,
                'change_from_previous': change
            }

        except Exception as e:
            logger.error(f"Error getting escalation trends: {e}")
            return {
                'success': False,
                'error': str(e)
            }
