"""
Sentiment storage and retrieval service for Digital FTE AI Customer Success Agent.
Stores and retrieves sentiment analysis results in PostgreSQL.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_
from src.services.database import SessionLocal
from src.models.message import Message
from src.models.sentiment_record import SentimentRecord

logger = logging.getLogger(__name__)


class SentimentStorage:
    """
    Service for storing and retrieving sentiment data.

    Per Constitution Principle XV:
    "System MUST analyze customer sentiment in every interaction and store results in PostgreSQL"
    """

    def __init__(self):
        """Initialize sentiment storage service."""
        self.retention_days = 90  # Keep sentiment data for 90 days
        logger.info("Sentiment storage service initialized")

    async def store_sentiment(
        self,
        message_id: int,
        sentiment_result: Dict[str, Any],
        customer_id: Optional[int] = None
    ) -> bool:
        """
        Store sentiment analysis result for a message.

        Args:
            message_id: The message ID
            sentiment_result: Sentiment analysis result dictionary
            customer_id: Optional customer ID

        Returns:
            True if successfully stored
        """
        try:
            db = SessionLocal()

            # Create sentiment record
            sentiment_record = SentimentRecord(
                message_id=message_id,
                sentiment=sentiment_result.get('sentiment', 'neutral'),
                confidence=float(sentiment_result.get('confidence', 0.5)),
                reasoning=sentiment_result.get('reasoning'),
                keywords=sentiment_result.get('keywords', []),
                emotion=sentiment_result.get('emotion'),
                analyzed_at=datetime.now()
            )

            db.add(sentiment_record)
            db.commit()

            logger.info(
                f"Sentiment stored: message_id={message_id}, "
                f"sentiment={sentiment_record.sentiment}"
            )

            return True

        except Exception as e:
            logger.error(f"Error storing sentiment: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    async def get_message_sentiment(
        self,
        message_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve sentiment analysis for a specific message.

        Args:
            message_id: The message ID

        Returns:
            Dictionary containing sentiment data or None
        """
        try:
            db = SessionLocal()

            record = db.query(SentimentRecord).filter(
                SentimentRecord.message_id == message_id
            ).first()

            db.close()

            if not record:
                return None

            return {
                'id': record.id,
                'message_id': record.message_id,
                'sentiment': record.sentiment,
                'confidence': record.confidence,
                'reasoning': record.reasoning,
                'keywords': record.keywords,
                'emotion': record.emotion,
                'analyzed_at': record.analyzed_at.isoformat() if record.analyzed_at else None
            }

        except Exception as e:
            logger.error(f"Error retrieving message sentiment: {e}")
            return None

    async def get_customer_sentiment_history(
        self,
        customer_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get sentiment history for a customer.

        Args:
            customer_id: The customer ID
            limit: Maximum number of records to return

        Returns:
            List of sentiment analysis results
        """
        try:
            db = SessionLocal()

            # Get recent sentiment records for customer
            records = db.query(SentimentRecord).join(
                Message,
                SentimentRecord.message_id == Message.id
            ).join(
                'support_tickets',
                Message.thread_id == 'support_tickets.id'
            ).filter(
                'support_tickets.customer_id' == customer_id
            ).order_by(
                SentimentRecord.analyzed_at.desc()
            ).limit(limit).all()

            db.close()

            results = []
            for record in records:
                results.append({
                    'id': record.id,
                    'message_id': record.message_id,
                    'sentiment': record.sentiment,
                    'confidence': record.confidence,
                    'reasoning': record.reasoning,
                    'keywords': record.keywords,
                    'emotion': record.emotion,
                    'analyzed_at': record.analyzed_at.isoformat() if record.analyzed_at else None
                })

            logger.info(
                f"Retrieved {len(results)} sentiment records for customer {customer_id}"
            )

            return results

        except Exception as e:
            logger.error(f"Error getting customer sentiment history: {e}")
            return []

    async def get_sentiment_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get sentiment statistics for a time period.

        Args:
            start_date: Start date for statistics
            end_date: End date for statistics

        Returns:
            Dictionary containing sentiment statistics
        """
        try:
            db = SessionLocal()

            # Set default date range (last 24 hours)
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(hours=24)

            # Get sentiment counts
            sentiment_counts = db.query(
                SentimentRecord.sentiment,
                func.count(SentimentRecord.id).label('count')
            ).filter(
                SentimentRecord.analyzed_at >= start_date,
                SentimentRecord.analyzed_at <= end_date
            ).group_by(
                SentimentRecord.sentiment
            ).all()

            db.close()

            # Build statistics
            stats = {
                'total_analyzed': sum(count for _, count in sentiment_counts),
                'positive_count': 0,
                'neutral_count': 0,
                'negative_count': 0,
                'positive_percentage': 0.0,
                'neutral_percentage': 0.0,
                'negative_percentage': 0.0
            }

            for sentiment, count in sentiment_counts:
                stats[f'{sentiment}_count'] = count

            total = stats['total_analyzed']
            if total > 0:
                stats['positive_percentage'] = (stats['positive_count'] / total) * 100
                stats['neutral_percentage'] = (stats['neutral_count'] / total) * 100
                stats['negative_percentage'] = (stats['negative_count'] / total) * 100

            # Calculate average confidence
            avg_confidence = db.query(func.avg(SentimentRecord.confidence)).filter(
                SentimentRecord.analyzed_at >= start_date,
                SentimentRecord.analyzed_at <= end_date
            ).scalar()

            stats['average_confidence'] = float(avg_confidence) if avg_confidence else 0.0

            logger.info(
                f"Sentiment statistics: total={total}, "
                f"positive={stats['positive_percentage']:.1f}%, "
                f"negative={stats['negative_percentage']:.1f}%"
            )

            return stats

        except Exception as e:
            logger.error(f"Error getting sentiment statistics: {e}")
            return {
                'error': str(e),
                'total_analyzed': 0
            }

    async def cleanup_old_sentiment_data(self) -> int:
        """
        Clean up old sentiment records.

        Returns:
            Number of records cleaned up
        """
        try:
            db = SessionLocal()

            cutoff_date = datetime.now() - timedelta(days=self.retention_days)

            # Delete old records
            deleted_count = db.query(SentimentRecord).filter(
                SentimentRecord.analyzed_at < cutoff_date
            ).delete()

            db.commit()
            db.close()

            logger.info(f"Cleaned up {deleted_count} old sentiment records")

            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old sentiment data: {e}")
            db.rollback()
            return 0
