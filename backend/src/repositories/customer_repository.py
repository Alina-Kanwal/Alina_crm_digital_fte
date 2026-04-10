from typing import List, Optional
from sqlalchemy.orm import Session
from src.models.customer import Customer
from src.schemas.crm import CustomerCreate

class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Customer]:
        return self.db.query(Customer).offset(skip).limit(limit).all()

    def get_by_id(self, customer_id: str) -> Optional[Customer]:
        return self.db.query(Customer).filter(Customer.id == customer_id).first()

    def get_by_email(self, email: str) -> Optional[Customer]:
        return self.db.query(Customer).filter(Customer.email == email).first()

    def create(self, customer: CustomerCreate) -> Customer:
        db_customer = Customer(**customer.model_dump())
        self.db.add(db_customer)
        self.db.commit()
        self.db.refresh(db_customer)
        return db_customer

    def update_lead_score(self, customer_id: str, points: float) -> Optional[Customer]:
        customer = self.get_by_id(customer_id)
        if customer:
            customer.lead_score = (customer.lead_score or 0) + points
            self.db.commit()
            self.db.refresh(customer)
        return customer
