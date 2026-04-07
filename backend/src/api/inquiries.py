"""
API endpoints for handling customer inquiries from multiple channels.
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any
import logging
from src.services.inquiry_processor import InquiryProcessor
from src.middleware.correlation import get_correlation_id

logger = logging.getLogger(__name__)

router = APIRouter()
inquiry_processor = InquiryProcessor()


@router.post("/email")
async def handle_email_inquiry(inquiry_data: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Handle incoming email inquiry.

    Expected format:
    {
        "id": "email-unique-id",
        "sender": "customer@example.com",
        "subject": "Email subject",
        "body": "Email body content",
        "timestamp": "2026-03-28 10:30:00"
    }
    """
    correlation_id = get_correlation_id()
    logger.info(f"Processing email inquiry [{correlation_id}]: {inquiry_data.get('id')}")

    try:
        result = await inquiry_processor.process_inquiry(inquiry_data, 'email')

        if not result.get('success'):
            logger.error(f"Failed to process email inquiry [{correlation_id}]: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get('error'))

        # Add correlation ID to response
        result['correlation_id'] = correlation_id

        logger.info(f"Email inquiry processed successfully [{correlation_id}] in {result.get('processing_time_seconds'):.2f}s")
        return result

    except Exception as e:
        logger.error(f"Error handling email inquiry [{correlation_id}]: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/whatsapp")
async def handle_whatsapp_inquiry(inquiry_data: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Handle incoming WhatsApp inquiry.

    Expected format:
    {
        "id": "whatsapp-unique-id",
        "sender": "whatsapp:+1234567890",
        "body": "Message content",
        "timestamp": "2026-03-28 10:30:00"
    }
    """
    correlation_id = get_correlation_id()
    logger.info(f"Processing WhatsApp inquiry [{correlation_id}]: {inquiry_data.get('id')}")

    try:
        result = await inquiry_processor.process_inquiry(inquiry_data, 'whatsapp')

        if not result.get('success'):
            logger.error(f"Failed to process WhatsApp inquiry [{correlation_id}]: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get('error'))

        # Add correlation ID to response
        result['correlation_id'] = correlation_id

        logger.info(f"WhatsApp inquiry processed successfully [{correlation_id}] in {result.get('processing_time_seconds'):.2f}s")
        return result

    except Exception as e:
        logger.error(f"Error handling WhatsApp inquiry [{correlation_id}]: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webform")
async def handle_webform_inquiry(inquiry_data: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Handle incoming web form inquiry.

    Expected format:
    {
        "id": "webform-unique-id",
        "sender": "customer@example.com",
        "name": "Customer Name",
        "subject": "Form subject",
        "body": "Form content",
        "timestamp": "2026-03-28 10:30:00",
        "metadata": {
            "name": "Customer Name",
            "email": "customer@example.com",
            "phone": "+1234567890"
        }
    }
    """
    correlation_id = get_correlation_id()
    logger.info(f"Processing webform inquiry [{correlation_id}]: {inquiry_data.get('id')}")

    try:
        result = await inquiry_processor.process_inquiry(inquiry_data, 'webform')

        if not result.get('success'):
            logger.error(f"Failed to process webform inquiry [{correlation_id}]: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get('error'))

        # Add correlation ID to response
        result['correlation_id'] = correlation_id

        logger.info(f"Webform inquiry processed successfully [{correlation_id}] in {result.get('processing_time_seconds'):.2f}s")
        return result

    except Exception as e:
        logger.error(f"Error handling webform inquiry [{correlation_id}]: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_inquiry_metrics():
    """Get inquiry processing performance metrics."""
    return inquiry_processor.get_performance_metrics()


# Health check endpoint for the inquiry processor
@router.get("/health")
async def inquiry_processor_health():
    """Check health of inquiry processing components."""
    try:
        agent_available = inquiry_processor.ai_agent.is_available()
        return {
            "status": "healthy" if agent_available else "degraded",
            "agent_available": agent_available,
            "components": {
                "message_parser": "healthy",
                "ai_agent": "healthy" if agent_available else "unavailable",
                "customer_identifier": "healthy",
                "conversation_manager": "healthy",
                "ticket_service": "healthy"
            }
        }
    except Exception as e:
        logger.error(f"Inquiry processor health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }