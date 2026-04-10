"""
Unit tests for Customer Identifier Service.
Tests cross-channel customer identification with pgvector embeddings.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import uuid

from src.services.customer_identifier import CustomerIdentifierService
from src.models.customer import Customer


@pytest.fixture
def customer_identifier():
    """Create a CustomerIdentifierService instance for testing."""
    return CustomerIdentifierService()


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    with patch('src.services.customer_identifier.SessionLocal') as mock_session_local:
        session = Mock()
        mock_session_local.return_value = session
        yield session


@pytest.mark.asyncio
async def test_identify_customer_by_email(customer_identifier, mock_db_session):
    """Test customer identification by email address."""
    cust_id = str(uuid.uuid4())
    mock_customer = Customer(
        email='john@example.com',
        first_name='John',
        last_name='Doe'
    )
    mock_customer.id = cust_id
    
    # Mock sqlalchemy query
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_customer

    # Test identification
    normalized_message = {
        'sender': 'john@example.com',
        'body': 'Hello world'
    }
    
    result = await customer_identifier.identify_customer(normalized_message)

    assert result['email'] == 'john@example.com'
    assert result['id'] == cust_id


@pytest.mark.asyncio
async def test_identify_customer_by_phone(customer_identifier, mock_db_session):
    """Test customer identification by phone number."""
    cust_id = str(uuid.uuid4())
    mock_customer = Customer(
        phone='+1234567890',
        first_name='Phone',
        last_name='User',
        email=None
    )
    mock_customer.id = cust_id
    
    # Mock sqlalchemy query
    # Since sender doesn't have '@', only the phone query will be executed
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_customer

    # Test identification
    normalized_message = {
        'sender': '+1234567890',
        'body': 'Hello via WhatsApp'
    }
    
    result = await customer_identifier.identify_customer(normalized_message)

    assert result['phone'] == '+1234567890'
    assert result['id'] == cust_id


@pytest.mark.asyncio
async def test_create_new_customer(customer_identifier, mock_db_session):
    """Test creating a new customer when no match found."""
    # Mock no existing customer found
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    mock_db_session.execute.return_value.first.return_value = None
    
    # Mock generate_embedding
    with patch('src.services.customer_identifier.generate_embedding', new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = [0.1] * 1536
        
        # Test customer creation
        normalized_message = {
            'sender': 'new@example.com',
            'body': 'I am new here',
            'metadata': {'name': 'New User'}
        }
        
        result = await customer_identifier.identify_customer(normalized_message)

        assert 'id' in result
        assert 'new@example.com' in result['email']
        assert mock_db_session.add.called
        assert mock_db_session.commit.called
