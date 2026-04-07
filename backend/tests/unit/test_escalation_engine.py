"""
Unit tests for Escalation Engine.
Tests automatic escalation logic based on predefined rules.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.services.escalation.engine import EscalationEngine
from src.services.escalation.profanity import ProfanityDetector
from src.services.escalation.sensitive_topics import SensitiveTopicDetector
from src.services.escalation.unresolved_tracker import UnresolvedTracker


@pytest.fixture
def escalation_engine():
    """Create an EscalationEngine instance for testing."""
    return EscalationEngine()


@pytest.mark.asyncio
async def test_escalate_pricing_inquiry(escalation_engine):
    """Test escalation for pricing-related inquiries."""
    message = "I need custom pricing for my enterprise account with 1000 users"
    customer_id = 1

    result = await escalation_engine.evaluate_escalation(
        message=message,
        customer_id=customer_id,
        sentiment='neutral'
    )

    assert result['should_escalate'] is True
    assert result['escalation_reason'] == 'pricing_inquiry'
    assert result['priority'] == 'P2'
    assert result['escalation_to'] == 'sales_team'


@pytest.mark.asyncio
async def test_escalate_refund_request(escalation_engine):
    """Test escalation for refund requests."""
    message = "I need a refund for my subscription"
    customer_id = 1

    result = await escalation_engine.evaluate_escalation(
        message=message,
        customer_id=customer_id,
        sentiment='neutral'
    )

    assert result['should_escalate'] is True
    assert result['escalation_reason'] == 'refund_request'
    assert result['priority'] == 'P1'
    assert result['escalation_to'] == 'billing_team'


@pytest.mark.asyncio
async def test_escalate_legal_matter(escalation_engine):
    """Test escalation for legal/compliance matters."""
    message = "I need to review the legal terms and possibly consult legal counsel"
    customer_id = 1

    result = await escalation_engine.evaluate_escalation(
        message=message,
        customer_id=customer_id,
        sentiment='neutral'
    )

    assert result['should_escalate'] is True
    assert result['escalation_reason'] == 'legal_matter'
    assert result['priority'] == 'P1'
    assert result['escalation_to'] == 'legal_team'


@pytest.mark.asyncio
async def test_escalate_profanity(escalation_engine):
    """Test escalation for profanity/abusive language."""
    message = "This is unacceptable you idiots! Fix this damn thing now!"
    customer_id = 1

    result = await escalation_engine.evaluate_escalation(
        message=message,
        customer_id=customer_id,
        sentiment='negative'
    )

    assert result['should_escalate'] is True
    assert result['escalation_reason'] == 'profanity_detected'
    assert result['priority'] == 'P2'
    assert result['escalation_to'] == 'support_supervisor'


@pytest.mark.asyncio
async def test_escalate_repeated_unresolved(escalation_engine):
    """Test escalation for 3+ unresolved interactions."""
    with patch.object(escalation_engine, '_count_unresolved_interactions') as mock_count:
        mock_count.return_value = 3

        message = "I'm still having the same problem"
        customer_id = 1

        result = await escalation_engine.evaluate_escalation(
            message=message,
            customer_id=customer_id,
            sentiment='frustrated'
        )

        assert result['should_escalate'] is True
        assert result['escalation_reason'] == 'repeated_unresolved'
        assert result['unresolved_count'] == 3


@pytest.mark.asyncio
async def test_escalate_consecutive_negative_sentiment(escalation_engine):
    """Test escalation for 2 consecutive negative sentiment interactions."""
    with patch.object(escalation_engine, '_get_recent_sentiment') as mock_sentiment:
        # 2 consecutive negative sentiments
        mock_sentiment.return_value = ['negative', 'negative']

        message = "This is still not working"
        customer_id = 1

        result = await escalation_engine.evaluate_escalation(
            message=message,
            customer_id=customer_id,
            sentiment='negative'
        )

        assert result['should_escalate'] is True
        assert result['escalation_reason'] == 'consecutive_negative_sentiment'


@pytest.mark.asyncio
async def test_no_escalation_for_simple_inquiry(escalation_engine):
    """Test no escalation for simple, resolvable inquiry."""
    message = "How do I connect my Slack integration?"
    customer_id = 1

    result = await escalation_engine.evaluate_escalation(
        message=message,
        customer_id=customer_id,
        sentiment='neutral'
    )

    assert result['should_escalate'] is False
    assert result['escalation_reason'] is None


@pytest.mark.asyncio
async def test_escalation_rate_calculation(escalation_engine):
    """Test calculation of escalation rate percentage."""
    with patch.object(escalation_engine, '_get_total_interactions') as mock_total:
        with patch.object(escalation_engine, '_get_escalated_interactions') as mock_escalated:
            mock_total.return_value = 100
            mock_escalated.return_value = 15  # 15% escalation rate

            rate = await escalation_engine.calculate_escalation_rate()

            assert rate == 15.0


@pytest.mark.asyncio
async def test_escalation_rate_above_threshold(escalation_engine):
    """Test detection of escalation rate above 20% threshold."""
    with patch.object(escalation_engine, '_get_total_interactions') as mock_total:
        with patch.object(escalation_engine, '_get_escalated_interactions') as mock_escalated:
            mock_total.return_value = 100
            mock_escalated.return_value = 25  # 25% - above threshold

            alert = await escalation_engine.check_escalation_rate_alert()

            assert alert['alert_triggered'] is True
            assert alert['escalation_rate'] == 25.0
            assert alert['threshold'] == 20.0


@pytest.mark.asyncio
async def test_escalation_rate_below_threshold(escalation_engine):
    """Test no alert when escalation rate is below 20%."""
    with patch.object(escalation_engine, '_get_total_interactions') as mock_total:
        with patch.object(escalation_engine, '_get_escalated_interactions') as mock_escalated:
            mock_total.return_value = 100
            mock_escalated.return_value = 15  # 15% - below threshold

            alert = await escalation_engine.check_escalation_rate_alert()

            assert alert['alert_triggered'] is False
            assert alert['escalation_rate'] == 15.0


@pytest.mark.asyncio
async def test_create_escalation_ticket(escalation_engine):
    """Test creation of escalation ticket."""
    escalation_data = {
        'customer_id': 1,
        'escalation_reason': 'pricing_inquiry',
        'priority': 'P2',
        'escalation_to': 'sales_team',
        'message': 'Custom pricing request',
        'timestamp': datetime.now()
    }

    with patch.object(escalation_engine, '_create_ticket') as mock_create:
        mock_create.return_value = {'ticket_id': 'ESC-123', 'success': True}

        result = await escalation_engine.create_escalation_ticket(escalation_data)

        assert result['success'] is True
        assert result['ticket_id'] == 'ESC-123'


@pytest.mark.asyncio
async def test_profanity_detection(escalation_engine):
    """Test profanity detection in messages."""
    profane_message = "This is a terrible service you idiots"

    with patch('src.services.escalation.profanity.ProfanityDetector') as mock_detector:
        detector = Mock()
        detector.detect_profanity.return_value = {'has_profanity': True, 'profane_words': ['idiots']}
        mock_detector.return_value = detector

        result = await escalation_engine.evaluate_escalation(
            message=profane_message,
            customer_id=1,
            sentiment='negative'
        )

        assert result['should_escalate'] is True
        assert result['escalation_reason'] == 'profanity_detected'


@pytest.mark.asyncio
async def test_sensitive_topic_detection(escalation_engine):
    """Test detection of sensitive topics."""
    with patch('src.services.escalation.sensitive_topics.SensitiveTopicDetector') as mock_detector:
        detector = Mock()
        detector.detect_sensitive_topics.return_value = {
            'has_sensitive_topic': True,
            'topic': 'refund_request'
        }
        mock_detector.return_value = detector

        result = await escalation_engine.evaluate_escalation(
            message="I want a refund",
            customer_id=1,
            sentiment='neutral'
        )

        assert result['should_escalate'] is True
        assert result['escalation_reason'] == 'refund_request'
