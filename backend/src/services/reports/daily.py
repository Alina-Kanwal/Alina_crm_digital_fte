"""
Daily report generation service for Digital FTE AI Customer Success Agent.
Generates comprehensive daily sentiment and performance reports.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from src.database.connection import SessionLocal
from src.models.sentiment_record import SentimentRecord
from src.models.support_ticket import SupportTicket
from src.models.message import Message

logger = logging.getLogger(__name__)


class DailyReportGenerator:
    """
    Service for generating daily support reports.

    Per Constitution Principle XV:
    "System MUST generate daily sentiment reports ... delivered to support managers by 9:00 AM"
    """

    def __init__(self):
        """Initialize daily report generator."""
        self.target_delivery_time = "09:00"  # 9:00 AM local time
        logger.info("Daily report generator initialized")

    async def generate_daily_report(
        self,
        report_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive daily support report.

        Args:
            report_date: Optional date for report (default: yesterday)

        Returns:
            Dictionary containing full daily report
        """
        try:
            # Set default report date to yesterday
            if not report_date:
                report_date = datetime.now() - timedelta(days=1)

            # Calculate date range (full day)
            day_start = report_date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)

            # Generate report sections
            sentiment_summary = await self._generate_sentiment_summary(day_start, day_end)
            ticket_summary = await self._generate_ticket_summary(day_start, day_end)
            top_complaints = await self._identify_top_complaints(day_start, day_end)
            channel_performance = await self._analyze_channel_performance(day_start, day_end)
            trend_analysis = await self._perform_trend_analysis(day_start, day_end)

            # Build comprehensive report
            report = {
                'report_date': report_date.isoformat(),
                'report_type': 'daily_sentiment_and_performance',
                'target_delivery_time': self.target_delivery_time,
                'generated_at': datetime.now().isoformat(),
                'sentiment_summary': sentiment_summary,
                'ticket_summary': ticket_summary,
                'top_complaints': top_complaints,
                'channel_performance': channel_performance,
                'trend_analysis': trend_analysis,
                'recommendations': await self._generate_recommendations(
                    sentiment_summary,
                    ticket_summary,
                    top_complaints
                )
            }

            logger.info(
                f"Daily report generated for {report_date.date()}: "
                f"{ticket_summary['total_tickets']} tickets processed"
            )

            return report

        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
            return {
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }

    async def _generate_sentiment_summary(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Generate sentiment summary for the report period.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary containing sentiment summary statistics
        """
        try:
            db = SessionLocal()

            # Get sentiment counts
            sentiment_counts = db.query(
                SentimentRecord.sentiment,
                func.count(SentimentRecord.id).label('count')
            ).filter(
                SentimentRecord.analyzed_at >= start_date,
                SentimentRecord.analyzed_at < end_date
            ).group_by(
                SentimentRecord.sentiment
            ).all()

            db.close()

            # Build summary
            positive_count = 0
            neutral_count = 0
            negative_count = 0
            positive_confidence = 0.0
            negative_confidence = 0.0

            for sentiment, count in sentiment_counts:
                if sentiment == 'positive':
                    positive_count = count
                elif sentiment == 'neutral':
                    neutral_count = count
                elif sentiment == 'negative':
                    negative_count = count

            total = positive_count + neutral_count + negative_count

            # Calculate percentages
            if total > 0:
                positive_pct = (positive_count / total) * 100
                neutral_pct = (neutral_count / total) * 100
                negative_pct = (negative_count / total) * 100
            else:
                positive_pct = neutral_pct = negative_pct = 0.0

            return {
                'total_analyzed': total,
                'positive_count': positive_count,
                'positive_percentage': positive_pct,
                'neutral_count': neutral_count,
                'neutral_percentage': neutral_pct,
                'negative_count': negative_count,
                'negative_percentage': negative_pct,
                'net_sentiment': 'positive' if positive_pct > negative_pct else 'negative' if negative_pct > positive_pct else 'neutral'
            }

        except Exception as e:
            logger.error(f"Error generating sentiment summary: {e}")
            return {'error': str(e)}

    async def _generate_ticket_summary(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Generate ticket summary for the report period.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary containing ticket summary statistics
        """
        try:
            db = SessionLocal()

            # Get ticket counts by status
            status_counts = db.query(
                SupportTicket.status,
                func.count(SupportTicket.id).label('count')
            ).filter(
                SupportTicket.created_at >= start_date,
                SupportTicket.created_at < end_date
            ).group_by(
                SupportTicket.status
            ).all()

            db.close()

            # Build summary
            total_tickets = sum(count for _, count in status_counts)
            open_count = sum(count for status, count in status_counts if status == 'open')
            resolved_count = sum(count for status, count in status_counts if status == 'resolved')
            escalated_count = sum(count for status, count in status_counts if status == 'escalated')

            return {
                'total_tickets': total_tickets,
                'open_count': open_count,
                'resolved_count': resolved_count,
                'escalated_count': escalated_count,
                'resolution_rate': (resolved_count / total_tickets * 100) if total_tickets > 0 else 0.0,
                'escalation_rate': (escalated_count / total_tickets * 100) if total_tickets > 0 else 0.0,
                'status_breakdown': {status: count for status, count in status_counts}
            }

        except Exception as e:
            logger.error(f"Error generating ticket summary: {e}")
            return {'error': str(e)}

    async def _identify_top_complaints(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Identify top customer complaints for the report period.

        Args:
            start_date: Start date
            end_date: End date
            limit: Maximum number of complaints to return

        Returns:
            List of top complaint topics
        """
        try:
            db = SessionLocal()

            # Fetch recent negative messages directly (no join to SupportTicket needed)
            negative_messages = db.query(Message).join(
                SentimentRecord,
                Message.ticket_id == SentimentRecord.ticket_id,
                isouter=True
            ).filter(
                SentimentRecord.sentiment == 'negative',
                SentimentRecord.analyzed_at >= start_date,
                SentimentRecord.analyzed_at < end_date
            ).order_by(
                SentimentRecord.analyzed_at.desc()
            ).limit(limit * 3).all()

            db.close()

            # Aggregate by topic
            complaint_topics = {}
            for msg in negative_messages:
                content = msg.content or ""
                keywords = self._extract_complaint_keywords(content)

                for keyword in keywords:
                    complaint_topics[keyword] = complaint_topics.get(keyword, 0) + 1

            # Sort by frequency and get top complaints
            top_complaints = sorted(
                complaint_topics.items(),
                key=lambda x: x[1],
                reverse=True
            )[:limit]

            results = [
                {'complaint': topic, 'count': count}
                for topic, count in top_complaints
            ]

            logger.info(
                f"Identified {len(results)} top complaints for period"
            )

            return results

        except Exception as e:
            logger.error(f"Error identifying top complaints: {e}")
            return []

    def _extract_complaint_keywords(self, content: str) -> List[str]:
        """
        Extract complaint keywords from message content.

        Args:
            content: Message or ticket content

        Returns:
            List of complaint keywords
        """
        content_lower = content.lower()

        # Common complaint keywords
        complaint_keywords = [
            'not working', 'broken', 'error', 'bug',
            'slow', 'crash', 'timeout', 'fail',
            'integration', 'authentication', 'login',
            'feature request', 'missing', 'documentation',
            'pricing', 'billing', 'support'
        ]

        found_keywords = []
        for keyword in complaint_keywords:
            if keyword in content_lower:
                found_keywords.append(keyword)

        return found_keywords

    async def _analyze_channel_performance(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Analyze performance by communication channel.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary containing channel performance metrics
        """
        try:
            db = SessionLocal()

            # Query tickets grouped by channel and sentiment (SentimentRecord has ticket_id)
            channel_sentiment = db.query(
                SupportTicket.channel,
                SentimentRecord.sentiment,
                func.count(SentimentRecord.id).label('count')
            ).join(
                SentimentRecord,
                SupportTicket.id == SentimentRecord.ticket_id
            ).filter(
                SentimentRecord.analyzed_at >= start_date,
                SentimentRecord.analyzed_at < end_date
            ).group_by(
                SupportTicket.channel,
                SentimentRecord.sentiment
            ).all()

            db.close()

            # Build channel performance summary
            channel_performance = {}

            for channel, sentiment, count in channel_sentiment:
                if channel not in channel_performance:
                    channel_performance[channel] = {
                        'total': 0,
                        'positive': 0,
                        'neutral': 0,
                        'negative': 0
                    }

                channel_performance[channel]['total'] += count
                channel_performance[channel][sentiment] += count

            # Calculate sentiment percentages per channel
            for channel, metrics in channel_performance.items():
                total = metrics['total']
                if total > 0:
                    metrics['positive_percentage'] = (metrics['positive'] / total) * 100
                    metrics['neutral_percentage'] = (metrics['neutral'] / total) * 100
                    metrics['negative_percentage'] = (metrics['negative'] / total) * 100
                else:
                    metrics['positive_percentage'] = 0.0
                    metrics['neutral_percentage'] = 0.0
                    metrics['negative_percentage'] = 0.0

            return channel_performance

        except Exception as e:
            logger.error(f"Error analyzing channel performance: {e}")
            return {'error': str(e)}

    async def _perform_trend_analysis(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Perform trend analysis comparing to previous period.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary containing trend analysis
        """
        try:
            # Get current period stats
            current_start = start_date
            current_end = end_date

            # Get previous period (same day range, 7 days ago)
            period_length = (current_end - current_start).days
            previous_start = current_start - timedelta(days=period_length)
            previous_end = current_start

            # Get sentiment for both periods
            current_stats = await self._generate_sentiment_summary(current_start, current_end)
            previous_stats = await self._generate_sentiment_summary(previous_start, previous_end)

            # Compare sentiment trends
            current_negative_pct = current_stats.get('negative_percentage', 0)
            previous_negative_pct = previous_stats.get('negative_percentage', 0)

            sentiment_trend = 'stable'
            if current_negative_pct > previous_negative_pct + 5:
                sentiment_trend = 'declining'
            elif current_negative_pct < previous_negative_pct - 5:
                sentiment_trend = 'improving'

            return {
                'current_period': {
                    'start': current_start.isoformat(),
                    'end': current_end.isoformat(),
                    'negative_percentage': current_negative_pct
                },
                'previous_period': {
                    'start': previous_start.isoformat(),
                    'end': previous_end.isoformat(),
                    'negative_percentage': previous_negative_pct
                },
                'sentiment_trend': sentiment_trend,
                'change_percentage': current_negative_pct - previous_negative_pct
            }

        except Exception as e:
            logger.error(f"Error performing trend analysis: {e}")
            return {'error': str(e)}

    async def _generate_recommendations(
        self,
        sentiment_summary: Dict[str, Any],
        ticket_summary: Dict[str, Any],
        top_complaints: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate recommendations based on report data.

        Args:
            sentiment_summary: Sentiment summary statistics
            ticket_summary: Ticket summary statistics
            top_complaints: List of top complaints

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Check escalation rate
        escalation_rate = ticket_summary.get('escalation_rate', 0)
        if escalation_rate > 20:
            recommendations.append(
                f"⚠️ Escalation rate ({escalation_rate:.1f}%) exceeds 20% target. "
                f"Review AI responses and knowledge base coverage."
            )

        # Check sentiment trends
        negative_pct = sentiment_summary.get('negative_percentage', 0)
        if negative_pct > 30:
            recommendations.append(
                f"⚠️ High negative sentiment ({negative_pct:.1f}%). "
                f"Review common complaints and agent responses."
            )

        # Check top complaints
        if len(top_complaints) > 0:
            top_complaint = top_complaints[0]['complaint']
            top_count = top_complaints[0]['count']
            if top_count > 5:
                recommendations.append(
                    f"📈 Most common complaint: '{top_complaint}' ({top_count} occurrences). "
                    f"Consider addressing this issue proactively."
                )

        return recommendations if recommendations else ["✅ All metrics within acceptable ranges"]
