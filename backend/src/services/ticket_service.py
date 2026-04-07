"""
Service layer for support ticket business logic.
"""
from typing import List, Optional
from src.repositories.ticket_repository import TicketRepository
from src.models.support_ticket import SupportTicket
from src.services.database import SessionLocal

class TicketService:
    def __init__(self):
        self.db = SessionLocal()
        self.repository = TicketRepository(self.db)

    def create_ticket(self, customer_id: int, channel: str, subject: str = None, description: str = None) -> SupportTicket:
        """Create a new support ticket."""
        return self.repository.create_ticket(customer_id, channel, subject, description)

    def get_ticket(self, ticket_id: int) -> Optional[SupportTicket]:
        """Get a support ticket by ID."""
        return self.repository.get_ticket(ticket_id)

    def get_tickets_by_customer(self, customer_id: int) -> List[SupportTicket]:
        """Get all support tickets for a customer."""
        return self.repository.get_tickets_by_customer(customer_id)

    def get_tickets_by_status(self, status: str) -> List[SupportTicket]:
        """Get all support tickets with a specific status."""
        return self.repository.get_tickets_by_status(status)

    def update_ticket(self, ticket_id: int, **kwargs) -> Optional[SupportTicket]:
        """Update a support ticket."""
        return self.repository.update_ticket(ticket_id, **kwargs)

    def delete_ticket(self, ticket_id: int) -> bool:
        """Delete a support ticket."""
        return self.repository.delete_ticket(ticket_id)

    def get_ticket_count_by_status(self) -> dict:
        """Get count of tickets by status."""
        return self.repository.get_ticket_count_by_status()

    def close(self):
        """Close database session."""
        self.db.close()