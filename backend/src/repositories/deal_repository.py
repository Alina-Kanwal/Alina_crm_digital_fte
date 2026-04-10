from typing import List, Optional
from sqlalchemy.orm import Session
from src.models.deal import Deal, DealStage
from src.schemas.crm import DealCreate, DealUpdate

class DealRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Deal]:
        return self.db.query(Deal).offset(skip).limit(limit).all()

    def get_by_id(self, deal_id: str) -> Optional[Deal]:
        return self.db.query(Deal).filter(Deal.id == deal_id).first()

    def create(self, deal: DealCreate) -> Deal:
        db_deal = Deal(**deal.model_dump())
        self.db.add(db_deal)
        self.db.commit()
        self.db.refresh(db_deal)
        return db_deal

    def update(self, deal_id: str, deal_update: DealUpdate) -> Optional[Deal]:
        db_deal = self.get_by_id(deal_id)
        if not db_deal:
            return None
        
        update_data = deal_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_deal, key, value)
            
        self.db.commit()
        self.db.refresh(db_deal)
        return db_deal

    def get_cold_deals(self, stage: DealStage, older_than_days: int) -> List[Deal]:
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(days=older_than_days)
        return self.db.query(Deal).filter(
            Deal.stage == stage,
            Deal.created_at < cutoff
        ).all()
