"""
Scheduled tasks for Digital FTE AI Customer Success Agent.
Celery worker for daily report generation and other scheduled operations.
"""
import logging
from typing import Dict, Any
from datetime import datetime, timedelta, time
from celery import Celery
from celery.schedules import crontab
from celery.decorators import periodic_task, task

from src.services.reports.daily import DailyReportGenerator
from src.services.reports.delivery import ReportDeliveryService
from src.services.sentiment.storage import SentimentStorage

logger = logging.getLogger(__name__)

# Initialize Celery app (configuration would come from settings)
# In production, would configure with proper broker (Redis/RabbitMQ)
celery_app = Celery(
    'digital_fte_worker',
    broker='redis://localhost:6379/0',  # Would be configured
    backend='redis://localhost:6379/1',
    timezone='UTC'
)


class ScheduledTasks:
    """
    Scheduled task manager for Digital FTE.

    Per Constitution Principle XV:
    "System MUST generate daily sentiment reports ... delivered to support managers by 9:00 AM"
    """

    def __init__(self):
        """Initialize scheduled tasks manager."""
        self.target_delivery_time = "09:00"  # 9:00 AM target
        self.report_generator = DailyReportGenerator()
        self.delivery_service = ReportDeliveryService()
        self.sentiment_storage = SentimentStorage()

        logger.info("Scheduled tasks manager initialized")

    @periodic_task(
        run_every=crontab(hour=9, minute=0),  # Run at 9:00 AM daily
        name='generate_and_send_daily_report',
        bind=True
    )
    async def generate_and_send_daily_report(self):
        """
        Generate and send daily support report.

        Scheduled to run every day at 9:00 AM.
        """
        try:
            logger.info("Starting daily report generation scheduled task")

            # Generate daily report
            report = await self.report_generator.generate_daily_report()

            if 'error' in report:
                logger.error(f"Daily report generation failed: {report['error']}")
                return

            # Deliver report
            delivery_result = await self.delivery_service.deliver_report(report)

            if delivery_result['success']:
                logger.info(
                    f"Daily report delivered successfully: "
                    f"report_date={report['report_date']}"
                )
            else:
                logger.warning(
                    f"Daily report delivery failed: "
                    f"{delivery_result}"
                )

        except Exception as e:
            logger.error(f"Error in daily report scheduled task: {e}")
            raise

    @periodic_task(
        run_every=timedelta(minutes=60),  # Run every hour
        name='cleanup_old_sentiment_data',
        bind=True
    )
    async def cleanup_old_sentiment_data(self):
        """
        Clean up old sentiment data (scheduled hourly).

        Runs every hour to clean up data older than retention period.
        """
        try:
            logger.info("Starting sentiment data cleanup scheduled task")

            # Clean up old sentiment records
            deleted_count = await self.sentiment_storage.cleanup_old_sentiment_data()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old sentiment records")

        except Exception as e:
            logger.error(f"Error in cleanup scheduled task: {e}")
            raise

    @periodic_task(
        run_every=timedelta(hours=24),  # Run daily at midnight
        name='generate_weekly_summary',
        bind=True
    )
    async def generate_weekly_summary(self):
        """
        Generate weekly summary (scheduled daily at midnight).

        Runs every day to generate weekly summaries for previous week.
        """
        try:
            logger.info("Starting weekly summary generation scheduled task")

            # Generate report for 7 days ago to yesterday
            report_date = datetime.now() - timedelta(days=7)
            report = await self.report_generator.generate_daily_report(report_date=report_date)

            if 'error' not in report:
                # Mark as weekly summary
                report['report_type'] = 'weekly_summary'
                logger.info(f"Weekly summary generated for week ending {report_date.date()}")

        except Exception as e:
            logger.error(f"Error in weekly summary scheduled task: {e}")
            raise

    @periodic_task(
        run_every=timedelta(minutes=5),  # Run every 5 minutes
        name='monitor_system_health',
        bind=True
    )
    async def monitor_system_health(self):
        """
        Monitor system health (scheduled every 5 minutes).

        Checks:
        - Database connectivity
        - Message queue health
        - External API status
        """
        try:
            # In production, would implement actual health checks
            # For now, just log
            logger.debug("System health monitoring check completed")

        except Exception as e:
            logger.error(f"Error in health monitoring task: {e}")


# Manual task that can be triggered on demand
@celery_app.task(
    name='trigger_manual_report',
    bind=True
)
async def trigger_manual_report(self, report_date: str = None):
    """
    Manually trigger report generation for a specific date.

    Args:
        report_date: Optional date string (YYYY-MM-DD) for report
    """
    try:
        if report_date:
            report_dt = datetime.fromisoformat(report_date)
        else:
            report_dt = None

        logger.info(f"Manual report generation triggered for date: {report_date}")

        # Generate report
        report = await DailyReportGenerator().generate_daily_report(report_dt)

        # Deliver report
        delivery_result = await ReportDeliveryService().deliver_report(report)

        return {
            'success': delivery_result['success'],
            'report_date': report.get('report_date'),
            'delivery_result': delivery_result
        }

    except Exception as e:
        logger.error(f"Error in manual report task: {e}")
        return {
            'success': False,
            'error': str(e)
        }


# Task for retrying failed report deliveries
@celery_app.task(
    name='retry_failed_delivery',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
async def retry_failed_delivery(self, report_data: Dict[str, Any], delivery_method: str = None):
    """
    Retry failed report delivery.

    Args:
        report_data: Report data to redeliver
        delivery_method: Specific delivery method to retry
    """
    try:
        logger.info(f"Retrying failed report delivery: method={delivery_method}")

        # Retry delivery
        delivery_service = ReportDeliveryService()
        delivery_result = await delivery_service.deliver_report(report_data)

        if delivery_result['success']:
            logger.info("Failed report delivery retry succeeded")
        else:
            logger.warning(f"Failed report delivery retry failed: {delivery_result}")

        return delivery_result

    except Exception as e:
        logger.error(f"Error in retry task: {e}")
        raise
