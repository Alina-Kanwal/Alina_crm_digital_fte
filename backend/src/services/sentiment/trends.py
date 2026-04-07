"""
Sentiment trend analysis service for Digital FTE AI Customer Success Agent.
Analyzes sentiment trends over time to identify patterns.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from src.services.database import SessionLocal
from src.models.sentiment_record import SentimentRecord

logger = logging.getLogger(__name__)


class SentimentTrendAnalyzer:
    """
    Service for analyzing sentiment trends over time.

    Provides trend analysis to:
    - Identify improving/declining patterns
    - Detect anomalies or sudden changes
    - Compare periods for performance assessment
    """

    def __init__(self):
        """Initialize sentiment trend analyzer."""
        self.comparison_periods = 7  # Default comparison period: 7 days
        logger.info("Sentiment trend analyzer initialized")

    async def analyze_sentiment_trends(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        periods: int = 4
    ) -> Dict[str, Any]:
        """
        Analyze sentiment trends over multiple time periods.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            periods: Number of periods to analyze

        Returns:
            Dictionary containing trend analysis
        """
        try:
            db = SessionLocal()

            # Set default end date to now
            if not end_date:
                end_date = datetime.now()

            # Set default start date to 4 weeks ago
            if not start_date:
                start_date = end_date - timedelta(weeks=4)

            # Analyze trends by period
            trends = []

            for period in range(periods):
                # Calculate period dates
                period_end = end_date - timedelta(weeks=period)
                period_start = period_end - timedelta(weeks=1)

                # Get sentiment data for period
                sentiment_counts = db.query(
                    SentimentRecord.sentiment,
                    func.count(SentimentRecord.id).label('count')
                ).filter(
                    SentimentRecord.analyzed_at >= period_start,
                    SentimentRecord.analyzed_at < period_end
                ).group_by(
                    SentimentRecord.sentiment
                ).all()

                # Build period summary
                total = sum(count for _, count in sentiment_counts)
                negative_count = sum(count for sentiment, count in sentiment_counts if sentiment == 'negative')
                negative_pct = (negative_count / total * 100) if total > 0 else 0

                trends.append({
                    'period': f"Period {periods - period}",
                    'start': period_start.isoformat(),
                    'end': period_end.isoformat(),
                    'total_analyzed': total,
                    'negative_count': negative_count,
                    'negative_percentage': negative_pct
                })

            db.close()

            # Calculate overall trend
            if len(trends) >= 2:
                latest_pct = trends[0]['negative_percentage']
                previous_pct = trends[1]['negative_percentage']

                if latest_pct > previous_pct + 5:
                    trend_direction = 'declining'
                    severity = 'high'
                elif latest_pct < previous_pct - 5:
                    trend_direction = 'improving'
                    severity = 'low'
                else:
                    trend_direction = 'stable'
                    severity = 'medium'

                change = latest_pct - previous_pct
            else:
                trend_direction = 'insufficient_data'
                severity = 'unknown'
                change = 0

            logger.info(
                f"Sentiment trends analyzed: {len(trends)} periods, "
                f"trend={trend_direction}, change={change:.1f}%"
            )

            return {
                'success': True,
                'trends': trends,
                'trend_direction': trend_direction,
                'severity': severity,
                'change_from_previous': change,
                'analysis_period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Error analyzing sentiment trends: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def detect_sentiment_anomalies(
        self,
        window_days: int = 1,
        threshold_std_dev: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in sentiment data.

        Args:
            window_days: Rolling window size in days
            threshold_std_dev: Standard deviation threshold for anomaly detection

        Returns:
            List of detected anomalies
        """
        try:
            db = SessionLocal()

            # Get recent sentiment data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=window_days)

            # Get sentiment records with sentiment scores
            records = db.query(SentimentRecord).filter(
                SentimentRecord.analyzed_at >= start_date,
                SentimentRecord.analyzed_at < end_date
            ).all()

            db.close()

            if not records:
                return []

            # Calculate mean and standard deviation of sentiment confidence
            confidences = [record.confidence for record in records]
            if len(confidences) == 0:
                return []

            import statistics
            mean_conf = statistics.mean(confidences)
            std_conf = statistics.stdev(confidences) if len(confidences) > 1 else 0

            anomalies = []

            for record in records:
                # Check if confidence is anomalous (too low or too high)
                z_score = abs((record.confidence - mean_conf) / std_conf)) if std_conf > 0 else 0

                if z_score > threshold_std_dev:
                    anomalies.append({
                        'record_id': record.id,
                        'analyzed_at': record.analyzed_at.isoformat() if record.analyzed_at else None,
                        'sentiment': record.sentiment,
                        'confidence': record.confidence,
                        'z_score': z_score,
                        'type': 'low_confidence' if record.confidence < mean_conf else 'high_confidence' if record.confidence > mean_conf else 'unknown'
                    })

            logger.info(f"Detected {len(anomalies)} sentiment anomalies")

            return anomalies

        except Exception as e:
            logger.error(f"Error detecting sentiment anomalies: {e}")
            return []

    async def compare_period_sentiment(
        self,
        period1_start: datetime,
        period1_end: datetime,
        period2_start: datetime,
        period2_end: datetime
    ) -> Dict[str, Any]:
        """
        Compare sentiment between two time periods.

        Args:
            period1_start: Start of first period
            period1_end: End of first period
            period2_start: Start of second period
            period2_end: End of second period

        Returns:
            Dictionary with comparison results
        """
        try:
            db = SessionLocal()

            # Get sentiment counts for period 1
            p1_counts = db.query(
                SentimentRecord.sentiment,
                func.count(SentimentRecord.id).label('count')
            ).filter(
                SentimentRecord.analyzed_at >= period1_start,
                SentimentRecord.analyzed_at < period1_end
            ).group_by(
                SentimentRecord.sentiment
            ).all()

            # Get sentiment counts for period 2
            p2_counts = db.query(
                SentimentRecord.sentiment,
                func.count(SentimentRecord.id).label('count')
            ).filter(
                SentimentRecord.analyzed_at >= period2_start,
                SentimentRecord.analyzed_at < period2_end
            ).group_by(
                SentimentRecord.sentiment
            ).all()

            db.close()

            # Calculate statistics for each period
            p1_total = sum(count for _, count in p1_counts)
            p1_negative = sum(count for sentiment, count in p1_counts if sentiment == 'negative')
            p1_negative_pct = (p1_negative / p1_total * 100) if p1_total > 0 else 0

            p2_total = sum(count for _, count in p2_counts)
            p2_negative = sum(count for sentiment, count in p2_counts if sentiment == 'negative')
            p2_negative_pct = (p2_negative / p2_total * 100) if p2_total > 0 else 0

            # Compare periods
            change = p2_negative_pct - p1_negative_pct
            improvement = change < 0  # Negative change is improvement

            return {
                'period1': {
                    'start': period1_start.isoformat(),
                    'end': period1_end.isoformat(),
                    'total': p1_total,
                    'negative_percentage': p1_negative_pct
                },
                'period2': {
                    'start': period2_start.isoformat(),
                    'end': period2_end.isoformat(),
                    'total': p2_total,
                    'negative_percentage': p2_negative_pct
                },
                'comparison': {
                    'change_percentage': change,
                    'improvement': improvement,
                    'trend': 'improving' if improvement else 'declining' if change > 5 else 'stable'
                }
            }

        except Exception as e:
            logger.error(f"Error comparing period sentiment: {e}")
            return {'error': str(e)}
