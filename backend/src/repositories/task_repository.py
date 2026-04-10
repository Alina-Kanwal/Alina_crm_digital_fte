from typing import List, Optional
from sqlalchemy.orm import Session
from src.models.task import Task
from src.schemas.crm import TaskCreate, TaskUpdate

class TaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Task]:
        return self.db.query(Task).offset(skip).limit(limit).all()

    def get_by_id(self, task_id: str) -> Optional[Task]:
        return self.db.query(Task).filter(Task.id == task_id).first()

    def create(self, task: TaskCreate) -> Task:
        db_task = Task(**task.model_dump())
        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)
        return db_task

    def update(self, task_id: str, task_update: TaskUpdate) -> Optional[Task]:
        db_task = self.get_by_id(task_id)
        if not db_task:
            return None
        
        update_data = task_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_task, key, value)
            
        self.db.commit()
        self.db.refresh(db_task)
        return db_task
