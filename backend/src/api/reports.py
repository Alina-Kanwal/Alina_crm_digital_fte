"""
API endpoints for reporting and analytics.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta
import logging
from src.services.reports.daily import DailyReportGenerator

logger = logging.getLogger(__name__)

router = APIRouter()
report_generator = DailyReportGenerator()


@router.get("/daily")
async def get_daily_report(
    date: Optional[str] = Query(None, description="Report date in ISO format (YYYY-MM-DD)")
):
    """
    Generate and retrieve daily support report.
    """
    try:
        report_date = datetime.fromisoformat(date) if date else None
        report = await report_generator.generate_daily_report(report_date)
        
        if "error" in report:
            logger.error(f"Failed to generate daily report: {report['error']}")
            raise HTTPException(status_code=500, detail=report["error"])
            
        return report
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Error in daily report endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sentiment")
async def get_sentiment_analysis(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze")
):
    """
    Retrieve sentiment analysis summary for the specifies period.
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Internal method call
        summary = await report_generator._generate_sentiment_summary(start_date, end_date)
        
        if "error" in summary:
            raise HTTPException(status_code=500, detail=summary["error"])
            
        return summary
    except Exception as e:
        logger.error(f"Error in sentiment analysis endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_metrics(
    days: int = Query(7, ge=1, le=30, description="Number of days for metrics")
):
    """
    Retrieve performance metrics for the specified period.
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        ticket_summary = await report_generator._generate_ticket_summary(start_date, end_date)
        channel_performance = await report_generator._analyze_channel_performance(start_date, end_date)
        
        return {
            "period_days": days,
            "ticket_summary": ticket_summary,
            "channel_performance": channel_performance
        }
    except Exception as e:
        logger.error(f"Error in metrics endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))