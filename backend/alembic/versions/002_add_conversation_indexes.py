"""
Add conversation retrieval indexes
Add optimized indexes for efficient conversation history retrieval and cross-channel lookups.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func

# revision identifiers, used by Alembic.
revision = '002_add_conversation_indexes'
down_revision = '001_initial_models'
branch_labels = None
depends_on = '001_initial_models'


def upgrade():
    """Add indexes for efficient conversation retrieval."""

    # ConversationThread indexes
    # Index for fast thread lookup by thread_id
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_conversation_threads_thread_id
        ON conversation_threads (thread_id)
    """)

    # Index for filtering active conversations
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_conversation_threads_is_active
        ON conversation_threads (is_active)
    """)

    # Index for chronological ordering of conversations
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_conversation_threads_last_activity
        ON conversation_threads (last_activity DESC)
    """)

    # Composite index for customer active conversations (most common query)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_conversation_threads_customer_active_last
        ON conversation_threads (customer_id, is_active, last_activity DESC)
    """)

    # Index for channel history queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_conversation_threads_channel_history
        ON conversation_threads USING GIN (channel_history)
    """)

    # Message indexes
    # Index for timestamp ordering (already exists but ensuring it's optimal)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_messages_timestamp_asc
        ON messages (timestamp ASC)
    """)

    # Composite index for thread message retrieval (most common query)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_messages_thread_timestamp
        ON messages (thread_id, timestamp ASC)
    """)

    # Index for sentiment filtering (for trend analysis)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_messages_sentiment
        ON messages (sentiment)
    """)

    # Composite index for thread/channel filtering
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_messages_thread_channel
        ON messages (thread_id, channel)
    """)

    print("✅ All conversation retrieval indexes added successfully")


def downgrade():
    """Remove conversation retrieval indexes."""

    # Remove ConversationThread indexes
    op.drop_index('ix_conversation_threads_thread_id', table_name='conversation_threads')
    op.drop_index('ix_conversation_threads_is_active', table_name='conversation_threads')
    op.drop_index('ix_conversation_threads_last_activity', table_name='conversation_threads')
    op.drop_index('ix_conversation_threads_customer_active_last', table_name='conversation_threads')
    op.drop_index('ix_conversation_threads_channel_history', table_name='conversation_threads')

    # Remove Message indexes
    op.drop_index('ix_messages_timestamp_asc', table_name='messages')
    op.drop_index('ix_messages_thread_timestamp', table_name='messages')
    op.drop_index('ix_messages_sentiment', table_name='messages')
    op.drop_index('ix_messages_thread_channel', table_name='messages')

    print("⚠️ All conversation retrieval indexes removed")
