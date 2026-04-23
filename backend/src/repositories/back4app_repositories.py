"""
Back4App-backed repositories for CRM entities.

These replace the SQLAlchemy repositories for Customer, Deal, Task,
and AuditLog. They speak to the Parse REST API via ParseClient and
return plain Python objects whose attributes match the existing
Pydantic response schemas (ConfigDict from_attributes=True).
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.models.deal import DealStage
from src.models.audit_log import AuditActionType
from src.services.back4app_client import parse_client

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
# Helper — Parse response → plain object with right attribute names
# ------------------------------------------------------------------ #

def _parse_dt(value: Any) -> Optional[datetime]:
    """Convert Parse ISO-8601 string or Date dict to a datetime."""
    if value is None:
        return None
    if isinstance(value, dict) and value.get("__type") == "Date":
        value = value["iso"]
    if isinstance(value, str):
        # Python 3.10 fromisoformat doesn't handle trailing Z
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return None


class _Record:
    """
    Minimal attribute-bag that satisfies Pydantic's from_attributes=True.
    Lets us avoid creating full SQLAlchemy models while keeping the
    existing response_model declarations in crm.py untouched.
    """
    __slots__: tuple = ()

    def __init__(self, **kwargs: Any):
        for k, v in kwargs.items():
            object.__setattr__(self, k, v)

    def __repr__(self):
        attrs = {k: getattr(self, k, None) for k in self.__class__.__annotations__}
        return f"<{self.__class__.__name__} {attrs}>"


# ------------------------------------------------------------------ #
# Customer
# ------------------------------------------------------------------ #

class B4ACustomerRecord(_Record):
    id: str
    email: str
    phone: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    customer_metadata: Dict[str, Any]
    is_active: bool
    lead_score: float
    created_at: datetime


def _to_customer(raw: Dict) -> B4ACustomerRecord:
    return B4ACustomerRecord(
        id=raw.get("objectId", ""),
        email=raw.get("email", ""),
        phone=raw.get("phone"),
        first_name=raw.get("firstName"),
        last_name=raw.get("lastName"),
        customer_metadata=raw.get("metadata", {}),
        is_active=raw.get("isActive", True),
        lead_score=raw.get("leadScore", 0.0),
        created_at=_parse_dt(raw.get("createdAt")) or datetime.now(timezone.utc),
    )


class B4ACustomerRepository:
    CLASS = "Customer"

    def get_all(self, skip: int = 0, limit: int = 100) -> List[B4ACustomerRecord]:
        results = parse_client.find(self.CLASS, skip=skip, limit=limit)
        return [_to_customer(r) for r in results]

    def get_by_id(self, customer_id: str) -> Optional[B4ACustomerRecord]:
        raw = parse_client.get(self.CLASS, customer_id)
        return _to_customer(raw) if raw else None

    def get_by_email(self, email: str) -> Optional[B4ACustomerRecord]:
        results = parse_client.find(self.CLASS, where={"email": email}, limit=1)
        return _to_customer(results[0]) if results else None

    def create(self, customer) -> B4ACustomerRecord:
        data = {
            "email":     customer.email,
            "phone":     customer.phone,
            "firstName": customer.first_name,
            "lastName":  customer.last_name,
            "metadata":  customer.customer_metadata or {},
            "isActive":  True,
            "leadScore": 0.0,
        }
        raw = parse_client.create(self.CLASS, data)
        return _to_customer(raw)

    def update_lead_score(self, customer_id: str, points: float) -> Optional[B4ACustomerRecord]:
        existing = self.get_by_id(customer_id)
        if not existing:
            return None
        new_score = (existing.lead_score or 0.0) + points
        raw = parse_client.update(self.CLASS, customer_id, {"leadScore": new_score})
        return _to_customer(raw)


# ------------------------------------------------------------------ #
# Deal
# ------------------------------------------------------------------ #

class B4ADealRecord(_Record):
    id: str
    title: str
    description: Optional[str]
    amount: float
    stage: DealStage
    customer_id: str
    owner_id: Optional[str]
    created_at: datetime
    updated_at: datetime


def _to_deal(raw: Dict) -> B4ADealRecord:
    stage_str = raw.get("stage", DealStage.LEAD.value)
    try:
        stage = DealStage(stage_str)
    except ValueError:
        stage = DealStage.LEAD

    return B4ADealRecord(
        id=raw.get("objectId", ""),
        title=raw.get("title", ""),
        description=raw.get("description"),
        amount=raw.get("amount", 0.0),
        stage=stage,
        customer_id=raw.get("customerId", ""),
        owner_id=raw.get("ownerId"),
        created_at=_parse_dt(raw.get("createdAt")) or datetime.now(timezone.utc),
        updated_at=_parse_dt(raw.get("updatedAt")) or datetime.now(timezone.utc),
    )


class B4ADealRepository:
    CLASS = "Deal"

    def get_all(self, skip: int = 0, limit: int = 100) -> List[B4ADealRecord]:
        results = parse_client.find(self.CLASS, skip=skip, limit=limit)
        return [_to_deal(r) for r in results]

    def get_by_id(self, deal_id: str) -> Optional[B4ADealRecord]:
        raw = parse_client.get(self.CLASS, deal_id)
        return _to_deal(raw) if raw else None

    def create(self, deal) -> B4ADealRecord:
        data = {
            "title":       deal.title,
            "description": deal.description,
            "amount":      deal.amount,
            "stage":       deal.stage.value if isinstance(deal.stage, DealStage) else deal.stage,
            "customerId":  deal.customer_id,
            "ownerId":     deal.owner_id,
        }
        raw = parse_client.create(self.CLASS, data)
        return _to_deal(raw)

    def update(self, deal_id: str, deal_update) -> Optional[B4ADealRecord]:
        if not self.get_by_id(deal_id):
            return None
        data = {
            k: (v.value if isinstance(v, DealStage) else v)
            for k, v in deal_update.model_dump(exclude_unset=True).items()
            if v is not None
        }
        raw = parse_client.update(self.CLASS, deal_id, data)
        return _to_deal(raw)

    def get_cold_deals(self, stage: DealStage, older_than_days: int) -> List[B4ADealRecord]:
        from datetime import timedelta
        cutoff = (datetime.now(timezone.utc) - timedelta(days=older_than_days)).isoformat()
        where = {
            "stage": stage.value,
            "createdAt": {"$lt": {"__type": "Date", "iso": cutoff}},
        }
        results = parse_client.find(self.CLASS, where=where)
        return [_to_deal(r) for r in results]


# ------------------------------------------------------------------ #
# Task
# ------------------------------------------------------------------ #

class B4ATaskRecord(_Record):
    id: str
    title: str
    description: Optional[str]
    is_completed: bool
    due_date: Optional[datetime]
    customer_id: Optional[str]
    deal_id: Optional[str]
    assigned_to_id: Optional[str]
    created_at: datetime
    updated_at: datetime


def _to_task(raw: Dict) -> B4ATaskRecord:
    return B4ATaskRecord(
        id=raw.get("objectId", ""),
        title=raw.get("title", ""),
        description=raw.get("description"),
        is_completed=raw.get("isCompleted", False),
        due_date=_parse_dt(raw.get("dueDate")),
        customer_id=raw.get("customerId"),
        deal_id=raw.get("dealId"),
        assigned_to_id=raw.get("assignedToId"),
        created_at=_parse_dt(raw.get("createdAt")) or datetime.now(timezone.utc),
        updated_at=_parse_dt(raw.get("updatedAt")) or datetime.now(timezone.utc),
    )


class B4ATaskRepository:
    CLASS = "Task"

    def get_all(self, skip: int = 0, limit: int = 100) -> List[B4ATaskRecord]:
        results = parse_client.find(self.CLASS, skip=skip, limit=limit)
        return [_to_task(r) for r in results]

    def get_by_id(self, task_id: str) -> Optional[B4ATaskRecord]:
        raw = parse_client.get(self.CLASS, task_id)
        return _to_task(raw) if raw else None

    def create(self, task) -> B4ATaskRecord:
        data = {
            "title":         task.title,
            "description":   task.description,
            "isCompleted":   task.is_completed,
            "customerId":    task.customer_id,
            "dealId":        task.deal_id,
            "assignedToId":  task.assigned_to_id,
        }
        if task.due_date:
            data["dueDate"] = {"__type": "Date", "iso": task.due_date.isoformat()}
        raw = parse_client.create(self.CLASS, data)
        return _to_task(raw)

    def update(self, task_id: str, task_update) -> Optional[B4ATaskRecord]:
        if not self.get_by_id(task_id):
            return None
        raw_data = task_update.model_dump(exclude_unset=True)
        data: Dict[str, Any] = {}
        for k, v in raw_data.items():
            if v is None:
                continue
            if k == "due_date":
                data["dueDate"] = {"__type": "Date", "iso": v.isoformat()}
            elif k == "is_completed":
                data["isCompleted"] = v
            elif k == "assigned_to_id":
                data["assignedToId"] = v
            else:
                data[k] = v
        raw = parse_client.update(self.CLASS, task_id, data)
        return _to_task(raw)


# ------------------------------------------------------------------ #
# AuditLog
# ------------------------------------------------------------------ #

class B4AAuditLogRecord(_Record):
    id: str
    action_type: AuditActionType
    message: str
    entity_id: Optional[str]
    entity_type: Optional[str]
    created_at: datetime


def _to_audit_log(raw: Dict) -> B4AAuditLogRecord:
    try:
        action_type = AuditActionType(raw.get("actionType", "inquiry_received"))
    except ValueError:
        action_type = AuditActionType.INQUIRY_RECEIVED
    return B4AAuditLogRecord(
        id=raw.get("objectId", ""),
        action_type=action_type,
        message=raw.get("message", ""),
        entity_id=raw.get("entityId"),
        entity_type=raw.get("entityType"),
        created_at=_parse_dt(raw.get("createdAt")) or datetime.now(timezone.utc),
    )


class B4AAuditLogRepository:
    CLASS = "AuditLog"

    def get_recent(self, limit: int = 20) -> List[B4AAuditLogRecord]:
        results = parse_client.find(self.CLASS, limit=limit, order="-createdAt")
        return [_to_audit_log(r) for r in results]

    def count_by_action(self, action_type: AuditActionType) -> int:
        return parse_client.count(self.CLASS, where={"actionType": action_type.value})

    def create(self, action_type: AuditActionType, message: str,
               entity_id: Optional[str] = None, entity_type: Optional[str] = None) -> B4AAuditLogRecord:
        data = {
            "actionType":  action_type.value,
            "message":     message,
            "entityId":    entity_id,
            "entityType":  entity_type,
        }
        raw = parse_client.create(self.CLASS, data)
        return _to_audit_log(raw)
