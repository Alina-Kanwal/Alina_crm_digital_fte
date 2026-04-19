"""
Customer identification accuracy monitoring and reporting service.
Tracks cross-channel customer identification accuracy to ensure 97%+ target is met.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from src.database.connection import SessionLocal
from src.models.customer import Customer
from src.models.message import Message
from src.models.conversation_thread import ConversationThread

logger = logging.getLogger(__name__)


class IdentificationMonitor:
    """Service for monitoring and reporting customer identification accuracy."""

    def __init__(self):
        """Initialize identification monitor."""
        self.accuracy_target = 0.97  # 97% target per Constitution Principle XI
        self.min_sample_size = 100  # Minimum interactions for reliable accuracy
        self.window_days = 7  # Rolling window for accuracy calculation
        logger.info(f"Identification monitor initialized (target: {self.accuracy_target*100}%)")

    async def calculate_identification_accuracy(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Calculate cross-channel customer identification accuracy.

        Args:
            start_date: Start date for calculation (default: 7 days ago)
            end_date: End date for calculation (default: now)
            db: Optional database session (for testing)

        Returns:
            Dictionary containing accuracy metrics
        """
        try:
            # Use provided session or create new one
            if db is None:
                db = SessionLocal()
                should_close = True
            else:
                should_close = False

            # Set default date range
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=self.window_days)

            # Get all customer interactions in the date range
            interactions = db.query(
                Message.content,
                Message.channel,
                Message.sentiment,
                ConversationThread.customer_id
            ).join(
                ConversationThread,
                Message.thread_id == ConversationThread.id
            ).filter(
                Message.timestamp >= start_date,
                Message.timestamp <= end_date,
                ConversationThread.customer_id.isnot(None)
            ).all()

            # Only close db session if we created it
            if should_close:
                db.close()

            if not interactions or len(interactions) < self.min_sample_size:
                logger.warning(
                    f"Insufficient sample size for accuracy calculation: "
                    f"{len(interactions) if interactions else 0} < {self.min_sample_size}"
                )
                return {
                    'success': False,
                    'reason': 'Insufficient sample size',
                    'sample_size': len(interactions) if interactions else 0,
                    'required_size': self.min_sample_size
                }

            # Count unique customers with multi-channel interactions
            customer_channels = {}  # customer_id -> set of channels

            for interaction in interactions:
                customer_id = interaction.customer_id
                channel = interaction.channel

                if customer_id not in customer_channels:
                    customer_channels[customer_id] = set()
                customer_channels[customer_id].add(channel)

            # Count multi-channel customers
            multi_channel_customers = 0
            for customer_id, channels in customer_channels.items():
                if len(channels) > 1:
                    multi_channel_customers += 1

            # Calculate accuracy
            total_customers = len(customer_channels)
            accuracy = multi_channel_customers / total_customers if total_customers > 0 else 0.0

            # Calculate channel distribution
            channel_counts = {}
            for customer_id, channels in customer_channels.items():
                for channel in channels:
                    channel_counts[channel] = channel_counts.get(channel, 0) + 1

            # Determine if target met
            target_met = accuracy >= self.accuracy_target

            logger.info(
                f"Identification accuracy calculated: {accuracy*100:.2f}% "
                f"({multi_channel_customers}/{total_customers} multi-channel customers) "
                f"Target met: {target_met}"
            )

            return {
                'success': True,
                'accuracy': accuracy,
                'accuracy_percentage': accuracy * 100,
                'multi_channel_customers': multi_channel_customers,
                'total_customers': total_customers,
                'target_met': target_met,
                'target': self.accuracy_target,
                'target_percentage': self.accuracy_target * 100,
                'gap': accuracy - self.accuracy_target,
                'channel_distribution': channel_counts,
                'sample_size': len(interactions),
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Error calculating identification accuracy: {e}")
            return {
                'success': False,
                'reason': f"Calculation error: {str(e)}"
            }

    async def get_identification_trends(
        self,
        periods: int = 4,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Get identification accuracy trends over multiple periods.

        Args:
            periods: Number of periods to analyze (default: 4 weeks)

        Returns:
            Dictionary containing trend data
        """
        try:
            trends = []

            for i in range(periods):
                # Calculate period end date (going backwards)
                period_end = datetime.now() - timedelta(weeks=i)
                period_start = period_end - timedelta(weeks=1)

                # Get accuracy for this period
                accuracy_data = await self.calculate_identification_accuracy(
                    start_date=period_start,
                    end_date=period_end,
                    db=db
                )

                if accuracy_data['success']:
                    trends.append({
                        'period': f"Week {periods - i}",
                        'start': period_start.isoformat(),
                        'end': period_end.isoformat(),
                        'accuracy': accuracy_data['accuracy'],
                        'accuracy_percentage': accuracy_data['accuracy_percentage'],
                        'target_met': accuracy_data['target_met'],
                        'multi_channel_customers': accuracy_data['multi_channel_customers'],
                        'total_customers': accuracy_data['total_customers']
                    })

            # Calculate trend direction
            if len(trends) >= 2:
                latest = trends[0]['accuracy']
                previous = trends[1]['accuracy']
                trend = 'improving' if latest > previous else 'declining' if latest < previous else 'stable'
                change = latest - previous
            else:
                trend = 'insufficient_data'
                change = 0.0

            return {
                'success': True,
                'trends': trends,
                'trend_direction': trend,
                'latest_accuracy': trends[0]['accuracy'] if trends else 0.0,
                'latest_accuracy_percentage': trends[0]['accuracy_percentage'] if trends else 0.0,
                'change_from_previous_period': change,
                'target_met': trends[0]['target_met'] if trends else False
            }

        except Exception as e:
            logger.error(f"Error getting identification trends: {e}")
            return {
                'success': False,
                'reason': f"Trend analysis error: {str(e)}"
            }

    async def get_low_identification_customers(
        self,
        limit: int = 20,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """
        Identify customers with poor cross-channel identification.

        Args:
            limit: Maximum number of customers to return

        Returns:
            List of customers with identification issues
        """
        try:
            # Use provided session or create new one
            if db is None:
                db = SessionLocal()
                should_close = True
            else:
                should_close = False

            # Get customers with only one channel interaction in recent period
            recent_date = datetime.now() - timedelta(days=self.window_days)

            # Count channels per customer
            customer_channel_count = db.query(
                Customer.id,
                func.count(Message.channel).distinct().label('channel_count')
            ).join(
                ConversationThread,
                Customer.id == ConversationThread.customer_id
            ).join(
                Message,
                ConversationThread.id == Message.thread_id
            ).filter(
                Message.timestamp >= recent_date
            ).group_by(
                Customer.id
            ).all()

            db.close()

            # Identify customers with only 1 channel (poor identification)
            low_identification = []

            for customer_id, channel_count in customer_channel_count:
                if channel_count == 1:
                    # Get customer details
                    customer = db.query(Customer).filter(Customer.id == customer_id).first()
                    if customer:
                        # Get the single channel used
                        messages = db.query(Message).join(
                            ConversationThread,
                            Message.thread_id == ConversationThread.id
                        ).filter(
                            ConversationThread.customer_id == customer_id,
                            Message.timestamp >= recent_date
                        ).all()

                        channels_used = list(set(msg.channel for msg in messages))

                        low_identification.append({
                            'customer_id': customer_id,
                            'email': customer.email,
                            'phone': customer.phone,
                            'channels_used': channels_used,
                            'channel_count': channel_count,
                            'message_count': len(messages),
                            'last_interaction': max(msg.timestamp for msg in messages).isoformat() if messages else None
                        })

                        if len(low_identification) >= limit:
                            break

            if should_close:
                db.close()

            logger.info(f"Found {len(low_identification)} customers with low cross-channel identification")

            return low_identification

        except Exception as e:
            logger.error(f"Error identifying low identification customers: {e}")
            return []

    async def generate_identification_report(self, db: Optional[Session] = None) -> Dict[str, Any]:
        """
        Generate comprehensive identification accuracy report.

        Returns:
            Dictionary containing full report
        """
        try:
            # Get current accuracy
            current_accuracy = await self.calculate_identification_accuracy(db=db)

            # Get trends
            trends = await self.get_identification_trends(db=db)

            # Get low identification customers
            low_id_customers = await self.get_low_identification_customers(db=db)

            # Build report
            report = {
                'generated_at': datetime.now().isoformat(),
                'summary': {
                    'current_accuracy': current_accuracy.get('accuracy_percentage', 0),
                    'target_met': current_accuracy.get('target_met', False),
                    'target_percentage': current_accuracy.get('target_percentage', 97),
                    'gap_percentage': (current_accuracy.get('accuracy', 0) - 0.97) * 100,
                },
                'current_accuracy': current_accuracy,
                'trends': trends,
                'low_identification_customers': low_id_customers,
                'recommendations': self._generate_recommendations(
                    current_accuracy,
                    trends,
                    low_id_customers
                )
            }

            logger.info("Identification accuracy report generated")

            return report

        except Exception as e:
            logger.error(f"Error generating identification report: {e}")
            return {
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }

    def _generate_recommendations(
        self,
        current_accuracy: Dict[str, Any],
        trends: Dict[str, Any],
        low_id_customers: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate recommendations based on identification metrics.

        Args:
            current_accuracy: Current accuracy data
            trends: Trend data
            low_id_customers: Customers with poor identification

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Check if target is not met
        if not current_accuracy.get('target_met', False):
            gap = current_accuracy.get('gap', 0)
            recommendations.append(
                f"⚠️ CRITICAL: Cross-channel identification accuracy ({current_accuracy.get('accuracy_percentage', 0):.1f}%) "
                f"is below target ({current_accuracy.get('target_percentage', 97)}%). "
                f"Gap: {gap*100:.1f} percentage points."
            )

        # Check trend
        if trends.get('trend_direction') == 'declining':
            recommendations.append(
                "📉 Trend: Identification accuracy is declining. "
                "Investigate recent changes to embedding or matching algorithms."
            )
        elif trends.get('trend_direction') == 'improving':
            recommendations.append(
                "📈 Trend: Identification accuracy is improving. "
                "Continue current approach."
            )

        # Check low identification customers
        if len(low_id_customers) > 10:
            recommendations.append(
                f"⚠️ {len(low_id_customers)} customers have only single-channel interactions. "
                "Consider requesting email/phone confirmation during conversations."
            )

        # Channel balance recommendations
        if current_accuracy.get('success'):
            channel_dist = current_accuracy.get('channel_distribution', {})
            if len(channel_dist) < 3:
                missing_channels = set(['email', 'whatsapp', 'webform']) - set(channel_dist.keys())
                recommendations.append(
                    f"ℹ️ Some channels have low usage: {', '.join(missing_channels)}. "
                    "Consider customer outreach to encourage multi-channel usage."
                )

        return recommendations if recommendations else ["✅ All identification metrics within targets"]

    async def log_identification_event(
        self,
        customer_id: int,
        channel: str,
        identified_as: Optional[int] = None,
        confidence: Optional[float] = None,
        method: str = 'embedding'
    ):
        """
        Log a customer identification event for tracking and analysis.

        Args:
            customer_id: The identified customer ID
            channel: The channel where identification occurred
            identified_as: If different, the customer ID this was identified as
            confidence: Confidence score of the identification
            method: Identification method (embedding, fuzzy, manual)
        """
        try:
            # This would log to an identification_events table
            # For now, just log to application logs
            logger.info(
                f"Identification event | "
                f"customer_id={customer_id}, "
                f"channel={channel}, "
                f"identified_as={identified_as if identified_as else 'self'}, "
                f"confidence={confidence:.2f if confidence else 'N/A'}, "
                f"method={method}"
            )

        except Exception as e:
            logger.error(f"Error logging identification event: {e}")
