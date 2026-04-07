"""
Pytest configuration and fixtures for Digital FTE Agent tests.

Handles test database setup, fixtures, and test configuration.
"""

import pytest
import asyncio
import os
import sys
from typing import AsyncGenerator, Generator
from datetime import datetime, timedelta
import random
import string

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from src.models.base import Base  # Use the correct Base from models.base
from src.models.customer import Customer
from src.models.support_ticket import SupportTicket
from src.models.conversation_thread import ConversationThread
from src.models.sentiment_record import SentimentRecord
from src.models.escalation import EscalationRule
from src.models.message import Message


# Test database configuration
TEST_DATABASE_URL = "sqlite:///:memory:"

# Import all models to ensure they are registered with SQLAlchemy
from src.models.customer import Customer
from src.models.support_ticket import SupportTicket
from src.models.conversation_thread import ConversationThread
from src.models.sentiment_record import SentimentRecord
from src.models.escalation import EscalationRule
from src.models.message import Message


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    return engine


@pytest.fixture(scope="function")
def test_db(test_engine) -> Generator[Session, None, None]:
    """Create test database session with fresh tables for each test."""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def test_customer(test_db: Session) -> Customer:
    """Create a test customer."""
    customer = Customer(
        email="test@example.com",
        phone="+1234567890",
        first_name="Test",
        last_name="User",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    test_db.add(customer)
    test_db.commit()
    test_db.refresh(customer)
    return customer


@pytest.fixture(scope="function")
def test_ticket(test_db: Session, test_customer: Customer) -> SupportTicket:
    """Create a test support ticket."""
    ticket = SupportTicket(
        customer_id=test_customer.id,
        channel="email",
        external_id="test-ext-123",
        subject="Test Subject",
        content="Test content",
        received_at=datetime.now(),
        sentiment="neutral",
        confidence_score=0.85,
        escalated=False,
        status="open",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    test_db.add(ticket)
    test_db.commit()
    test_db.refresh(ticket)
    return ticket


@pytest.fixture(scope="function")
def test_conversation(test_db: Session, test_customer: Customer) -> ConversationThread:
    """Create a test conversation thread."""
    conversation = ConversationThread(
        customer_id=test_customer.id,
        channel="email",
        status="active",
        subject="Test Conversation",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    test_db.add(conversation)
    test_db.commit()
    test_db.refresh(conversation)
    return conversation


@pytest.fixture(scope="function")
def sample_tickets_data(test_db: Session, test_customer: Customer) -> list:
    """Create sample ticket data for testing."""
    tickets = []

    # Create 20 test tickets with various statuses
    for i in range(20):
        is_escalated = random.random() < 0.15  # 15% escalation rate
        ticket = SupportTicket(
            customer_id=test_customer.id,
            channel=random.choice(["email", "whatsapp", "webform"]),
            external_id=f"ext-{i}",
            subject=f"Test Subject {i}",
            content=f"Test content {i}",
            received_at=datetime.now() - timedelta(hours=random.randint(1, 48)),
            responded_at=datetime.now() - timedelta(hours=random.randint(0, 47)) if random.random() > 0.2 else None,
            resolved_at=datetime.now() - timedelta(hours=random.randint(0, 46)) if random.random() > 0.5 and is_escalated == False else None,
            sentiment=random.choice(["positive", "neutral", "negative"]),
            confidence_score=random.uniform(0.6, 0.95),
            escalated=is_escalated,
            escalation_reason=random.choice(["pricing", "refund", "profanity", None]) if is_escalated else None,
            status=random.choice(["open", "in_progress", "waiting_customer", "resolved", "closed", "escalated"]),
            created_at=datetime.now() - timedelta(hours=random.randint(1, 48)),
            updated_at=datetime.now() - timedelta(hours=random.randint(0, 47))
        )
        tickets.append(ticket)
        test_db.add(ticket)

    test_db.commit()
    return tickets


@pytest.fixture(scope="function")
def sample_multi_channel_data(test_db: Session) -> dict:
    """Create sample multi-channel customer data."""
    customers = []

    # Create customers with different channel usage patterns
    for i in range(10):
        # Multi-channel customers (70%)
        if random.random() < 0.7:
            channels = ["email"]
            if random.random() < 0.7:
                channels.append("whatsapp")
            if random.random() < 0.5:
                channels.append("webform")
        else:
            # Single-channel customers (30%)
            channels = [random.choice(["email", "whatsapp", "webform"])]

        customer = Customer(
            email=f"customer{i}@example.com",
            phone=f"+12345678{i:02d}",
            first_name=f"Customer{i}",
            last_name=f"Test{i}",
            created_at=datetime.now() - timedelta(days=random.randint(1, 30)),
            updated_at=datetime.now()
        )
        test_db.add(customer)
        customers.append(customer)

        # Create conversations for each channel
        for channel in channels:
            conversation = ConversationThread(
                customer_id=customer.id,
                channel=channel,
                status=random.choice(["active", "closed"]),
                subject=f"{channel} conversation",
                created_at=datetime.now() - timedelta(days=random.randint(1, 15)),
                updated_at=datetime.now()
            )
            test_db.add(conversation)

            # Create messages for each conversation
            for msg_num in range(random.randint(1, 5)):
                message = Message(
                    conversation_id=conversation.id,
                    direction=random.choice(["incoming", "outgoing"]),
                    content=f"Message {msg_num} from {channel}",
                    sentiment=random.choice(["positive", "neutral", "negative"]),
                    timestamp=datetime.now() - timedelta(hours=random.randint(1, 100))
                )
                test_db.add(message)

    test_db.commit()

    return {
        'customers': customers,
        'total_customers': len(customers),
        'multi_channel_count': sum(1 for c in customers if len([conv for conv in test_db.query(ConversationThread).filter(
            ConversationThread.customer_id == c.id
        ).distinct(ConversationThread.channel).all()]) > 1)
    }


# Async fixtures for async tests
@pytest.fixture(scope="function")
async def async_test_db() -> AsyncGenerator[Session, None]:
    """Create async test database session."""
    # For now, use sync database - in production would use asyncpg
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def generate_test_email() -> str:
    """Generate a random test email address."""
    return f"test-{random.randint(1000, 9999)}@example.com"


def generate_test_phone() -> str:
    """Generate a random test phone number."""
    return f"+1{random.randint(200, 999)}{random.randint(200, 999)}{random.randint(1000, 9999)}"


def generate_test_message() -> str:
    """Generate a random test message."""
    messages = [
        "I need help with my account",
        "How do I reset my password?",
        "What are your pricing plans?",
        "I want to cancel my subscription",
        "Your service is not working",
        "Great job on the new feature!",
        "I need a refund",
        "When will this be fixed?",
        "This is ridiculous!",
        "Thank you for your help"
    ]
    return random.choice(messages)


# Configuration for pytest
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "chaos: marks tests as chaos tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add markers based on test location
        if "tests/integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "tests/e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "tests/chaos" in str(item.fspath):
            item.add_marker(pytest.mark.chaos)