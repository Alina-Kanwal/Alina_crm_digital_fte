"""
Customer model for storing customer information and cross-channel identification.
"""
from sqlalchemy import Column, String, Text, JSON, Boolean, Index, Float, DateTime
from src.utils.db_utils import Vector1536
from src.models.base import BaseModel


class Customer(BaseModel):
    """
    Represents an individual or entity seeking support.
    """

    __tablename__ = "customers"

    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), index=True, nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    session_ids = Column(JSON, default=list)
    embedding = Column(Vector1536, nullable=True)
    lead_score = Column(Float, default=0.0)
    customer_metadata = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True, index=True)

    def __repr__(self):
        return f"<Customer(id='{self.id}', email='{self.email}', phone='{self.phone}')>"

    @property
    def identifiers(self) -> dict:
        """Get all available identifiers for cross-channel matching."""
        identifiers = {}
        if self.email:
            identifiers["email"] = self.email
        if self.phone:
            identifiers["phone"] = self.phone
        return identifiers
