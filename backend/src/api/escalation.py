"""
Manual escalation API endpoint for Digital FTE AI Customer Success Agent.
Allows human agents to manually escalate tickets.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from src.services.escalation.engine import EscalationEngine, EscalationTrigger, EscalationSeverity
from src.services.escalation.notifier import HumanAgentNotifier
from src.services.database import SessionLocal
from src.models.support_ticket import SupportTicket

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/escalation", tags=["escalation"])


class ManualEscalationRequest(BaseModel):
    """Request model for manual escalation."""
    ticket_id: int = Field(..., description="Support ticket ID to escalate")
    agent_id: str = Field(..., description="ID of the agent requesting escalation")
    reason: str = Field(..., description="Reason for escalation")
    priority: Optional[int] = Field(2, description="Priority level (1-4, default: 2)")
    notes: Optional[str] = Field(None, description="Additional notes for the escalation")


class ManualEscalationResponse(BaseModel):
    """Response model for manual escalation."""
    success: bool
    ticket_id: int
    escalated: bool
    message: str
    timestamp: str


@router.post("/manual", response_model=ManualEscalationResponse)
async def manual_escalation(
    request: ManualEscalationRequest,
    correlation_id: Optional[str] = None
) -> ManualEscalationResponse:
    """
    Manually escalate a support ticket.

    Per Constitution Principle XII:
    Human agents must have ability to manually escalate when needed.

    Args:
        request: Manual escalation request
        correlation_id: Optional correlation ID for tracing

    Returns:
        Escalation response with status and details
    """
    try:
        # Log the escalation request
        logger.info(
            f"Manual escalation request | "
            f"ticket_id={request.ticket_id}, "
            f"agent_id={request.agent_id}, "
            f"reason={request.reason}, "
            f"correlation_id={correlation_id}"
        )

        db = SessionLocal()

        # Get the ticket
        ticket = db.query(SupportTicket).filter(
            SupportTicket.id == request.ticket_id
        ).first()

        if not ticket:
            db.close()
            raise HTTPException(
                status_code=404,
                detail=f"Ticket {request.ticket_id} not found"
            )

        # Check if already escalated
        if ticket.status == 'escalated':
            db.close()
            return ManualEscalationResponse(
                success=False,
                ticket_id=request.ticket_id,
                escalated=False,
                message="Ticket is already escalated",
                timestamp=datetime.now().isoformat()
            )

        # Update ticket to escalated
        ticket.status = 'escalated'
        ticket.assigned_to = request.agent_id
        ticket.priority = request.priority
        ticket.updated_at = datetime.now()

        # Add escalation notes if provided
        if request.notes:
            if not ticket.resolution_summary:
                ticket.resolution_summary = ""
            ticket.resolution_summary += f"\n\nManual Escalation by {request.agent_id}: {request.notes}"

        db.commit()

        # Notify human agents
        notifier = HumanAgentNotifier()
        notification_data = {
            'escalation_id': f"MANUAL-{request.ticket_id}-{int(datetime.now().timestamp())}",
            'ticket_id': request.ticket_id,
            'customer_id': ticket.customer_id,
            'trigger': EscalationTrigger.MANUAL_REQUEST,
            'severity': EscalationSeverity.HIGH,
            'reason': request.reason,
            'message': ticket.message,
            'assigned_to': request.agent_id,
            'priority': request.priority,
            'escalation_type': 'manual',
            'requested_by': request.agent_id
        }

        await notifier.notify_escalation(notification_data)

        db.close()

        logger.info(
            f"Manual escalation completed: ticket_id={request.ticket_id}, "
            f"assigned_to={request.agent_id}"
        )

        return ManualEscalationResponse(
            success=True,
            ticket_id=request.ticket_id,
            escalated=True,
            message="Ticket successfully escalated",
            timestamp=datetime.now().isoformat()
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error processing manual escalation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing manual escalation: {str(e)}"
        )


@router.get("/status/{ticket_id}")
async def get_escalation_status(
    ticket_id: int,
    correlation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get escalation status for a specific ticket.

    Args:
        ticket_id: Support ticket ID
        correlation_id: Optional correlation ID for tracing

    Returns:
        Dictionary containing escalation status
    """
    try:
        db = SessionLocal()

        ticket = db.query(SupportTicket).filter(
            SupportTicket.id == ticket_id
        ).first()

        db.close()

        if not ticket:
            raise HTTPException(
                status_code=404,
                detail=f"Ticket {ticket_id} not found"
            )

        is_escalated = ticket.status == 'escalated'

        logger.debug(
            f"Escalation status requested: ticket_id={ticket_id}, "
            f"escalated={is_escalated}, correlation_id={correlation_id}"
        )

        return {
            'ticket_id': ticket_id,
            'status': ticket.status,
            'is_escalated': is_escalated,
            'assigned_to': ticket.assigned_to,
            'priority': ticket.priority,
            'created_at': ticket.created_at.isoformat() if ticket.created_at else None,
            'updated_at': ticket.updated_at.isoformat() if ticket.updated_at else None,
            'resolution_summary': ticket.resolution_summary
        }

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error getting escalation status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting escalation status: {str(e)}"
        )


@router.get("/stats")
async def get_escalation_stats(
    days: int = 7,
    correlation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get escalation statistics for a time period.

    Args:
        days: Number of days to look back (default: 7)
        correlation_id: Optional correlation ID for tracing

    Returns:
        Dictionary containing escalation statistics
    """
    try:
        from src.services.escalation.tracker import EscalationTracker

        tracker = EscalationTracker()
        stats = await tracker.calculate_escalation_rate()

        logger.info(
            f"Escalation stats requested: days={days}, "
            f"rate={stats.get('escalation_percentage', 0):.1f}%, "
            f"correlation_id={correlation_id}"
        )

        return stats

    except Exception as e:
        logger.error(f"Error getting escalation stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting escalation stats: {str(e)}"
        )
