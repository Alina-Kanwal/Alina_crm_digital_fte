import asyncio
import logging
from datetime import datetime, timedelta
from src.database.connection import get_db_session
from src.models.deal import DealStage
from src.models.audit_log import AuditLog, AuditActionType
from src.repositories import CustomerRepository, DealRepository, TaskRepository, UserRepository
from src.schemas.crm import TaskCreate, DealUpdate

logger = logging.getLogger(__name__)


from src.utils.audit import write_audit


class LivingAgentService:
    """
    The background engine that works 24/7.
    Periodically scans the CRM and takes autonomous actions,
    writing every action to the AuditLog for full traceability.
    """

    def __init__(self, interval_seconds: int = 3600):
        self.interval = interval_seconds
        self._running = False

    async def start_working_247(self):
        self._running = True
        logger.info("Digital FTE Agent started 24/7 autonomous cycle.")

        while self._running:
            try:
                await self._perform_autonomous_review()
            except Exception as e:
                logger.error(f"Error in autonomous cycle: {e}")

            await asyncio.sleep(self.interval)

    def stop(self):
        self._running = False

    async def _perform_autonomous_review(self):
        """
        Core autonomous review: finds cold deals, assigns unowned deals,
        and decays inactive lead scores. Every real action is written to AuditLog.
        """
        logger.info(f"[{datetime.utcnow().isoformat()}] Autonomous review starting...")

        with get_db_session() as db:
            customer_repo = CustomerRepository(db)
            deal_repo = DealRepository(db)
            task_repo = TaskRepository(db)
            user_repo = UserRepository(db)

            # Record cycle start
            write_audit(db, AuditActionType.AGENT_CYCLE_STARTED,
                         "Autonomous review cycle initiated.")

            # ── 1. Nudge cold deals ─────────────────────────────────
            cold_deals = deal_repo.get_cold_deals(
                stage=DealStage.LEAD, older_than_days=3
            )
            nudge_count = 0
            for deal in cold_deals:
                task_data = TaskCreate(
                    title=f"Follow-up required: {deal.title}",
                    description=(
                        "This opportunity has been inactive for 3 days. "
                        "A timely follow-up is recommended."
                    ),
                    customer_id=deal.customer_id,
                    due_date=datetime.utcnow() + timedelta(hours=4),
                )
                task_repo.create(task_data)
                write_audit(
                    db, AuditActionType.NUDGE_TASK_CREATED,
                    f"Created follow-up task for inactive deal '{deal.title}'.",
                    entity_id=str(deal.id), entity_type="deal",
                )
                nudge_count += 1

            if nudge_count:
                logger.info(f"Created {nudge_count} follow-up tasks for cold deals.")

            # ── 2. Auto-assign unowned deals ────────────────────────
            unowned_deals = [d for d in deal_repo.get_all() if d.owner_id is None]
            for deal in unowned_deals:
                best_agent = user_repo.get_agent_with_lowest_load()
                if best_agent:
                    deal_repo.update(deal.id, DealUpdate(owner_id=best_agent.id))
                    write_audit(
                        db, AuditActionType.DEAL_AUTO_ASSIGNED,
                        f"Deal '{deal.title}' assigned to {best_agent.first_name or best_agent.email}.",
                        entity_id=str(deal.id), entity_type="deal",
                    )
                    logger.info(f"Auto-assigned deal {deal.id} → {best_agent.email}")

            # ── 3. Lead score decay ─────────────────────────────────
            active_customers = customer_repo.get_all(limit=1000)
            decayed = 0
            for c in active_customers:
                if c.is_active and (c.lead_score or 0) > 0:
                    customer_repo.update_lead_score(c.id, -1.0)
                    decayed += 1

            if decayed:
                write_audit(
                    db, AuditActionType.LEAD_SCORE_UPDATED,
                    f"Applied minor score decay to {decayed} inactive leads.",
                )

            # ── 4. Cycle complete ───────────────────────────────────
            write_audit(db, AuditActionType.AGENT_CYCLE_COMPLETED,
                         "Autonomous review cycle completed successfully.")
            db.commit()

        logger.info("Autonomous review cycle finished.")


living_agent = LivingAgentService(interval_seconds=15)
