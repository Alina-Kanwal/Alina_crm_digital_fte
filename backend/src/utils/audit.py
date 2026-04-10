from src.models.audit_log import AuditLog, AuditActionType
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

def write_audit(db: Session, action_type: AuditActionType, message: str,
                entity_id: str = None, entity_type: str = None):
    """
    Central helper to record a real autonomous action in the audit log.
    This ensures the dashboard 'System Activity' feed is always 100% real.
    """
    try:
        log = AuditLog(
            action_type=action_type,
            message=message,
            entity_id=entity_id,
            entity_type=entity_type,
        )
        db.add(log)
        # We don't commit here, usually the caller will commit as part of their transaction
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")
