"""
AuditLog model - records every real autonomous action taken by the system.
Replaces all synthesized/mocked activity data in the frontend.
"""
from sqlalchemy import Column, String, Text, Enum
import enum
from src.models.base import BaseModel


class AuditActionType(enum.Enum):
    DEAL_AUTO_ASSIGNED    = "deal_auto_assigned"
    NUDGE_TASK_CREATED    = "nudge_task_created"
    LEAD_SCORE_UPDATED    = "lead_score_updated"
    INQUIRY_RECEIVED      = "inquiry_received"
    INQUIRY_RESOLVED      = "inquiry_resolved"
    DEAL_STAGE_CHANGED    = "deal_stage_changed"
    CUSTOMER_CREATED      = "customer_created"
    AGENT_CYCLE_STARTED   = "agent_cycle_started"
    AGENT_CYCLE_COMPLETED = "agent_cycle_completed"


class AuditLog(BaseModel):
    """
    Persistent, real-time record of every autonomous action the system takes.
    Feeds the dashboard Activity Feed with 100% real data.
    """
    __tablename__ = "audit_logs"

    action_type = Column(
        Enum(AuditActionType),
        nullable=False,
        index=True
    )
    # Human-readable summary of what happened
    message = Column(Text, nullable=False)
    # Optional reference to the entity this action was performed on
    entity_id = Column(String(36), nullable=True, index=True)
    entity_type = Column(String(50), nullable=True)  # "deal", "customer", "task"

    def __repr__(self):
        return f"<AuditLog(action='{self.action_type}', msg='{self.message[:40]}')>"
