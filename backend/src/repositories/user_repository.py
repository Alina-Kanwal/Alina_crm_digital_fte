from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.models.user import User, UserRole
from src.models.deal import Deal

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.db.query(User).offset(skip).limit(limit).all()

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_active_agents(self) -> List[User]:
        return self.db.query(User).filter(
            User.role == UserRole.AGENT,
            User.is_active == True
        ).all()

    def get_agent_with_lowest_load(self) -> Optional[User]:
        """
        Finds the agent with the fewest open deals assigned.
        """
        agents = self.get_active_agents()
        if not agents:
            return None
        
        # Count open deals for each agent
        agent_loads = {}
        for agent in agents:
            count = self.db.query(func.count(Deal.id)).filter(
                Deal.owner_id == agent.id
            ).scalar()
            agent_loads[agent] = count
            
        if not agent_loads:
            return agents[0] if agents else None
            
        # Return agent with minimum count
        return min(agent_loads, key=agent_loads.get)
