"""
Product documentation search service using pgvector.
Implements semantic search over product documentation using PostgreSQL pgvector extension.
"""
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from src.services.database import SessionLocal
from src.models.documentation import Documentation
from src.services.cache_service import get_cache_service
from src.utils.embeddings import generate_embedding, cosine_similarity
from sqlalchemy import select, func, text

logger = logging.getLogger(__name__)


class DocumentSearchService:
    """Service for semantic similarity search over knowledge base documents."""

    def __init__(self, relevance_threshold: float = 0.5):
        """
        Initialize the documentation search service.

        Args:
            relevance_threshold: Minimum cosine similarity score (0.0 to 1.0)
        """
        self.relevance_threshold = relevance_threshold
        self.cache = get_cache_service()
        logger.info(f"Document search service initialized (relevance_threshold={relevance_threshold})")

    async def search(self, query: str, max_results: int = 5) -> List[Dict[ Any, Any]]:
        """
        Search product documentation using high-performance pgvector semantic search.
        Uses native PostgreSQL <=> operator for cosine similarity at the database level.
        """
        logger.debug(f"Searching documentation for: '{query}'")
        
        # 0. Check cache first
        cache_key = f"doc_search:{hash(query)}:{max_results}"
        try:
            cached_results = await self.cache.get(cache_key)
            if cached_results:
                logger.debug(f"Returning cached search results for: '{query}'")
                return cached_results
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")

        # 1. Generate embedding for query
        query_embedding = await generate_embedding(query)
        if not query_embedding:
            logger.error("Failed to generate embedding for query")
            return []

        db = SessionLocal()
        try:
            # 2. Query documentation using pgvector cosine distance: <=> operator
            # (1 - distance) = cosine similarity
            # We use the native pgvector <=> operator for maximum performance.
            
            # Convert embedding to pgvector string format: '[v1, v2, ...]'
            from src.utils.embeddings import embedding_to_vector_str
            vector_str = embedding_to_vector_str(query_embedding)
            
            # Construct the query. pgvector's <=> is cosine distance.
            # 1 - (embedding <=> vector) is cosine similarity.
            stmt = text(f"""
                SELECT id, title, content, source, category, 
                       (1 - (embedding <=> :query_vec)) as similarity
                FROM documentation
                WHERE (1 - (embedding <=> :query_vec)) >= :threshold
                ORDER BY similarity DESC
                LIMIT :limit
            """)
            
            result = db.execute(stmt, {
                "query_vec": vector_str,
                "threshold": self.relevance_threshold,
                "limit": max_results
            })
            
            results = []
            for row in result:
                results.append({
                    "id": str(row[0]),
                    "title": row[1],
                    "content": row[2],
                    "source": row[3],
                    "category": row[4],
                    "score": float(row[5])
                })

            if not results:
                logger.warning("No documentation matches found via pgvector search")
                return self._get_database_keyword_search(query, max_results)

            # Store in cache
            try:
                await self.cache.set(cache_key, results, expire_seconds=3600)
            except Exception as e:
                logger.warning(f"Cache storage failed: {e}")
                
            logger.info(f"Knowledge search found {len(results)} relevant documents via SQL pgvector search")
            return results

        except Exception as e:
            logger.error(f"Database pgvector search failed: {e}. Falling back to keyword search.")
            return self._get_database_keyword_search(query, max_results)
        finally:
            db.close()

    def _get_database_keyword_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Fallback to real database keyword search if semantic search fails."""
        logger.debug(f"Falling back to database keyword search for: '{query}'")
        db = SessionLocal()
        try:
            # Simple keyword match using ILIKE
            query_word = f"%{query}%"
            stmt = select(Documentation).where(
                (Documentation.title.ilike(query_word)) | 
                (Documentation.content.ilike(query_word))
            ).limit(max_results)
            
            result = db.execute(stmt).scalars().all()
            
            return [
                {
                    "id": str(doc.id),
                    "title": doc.title,
                    "content": doc.content,
                    "source": doc.source,
                    "category": doc.category,
                    "score": 0.5  # Lower confidence for keyword match
                }
                for doc in result
            ]
        except Exception as e:
            logger.error(f"Keyword search also failed: {e}")
            return []
        finally:
            db.close()

    async def add_document(self, title: str, content: str, category: str = "general", source: str = None) -> bool:
        """
        Produce a new record in knowledge base with generated embedding.

        Args:
            title: Document title
            content: Document text content
            category: Document category
            source: Reference source

        Returns:
            True if successful
        """
        logger.info(f"Adding document to KB: '{title}'")
        
        embedding = await generate_embedding(content)
        if not embedding:
            logger.warning(f"Failed to generate embedding for document: {title}. Doc will still be available via keyword search.")

        db = SessionLocal()
        try:
            new_doc = Documentation(
                title=title,
                content=content,
                category=category,
                source=source,
                embedding=embedding
            )
            db.add(new_doc)
            db.commit()
            
            # 4. Invalidate search cache
            try:
                await self.cache.clear()
                logger.info("Documentation search cache cleared (new content added)")
            except Exception as e:
                logger.warning(f"Cache invalidation failed: {e}")
                
            return True
        except Exception as e:
            logger.error(f"Error adding document to DB: {e}")
            db.rollback()
            return False
        finally:
            db.close()