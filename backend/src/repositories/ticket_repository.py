"""
Repository for support ticket data access operations.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.models.support_ticket import SupportTicket
from src.models.customer import Customer
from src.services.database import SessionLocal

class TicketRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_ticket(self, customer_id: int, channel: str, subject: str = None, description: str = None) -> SupportTicket:
        """Create a new support ticket."""
        db_ticket = SupportTicket(
            customer_id=customer_id,
            channel=channel,
            subject=subject,
            description=description
        )
        self.db.add(db_ticket)
        self.db.commit()
        self.db.refresh(db_ticket)
        return db_ticket

    def get_ticket(self, ticket_id: int) -> Optional[SupportTicket]:
        """Get a support ticket by ID."""
        return self.db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()

    def get_tickets_by_customer(self, customer_id: int) -> List[SupportTicket]:
        """Get all support tickets for a customer."""
        return self.db.query(SupportTicket).filter(SupportTicket.customer_id == customer_id).all()

    def get_tickets_by_status(self, status: str) -> List[SupportTicket]:
        """Get all support tickets with a specific status."""
        return self.db.query(SupportTicket).filter(SupportTicket.status == status).all()

    def update_ticket(self, ticket_id: int, **kwargs) -> Optional[SupportTicket]:
        """Update a support ticket."""
        db_ticket = self.get_ticket(ticket_id)
        if db_ticket:
            for key, value in kwargs.items():
                if hasattr(db_ticket, key):
                    setattr(db_ticket, key, value)
            self.db.commit()
            self.db.refresh(db_ticket)
        return db_ticket

    def delete_ticket(self, ticket_id: int) -> bool:
        """Delete a support ticket."""
        db_ticket = self.get_ticket(ticket_id)
        if db_ticket:
            self.db.delete(db_ticket)
            self.db.commit()
            return True
        return False

    def get_ticket_count_by_status(self) -> dict:
        """Get count of tickets by status."""
        from sqlalchemy import func
        result = self.db.query(
            SupportTicket.status,
            func.count(SupportTicket.id)
        ).group_by(SupportTicket.status).all()
        return {status: count for status, count in result}