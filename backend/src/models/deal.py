"""
Deal model for tracking the sales/support pipeline.
"""
from sqlalchemy import Column, String, Float, ForeignKey, Enum
import enum
from sqlalchemy.orm import relationship
from src.models.base import BaseModel

class DealStage(enum.Enum):
    LEAD = "lead"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    WON = "won"
    LOST = "lost"

class Deal(BaseModel):
    """
    Represents a CRM Deal or Pipeline item.
    """
    __tablename__ = "deals"

    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    amount = Column(Float, default=0.0)
    stage = Column(Enum(DealStage), default=DealStage.LEAD, index=True)
    
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    
    # Relationships
    customer = relationship("Customer")
    owner = relationship("User")

    def __repr__(self):
        return f"<Deal(id='{self.id}', title='{self.title}', stage='{self.stage}')>"
