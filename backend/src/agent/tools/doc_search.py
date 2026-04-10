"""
Custom tool: Knowledge base search for Digital FTE AI Customer Success Agent.
Searches product documentation using the DocumentSearchService (pgvector).
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

async def search_knowledge_base(query: str, max_results: int = 5,
                               min_similarity: float = 0.7) -> List[Dict[str, Any]]:
    """
    Bridge to the DocumentSearchService.
    """
    try:
        from src.services.doc_search import DocumentSearchService
        search_service = DocumentSearchService(relevance_threshold=min_similarity)
        return await search_service.search(query, max_results=max_results)
    except Exception as e:
        logger.error(f"Knowledge search error: {e}")
        return []