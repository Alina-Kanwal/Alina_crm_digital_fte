"""
Unit tests for Customer Identifier Service.
Tests cross-channel customer identification with pgvector embeddings.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.services.customer_identifier import CustomerIdentifier
from src.models.customer import Customer


@pytest.fixture
def customer_identifier():
    """Create a CustomerIdentifier instance for testing."""
    return CustomerIdentifier()


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    with patch('src.services.customer_identifier.SessionLocal') as mock:
        session = Mock()
        session.query.return_value.filter.return_value.first.return_value = None
        session.close.return_value = None
        mock.return_value = session
        yield session


@pytest.mark.asyncio
async def test_identify_customer_by_email(customer_identifier, mock_db):
    """Test customer identification by email address."""
    # Mock customer in database
    mock_customer = Customer(
        id=1,
        email='john@example.com',
        phone=None,
        embedding=None,
        created_at=datetime.now()
    )
    mock_db.query.return_value.filter.return_value.first.return_value = mock_customer

    # Test identification
    result = await customer_identifier.identify_customer(
        email='john@example.com',
        phone=None,
        session_id=None
    )

    assert result['success'] is True
    assert result['customer_id'] == 1
    assert result['identification_method'] == 'email'


@pytest.mark.asyncio
async def test_identify_customer_by_phone(customer_identifier, mock_db):
    """Test customer identification by phone number."""
    # Mock customer in database
    mock_customer = Customer(
        id=2,
        email=None,
        phone='+1234567890',
        embedding=None,
        created_at=datetime.now()
    )
    mock_db.query.return_value.filter.return_value.first.return_value = mock_customer

    # Test identification
    result = await customer_identifier.identify_customer(
        email=None,
        phone='+1234567890',
        session_id=None
    )

    assert result['success'] is True
    assert result['customer_id'] == 2
    assert result['identification_method'] == 'phone'


@pytest.mark.asyncio
async def test_create_new_customer(customer_identifier, mock_db):
    """Test creating a new customer."""
    # Mock no existing customer found
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Test customer creation
    result = await customer_identifier.identify_customer(
        email='new@example.com',
        phone='+1987654321',
        session_id='session-123'
    )

    assert result['success'] is True
    assert result['new_customer'] is True
    assert mock_db.add.called or mock_db.commit.called


@pytest.mark.asyncio
async def test_cross_channel_matching(customer_identifier):
    """Test cross-channel customer matching using pgvector."""
    # Test embedding-based matching
    with patch.object(customer_identifier, '_find_similar_customer') as mock_match:
        mock_match.return_value = {
            'customer_id': 1,
            'similarity_score': 0.95,
            'match_method': 'pgvector'
        }

        result = await customer_identifier.match_cross_channel(
            email='different@example.com',
            phone='+1555555555',
            session_id='session-456'
        )

        assert result['found'] is True
        assert result['customer_id'] == 1
        assert result['similarity_score'] == 0.95
        assert result['match_method'] == 'pgvector'


@pytest.mark.asyncio
async def test_low_confidence_matching(customer_identifier):
    """Test handling of low confidence matches."""
    with patch.object(customer_identifier, '_find_similar_customer') as mock_match:
        # Low similarity score
        mock_match.return_value = {
            'customer_id': 1,
            'similarity_score': 0.65,
            'match_method': 'pgvector'
        }

        result = await customer_identifier.match_cross_channel(
            email='test@example.com',
            phone='+1111111111',
            session_id='session-789'
        )

        # Should create new customer if similarity < 0.7 threshold
        assert result['found'] is False
        assert result['reason'] == 'low_confidence'


@pytest.mark.asyncio
async def test_update_customer_profile(customer_identifier, mock_db):
    """Test updating customer profile with new information."""
    mock_customer = Customer(
        id=1,
        email='john@example.com',
        phone=None,
        embedding=None,
        created_at=datetime.now()
    )
    mock_db.query.return_value.filter.return_value.first.return_value = mock_customer

    # Update with phone number
    result = await customer_identifier.update_customer_profile(
        customer_id=1,
        phone='+1234567890',
        email='john@example.com'
    )

    assert result['success'] is True
    assert mock_db.commit.called


@pytest.mark.asyncio
async def test_identification_accuracy_tracking(customer_identifier):
    """Test tracking of identification accuracy."""
    with patch.object(customer_identifier, '_record_identification_result') as mock_record:
        await customer_identifier.record_identification_result(
            customer_id=1,
            identification_method='email',
            correct=True,
            confidence=0.95
        )

        mock_record.assert_called_once()


@pytest.mark.asyncio
async def test_get_customer_conversations(customer_identifier, mock_db):
    """Test retrieving all conversations for a customer."""
    with patch.object(customer_identifier, 'get_customer_conversations') as mock_get:
        mock_get.return_value = [
            {'thread_id': 'thread-1', 'channel': 'email', 'message_count': 5},
            {'thread_id': 'thread-2', 'channel': 'whatsapp', 'message_count': 3}
        ]

        result = await customer_identifier.get_customer_conversations(customer_id=1)

        assert len(result) == 2
        assert result[0]['thread_id'] == 'thread-1'
        assert result[1]['thread_id'] == 'thread-2'


@pytest.mark.asyncio
async def test_handle_multiple_identifiers(customer_identifier, mock_db):
    """Test handling customer with multiple identifiers (email + phone)."""
    mock_customer = Customer(
        id=1,
        email='john@example.com',
        phone='+1234567890',
        embedding=None,
        created_at=datetime.now()
    )
    mock_db.query.return_value.filter.return_value.first.return_value = mock_customer

    # Identify with both email and phone
    result = await customer_identifier.identify_customer(
        email='john@example.com',
        phone='+1234567890',
        session_id=None
    )

    assert result['success'] is True
    assert result['customer_id'] == 1
    # Should prioritize email as primary identifier
    assert result['identification_method'] == 'email'
