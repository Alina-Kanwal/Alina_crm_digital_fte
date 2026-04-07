"""
Documentation model for storing product guides and FAQs with pgvector embeddings.
"""
from sqlalchemy import Column, String, Text, Index
from pgvector.sqlalchemy import Vector
from src.models.base import BaseModel


class Documentation(BaseModel):
    """
    Knowledge base documentation chunks for AI retrieval.

    Attributes:
        id: UUID primary key (inherited from BaseModel)
        title: Document title
        content: Text content/chunk
        source: Source file or URL
        embedding: pgvector embedding (1536 dim)
        category: Documentation category (billing, technical, etc.)
    """

    __tablename__ = "documentation"

    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(255), nullable=True)
    embedding = Column(Vector(1536), nullable=True)
    category = Column(String(50), index=True, nullable=True)

    # Index for fast similarity search
    # This uses IVFFlat or HNSW in production, but let's just make sure it's indexed
    __table_args__ = (
        Index('idx_doc_category', 'category'),
    )

    def __repr__(self):
        return f"<Documentation(id='{self.id}', title='{self.title[:30]}..')>"
