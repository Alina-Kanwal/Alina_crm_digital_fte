"""
Initial models migration.

Creates all tables for Digital FTE system:
- customers (with pgvector support)
- support_tickets (full lifecycle)
- conversation_threads (cross-channel)
- escalation_rules (automatic triggers)
- sentiment_records (analysis)

Revision ID: 001
Revises:
Create Date: 2026-03-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables with production-grade schema."""
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create customers table
    op.create_table(
        'customers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('phone_number', sa.String(20), nullable=True, index=True),
        sa.Column('session_ids', postgresql.ARRAY(sa.String), default=list),
        sa.Column('embedding', sa.Text, nullable=True),  # pgvector column
        sa.Column('metadata', postgresql.JSON, default=dict),
        sa.Column('is_active', sa.String(10), default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create support_tickets table
    op.create_table(
        'support_tickets',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('customer_id', sa.String(36), sa.ForeignKey('customers.id'), nullable=False, index=True),
        sa.Column('channel', sa.String(50), nullable=False, index=True),
        sa.Column('external_id', sa.String(255), nullable=True, index=True),
        sa.Column('subject', sa.String(500), nullable=True),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ai_response', sa.Text, nullable=True),
        sa.Column('sentiment', sa.String(20), nullable=True),
        sa.Column('confidence_score', sa.Float, nullable=True),
        sa.Column('escalated', sa.String(10), default='false'),
        sa.Column('escalation_reason', sa.String(500), nullable=True),
        sa.Column('resolution_category', sa.String(100), nullable=True),
        sa.Column('metadata', postgresql.JSON, default=dict),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create conversation_threads table
    op.create_table(
        'conversation_threads',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('customer_id', sa.String(36), sa.ForeignKey('customers.id'), nullable=False, index=True),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('started_at', sa.String, nullable=False),
        sa.Column('last_updated_at', sa.String, nullable=False),
        sa.Column('message_count', sa.String, nullable=False),
        sa.Column('channel_history', postgresql.JSON, default=list),
        sa.Column('is_resolved', sa.String(10), default='false'),
        sa.Column('resolution_summary', sa.Text, nullable=True),
        sa.Column('metadata', postgresql.JSON, default=dict),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create escalation_rules table
    op.create_table(
        'escalation_rules',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('trigger_type', sa.String(50), nullable=False, index=True),
        sa.Column('trigger_config', postgresql.JSON, nullable=False, default=dict),
        sa.Column('priority', sa.String, nullable=False),
        sa.Column('is_active', sa.String(10), default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create sentiment_records table
    op.create_table(
        'sentiment_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('ticket_id', sa.String(36), sa.ForeignKey('support_tickets.id'), nullable=False, index=True),
        sa.Column('analyzed_at', sa.String, nullable=False),
        sa.Column('sentiment', sa.String(20), nullable=False, index=True),
        sa.Column('score', sa.Float, nullable=True),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('text_snippet', sa.Text, nullable=True),
        sa.Column('metadata', postgresql.JSON, default=dict),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes for performance
    op.create_index('idx_support_tickets_customer_status', 'support_tickets', ['customer_id', 'escalated'])
    op.create_index('idx_conversation_threads_customer_active', 'conversation_threads', ['customer_id', 'is_resolved'])
    op.create_index('idx_sentiment_tickets_sentiment', 'sentiment_records', ['ticket_id', 'sentiment'])

    # Insert default escalation rules
    from src.models.escalation import DEFAULT_RULES
    for rule in DEFAULT_RULES:
        op.execute(
            sa.insert('escalation_rules').values(**rule)
        )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index('idx_sentiment_tickets_sentiment', table_name='sentiment_records')
    op.drop_index('idx_conversation_threads_customer_active', table_name='conversation_threads')
    op.drop_index('idx_support_tickets_customer_status', table_name='support_tickets')

    op.drop_table('sentiment_records')
    op.drop_table('escalation_rules')
    op.drop_table('conversation_threads')
    op.drop_table('support_tickets')
    op.drop_table('customers')

    op.execute('DROP EXTENSION IF EXISTS vector')
