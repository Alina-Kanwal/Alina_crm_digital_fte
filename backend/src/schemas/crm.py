from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.models.user import UserRole
from src.models.deal import DealStage

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole = UserRole.AGENT

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Deal Schemas
class DealBase(BaseModel):
    title: str
    description: Optional[str] = None
    amount: float = 0.0
    stage: DealStage = DealStage.LEAD
    customer_id: str
    owner_id: Optional[str] = None

class DealCreate(DealBase):
    pass

class DealUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    stage: Optional[DealStage] = None
    owner_id: Optional[str] = None

class DealResponse(DealBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Task Schemas
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_completed: bool = False
    due_date: Optional[datetime] = None
    customer_id: Optional[str] = None
    deal_id: Optional[str] = None
    assigned_to_id: Optional[str] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_completed: Optional[bool] = None
    due_date: Optional[datetime] = None
    assigned_to_id: Optional[str] = None

class TaskResponse(TaskBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Customer schemas
class CustomerBase(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    customer_metadata: Dict[str, Any] = Field(default_factory=dict)

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: str
    is_active: bool
    lead_score: float = 0.0
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
