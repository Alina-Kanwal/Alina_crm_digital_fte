"""
Report trend analysis service for Digital FTE AI Customer Success Agent.
Analyzes report trends over time to identify patterns and improvements.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import func
from src.services.database import SessionLocal
from src.models.support_ticket import SupportTicket

logger = logging.getLogger(__name__)


class ReportTrendAnalyzer:
    """
    Service for analyzing report trends over time.

    Provides trend analysis to:
    - Identify improving/declining performance
    - Compare metrics across periods
    - Highlight areas requiring attention
    """

    def __init__(self):
        """Initialize report trend analyzer."""
        self.comparison_periods = 4  # Default comparison: 4 weeks
        logger.info("Report trend analyzer initialized")

    async def analyze_resolution_trends(
        self,
        weeks: int = 4
    ) -> Dict[str, Any]:
        """
        Analyze resolution rate trends over multiple weeks.

        Args:
            weeks: Number of weeks to analyze

        Returns:
            Dictionary containing resolution trend analysis
        """
        try:
            db = SessionLocal()

            trends = []

            for week in range(weeks):
                # Calculate week dates
                week_end = datetime.now() - timedelta(weeks=week)
                week_start = week_end - timedelta(weeks=1)

                # Get ticket stats for week
                total_tickets = db.query(SupportTicket).filter(
                    SupportTicket.created_at >= week_start,
                    SupportTicket.created_at < week_end
                ).count()

                resolved_tickets = db.query(SupportTicket).filter(
                    SupportTicket.created_at >= week_start,
                    SupportTicket.created_at < week_end,
                    SupportTicket.status == 'resolved'
                ).count()

                escalated_tickets = db.query(SupportTicket).filter(
                    SupportTicket.created_at >= week_start,
                    SupportTicket.created_at < week_end,
                    SupportTicket.status == 'escalated'
                ).count()

                resolution_rate = (resolved_tickets / total_tickets * 100) if total_tickets > 0 else 0
                escalation_rate = (escalated_tickets / total_tickets * 100) if total_tickets > 0 else 0

                trends.append({
                    'week': f"Week {weeks - week}",
                    'start': week_start.isoformat(),
                    'end': week_end.isoformat(),
                    'total_tickets': total_tickets,
                    'resolved_tickets': resolved_tickets,
                    'escalated_tickets': escalated_tickets,
                    'resolution_rate': resolution_rate,
                    'escalation_rate': escalation_rate
                })

            db.close()

            # Calculate overall trend
            if len(trends) >= 2:
                latest_rate = trends[0]['resolution_rate']
                previous_rate = trends[1]['resolution_rate']

                if latest_rate > previous_rate + 5:
                    trend_direction = 'declining'
                    severity = 'high'
                elif latest_rate < previous_rate - 5:
                    trend_direction = 'improving'
                    severity = 'low'
                else:
                    trend_direction = 'stable'
                    severity = 'medium'

                change = latest_rate - previous_rate
            else:
                trend_direction = 'insufficient_data'
                severity = 'unknown'
                change = 0

            logger.info(
                f"Resolution trends analyzed: {len(trends)} weeks, "
                f"trend={trend_direction}, change={change:.1f}%"
            )

            return {
                'success': True,
                'trends': trends,
                'trend_direction': trend_direction,
                'severity': severity,
                'change_from_previous': change,
                'latest_rate': trends[0]['resolution_rate'] if trends else 0
            }

        except Exception as e:
            logger.error(f"Error analyzing resolution trends: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def analyze_volume_trends(
        self,
        weeks: int = 4
    ) -> Dict[str, Any]:
        """
        Analyze ticket volume trends over multiple weeks.

        Args:
            weeks: Number of weeks to analyze

        Returns:
            Dictionary containing volume trend analysis
        """
        try:
            db = SessionLocal()

            trends = []

            for week in range(weeks):
                # Calculate week dates
                week_end = datetime.now() - timedelta(weeks=week)
                week_start = week_end - timedelta(weeks=1)

                # Get ticket count for week
                total_tickets = db.query(SupportTicket).filter(
                    SupportTicket.created_at >= week_start,
                    SupportTicket.created_at < week_end
                ).count()

                trends.append({
                    'week': f"Week {weeks - week}",
                    'start': week_start.isoformat(),
                    'end': week_end.isoformat(),
                    'ticket_volume': total_tickets
                })

            db.close()

            # Calculate overall trend
            if len(trends) >= 2:
                latest_volume = trends[0]['ticket_volume']
                previous_volume = trends[1]['ticket_volume']

                volume_change_pct = ((latest_volume - previous_volume) / previous_volume * 100) if previous_volume > 0 else 0

                if volume_change_pct > 20:
                    trend_direction = 'increasing'
                    severity = 'high'
                elif volume_change_pct < -20:
                    trend_direction = 'decreasing'
                    severity = 'medium'  # Could be concern
                else:
                    trend_direction = 'stable'
                    severity = 'low'

            else:
                trend_direction = 'insufficient_data'
                severity = 'unknown'
                volume_change_pct = 0

            logger.info(
                f"Volume trends analyzed: {len(trends)} weeks, "
                f"trend={trend_direction}, change={volume_change_pct:.1f}%"
            )

            return {
                'success': True,
                'trends': trends,
                'trend_direction': trend_direction,
                'severity': severity,
                'volume_change_percentage': volume_change_pct,
                'latest_volume': trends[0]['ticket_volume'] if trends else 0
            }

        except Exception as e:
            logger.error(f"Error analyzing volume trends: {e}")
            return {
                'success': False,
                'error': str(e)
            }
