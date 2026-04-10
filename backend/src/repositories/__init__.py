"""
Data repositories for Digital FTE agent.
"""
from src.repositories.ticket_repository import TicketRepository
from src.repositories.customer_repository import CustomerRepository
from src.repositories.deal_repository import DealRepository
from src.repositories.task_repository import TaskRepository
from src.repositories.user_repository import UserRepository

__all__ = ["TicketRepository", "CustomerRepository", "DealRepository", "TaskRepository", "UserRepository"]