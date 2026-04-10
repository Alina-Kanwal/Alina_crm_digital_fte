"""
User model for CRM agents and administrators.
"""
from sqlalchemy import Column, String, Boolean, Enum
import enum
from src.models.base import BaseModel

class UserRole(enum.Enum):
    ADMIN = "admin"
    AGENT = "agent"
    VIEWER = "viewer"

class User(BaseModel):
    """
    Internal CRM user (Agent or Admin).
    """
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.AGENT, nullable=False)
    is_active = Column(Boolean, default=True, index=True)

    def __repr__(self):
        return f"<User(id='{self.id}', email='{self.email}', role='{self.role}')>"
