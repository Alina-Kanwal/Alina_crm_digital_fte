"""
Basic CRUD operations for support tickets.

Provides core database operations for ticket lifecycle management.
"""

import logging
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from src.models import SupportTicket, Customer
from src.database.connection import get_async_db_session

logger = logging.getLogger(__name__)


class TicketCRUDService:
    """
    CRUD service for support tickets.

    Provides Create, Read, Update, Delete, and List operations
    for ticket management.
    """

    async def create_ticket(
        self,
        session: AsyncSession,
        customer_id: str,
        channel: str,
        content: str,
        external_id: Optional[str] = None,
        subject: Optional[str] = None,
    ) -> SupportTicket:
        """
        Create a new support ticket.

        Args:
            session: Database session
            customer_id: Customer ID
            channel: Channel identifier (email, whatsapp, web_form)
            content: Message content
            external_id: External system message ID
            subject: Subject line (for email/web form)

        Returns:
            Created SupportTicket instance
        """
        ticket = SupportTicket(
            customer_id=customer_id,
            channel=channel,
            content=content,
            external_id=external_id,
            subject=subject,
            received_at=datetime.utcnow().isoformat(),
        )

        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)

        logger.info(f"Created ticket: {ticket.id} for customer: {customer_id}")
        return ticket

    async def get_ticket_by_id(
        self,
        session: AsyncSession,
        ticket_id: str,
    ) -> Optional[SupportTicket]:
        """
        Retrieve ticket by ID.

        Args:
            session: Database session
            ticket_id: Ticket ID

        Returns:
            SupportTicket instance or None
        """
        result = await session.execute(
            select(SupportTicket)
            .where(SupportTicket.id == ticket_id)
            .options(selectinload(SupportTicket.customer))
        )

        ticket = result.scalar_one_or_none()
        if ticket:
            logger.debug(f"Retrieved ticket: {ticket_id}")

        return ticket

    async def get_tickets_by_customer(
        self,
        session: AsyncSession,
        customer_id: str,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> List[SupportTicket]:
        """
        Retrieve tickets for a customer.

        Args:
            session: Database session
            customer_id: Customer ID
            limit: Maximum tickets to return
            offset: Offset for pagination
            status: Optional status filter

        Returns:
            List of SupportTicket instances
        """
        query = (
            select(SupportTicket)
            .where(SupportTicket.customer_id == customer_id)
            .order_by(SupportTicket.created_at.desc())
        )

        if status:
            # Filter by status (need to handle the computed property)
            query = query.where(SupportTicket.escalated == ("true" if status == "escalated" else "false"))

        result = await session.execute(query.limit(limit).offset(offset))
        tickets = result.scalars().all()

        logger.debug(f"Retrieved {len(tickets)} tickets for customer: {customer_id}")
        return tickets

    async def list_tickets(
        self,
        session: AsyncSession,
        limit: int = 100,
        offset: int = 0,
        channel: Optional[str] = None,
        status: Optional[str] = None,
        customer_id: Optional[str] = None,
    ) -> List[SupportTicket]:
        """
        List tickets with optional filters.

        Args:
            session: Database session
            limit: Maximum tickets to return
            offset: Offset for pagination
            channel: Optional channel filter
            status: Optional status filter
            customer_id: Optional customer ID filter

        Returns:
            List of SupportTicket instances
        """
        query = select(SupportTicket).order_by(SupportTicket.created_at.desc())

        if channel:
            query = query.where(SupportTicket.channel == channel)

        if customer_id:
            query = query.where(SupportTicket.customer_id == customer_id)

        if status:
            query = query.where(SupportTicket.escalated == ("true" if status == "escalated" else "false"))

        result = await session.execute(query.limit(limit).offset(offset))
        tickets = result.scalars().all()

        logger.debug(f"Listed {len(tickets)} tickets with filters")
        return tickets

    async def update_ticket(
        self,
        session: AsyncSession,
        ticket_id: str,
        ai_response: Optional[str] = None,
        sentiment: Optional[str] = None,
        confidence_score: Optional[float] = None,
        escalated: Optional[str] = None,
        escalation_reason: Optional[str] = None,
        resolution_category: Optional[str] = None,
        resolved_at: Optional[str] = None,
    ) -> Optional[SupportTicket]:
        """
        Update ticket fields.

        Args:
            session: Database session
            ticket_id: Ticket ID
            ai_response: Agent's response
            sentiment: Detected sentiment
            confidence_score: AI confidence
            escalated: Whether escalated to human
            escalation_reason: Reason for escalation
            resolution_category: Type of resolution
            resolved_at: Resolution timestamp

        Returns:
            Updated SupportTicket instance or None
        """
        # Get existing ticket
        ticket = await self.get_ticket_by_id(session, ticket_id)
        if not ticket:
            return None

        # Update fields
        if ai_response is not None:
            ticket.ai_response = ai_response
            ticket.responded_at = datetime.utcnow().isoformat()

        if sentiment is not None:
            ticket.sentiment = sentiment

        if confidence_score is not None:
            ticket.confidence_score = confidence_score

        if escalated is not None:
            ticket.escalated = escalated

        if escalation_reason is not None:
            ticket.escalation_reason = escalation_reason

        if resolution_category is not None:
            ticket.resolution_category = resolution_category

        if resolved_at is not None:
            ticket.resolved_at = resolved_at

        await session.commit()
        await session.refresh(ticket)

        logger.info(f"Updated ticket: {ticket_id}")
        return ticket

    async def delete_ticket(
        self,
        session: AsyncSession,
        ticket_id: str,
    ) -> bool:
        """
        Delete a ticket.

        Args:
            session: Database session
            ticket_id: Ticket ID

        Returns:
            True if deleted, False if not found
        """
        ticket = await self.get_ticket_by_id(session, ticket_id)
        if not ticket:
            return False

        await session.delete(ticket)
        await session.commit()

        logger.warning(f"Deleted ticket: {ticket_id}")
        return True

    async def get_ticket_statistics(
        self,
        session: AsyncSession,
        days: int = 7,
    ) -> dict:
        """
        Get ticket statistics.

        Args:
            session: Database session
            days: Number of days to look back

        Returns:
            Dictionary with statistics
        """
        since = datetime.utcnow() - datetime(days=days)

        # Get total tickets in period
        result = await session.execute(
            select(SupportTicket)
            .where(SupportTicket.created_at >= since.isoformat())
        )
        total_tickets = len(result.scalars().all())

        # Get escalated tickets
        result = await session.execute(
            select(SupportTicket)
            .where(
                and_(
                    SupportTicket.created_at >= since.isoformat(),
                    SupportTicket.escalated == "true",
                )
            )
        )
        escalated_tickets = len(result.scalars().all())

        # Get resolved tickets
        result = await session.execute(
            select(SupportTicket)
            .where(
                and_(
                    SupportTicket.created_at >= since.isoformat(),
                    SupportTicket.resolved_at.isnot(None),
                )
            )
        )
        resolved_tickets = len(result.scalars().all())

        # Get sentiment breakdown
        result = await session.execute(
            select(SupportTicket.sentiment)
            .where(SupportTicket.created_at >= since.isoformat())
        )

        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0, None: 0}
        for row in result.scalars():
            sentiment = row[0]
            sentiment_counts[sentiment if sentiment in sentiment_counts else None] += 1

        return {
            "total_tickets": total_tickets,
            "escalated_tickets": escalated_tickets,
            "resolved_tickets": resolved_tickets,
            "escalation_rate": escalated_tickets / total_tickets if total_tickets > 0 else 0,
            "resolution_rate": resolved_tickets / total_tickets if total_tickets > 0 else 0,
            "sentiment_distribution": sentiment_counts,
            "period_days": days,
        }


# Singleton service instance
_crud_service: Optional[TicketCRUDService] = None


def get_ticket_crud_service() -> TicketCRUDService:
    """
    Get or create singleton CRUD service.

    Returns:
        TicketCRUDService instance
    """
    global _crud_service
    if _crud_service is None:
        _crud_service = TicketCRUDService()
    return _crud_service
