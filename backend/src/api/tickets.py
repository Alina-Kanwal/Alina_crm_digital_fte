"""
API endpoints for ticket management.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Any
import logging
from src.services.ticket_crud import get_ticket_crud_service
from src.database.connection import get_async_db_session
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()
ticket_service = get_ticket_crud_service()


@router.get("/")
async def get_tickets(
    limit: int = Query(100, ge=1, le=500),
    offset: int = 0,
    channel: Optional[str] = None,
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
):
    """
    List all support tickets with filtering options.
    """
    async with get_async_db_session() as session:
        try:
            tickets = await ticket_service.list_tickets(
                session=session,
                limit=limit,
                offset=offset,
                channel=channel,
                status=status,
                customer_id=customer_id
            )
            return tickets
        except Exception as e:
            logger.error(f"Error listing tickets: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticket_id}")
async def get_ticket(ticket_id: str):
    """
    Retrieve a specific ticket by ID.
    """
    async with get_async_db_session() as session:
        try:
            ticket = await ticket_service.get_ticket_by_id(session, ticket_id)
            if not ticket:
                raise HTTPException(status_code=404, detail="Ticket not found")
            return ticket
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving ticket {ticket_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.put("/{ticket_id}")
async def update_ticket(ticket_id: str, ticket_data: dict):
    """
    Update ticket fields.
    """
    async with get_async_db_session() as session:
        try:
            updated_ticket = await ticket_service.update_ticket(
                session=session,
                ticket_id=ticket_id,
                **ticket_data
            )
            if not updated_ticket:
                raise HTTPException(status_code=404, detail="Ticket not found")
            return updated_ticket
        except Exception as e:
            logger.error(f"Error updating ticket {ticket_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
async def get_ticket_stats(days: int = 7):
    """
    Get ticket performance statistics.
    """
    async with get_async_db_session() as session:
        try:
            stats = await ticket_service.get_ticket_statistics(session, days)
            return stats
        except Exception as e:
            logger.error(f"Error getting ticket stats: {e}")
            raise HTTPException(status_code=500, detail=str(e))