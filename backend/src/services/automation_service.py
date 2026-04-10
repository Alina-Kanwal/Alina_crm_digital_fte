import logging
from typing import Optional
from src.database.connection import get_db_session
from src.models.deal import DealStage
from src.repositories import CustomerRepository, DealRepository, TaskRepository
from src.schemas.crm import DealCreate, TaskCreate
from datetime import datetime, timedelta
from src.utils.audit import write_audit
from src.models.audit_log import AuditActionType

logger = logging.getLogger(__name__)

class AutomationService:
    """
    Handles CRM workflow automations based on events and AI insights.
    """

    def process_automation_triggers(self, customer_id: str, content: str, sentiment: str, sentiment_score: float):
        """
        Main entry point for triggering automations after an inquiry is processed.
        """
        logger.info(f"Running automation triggers for customer {customer_id}")
        
        # 1. High intent -> Auto Deal + Lead Score push
        if sentiment == "positive" and sentiment_score > 0.7:
             self._create_auto_deal(customer_id, content)
             self._update_lead_score(customer_id, 20.0) # Significant boost
        
        # 2. Support / Action required -> Auto Task
        if any(word in content.lower() for word in ["help", "support", "issue", "problem", "broken", "pricing"]):
            self._create_auto_task(customer_id, content)
            self._update_lead_score(customer_id, 5.0) # Minor interest boost

    def _update_lead_score(self, customer_id: str, points: float):
        with get_db_session() as db:
            repo = CustomerRepository(db)
            repo.update_lead_score(customer_id, points)
            write_audit(
                db, AuditActionType.LEAD_SCORE_UPDATED,
                f"Lead score adjusted by {points} based on interaction.",
                entity_id=customer_id, entity_type="customer"
            )
            db.commit()
            logger.info(f"Updated lead score for {customer_id} by {points}")

    def _create_auto_deal(self, customer_id: str, content: str):
        with get_db_session() as db:
            repo = DealRepository(db)
            # Simple check if an open deal already exists (Lead stage)
            # (In a real app, logic would be more sophisticated)
            deals = repo.get_all()
            existing = next((d for d in deals if d.customer_id == customer_id and d.stage == DealStage.LEAD), None)
            
            if not existing:
                deal_data = DealCreate(
                    title=f"AI Generated: {content[:30]}...",
                    description=f"Auto-generated deal based on high-intent inquiry: {content}",
                    amount=0.0,
                    stage=DealStage.LEAD,
                    customer_id=customer_id
                )
                repo.create(deal_data)
                write_audit(
                    db, AuditActionType.DEAL_AUTO_ASSIGNED,
                    f"Autonomous deal created: {deal_data.title}",
                    entity_id=customer_id, entity_type="customer"
                )
                db.commit()
                logger.info(f"Created auto-deal for customer {customer_id}")

    def _create_auto_task(self, customer_id: str, content: str):
         with get_db_session() as db:
            repo = TaskRepository(db)
            task_data = TaskCreate(
                title=f"Follow up: {content[:30]}...",
                description=f"Automated follow-up task triggered by inquiry: {content}",
                is_completed=False,
                due_date=datetime.utcnow() + timedelta(days=1),
                customer_id=customer_id
            )
            repo.create(task_data)
            write_audit(
                db, AuditActionType.NUDGE_TASK_CREATED,
                f"Autonomous follow-up task created: {task_data.title}",
                entity_id=customer_id, entity_type="customer"
            )
            db.commit()
            logger.info(f"Created auto-task for customer {customer_id}")

automation_service = AutomationService()
