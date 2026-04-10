"""
Task model for tracking follow-ups and actions.
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import BaseModel

class Task(BaseModel):
    """
    Represents an actionable item or follow-up in the CRM.
    """
    __tablename__ = "tasks"

    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    is_completed = Column(Boolean, default=False, index=True)
    due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=True, index=True)
    deal_id = Column(String(36), ForeignKey("deals.id"), nullable=True, index=True)
    assigned_to_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    
    # Relationships
    customer = relationship("Customer")
    deal = relationship("Deal")
    assigned_to = relationship("User")

    def __repr__(self):
        return f"<Task(id='{self.id}', title='{self.title}', completed={self.is_completed})>"
