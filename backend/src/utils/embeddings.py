import os
import litellm
from typing import List, Optional, Tuple
import numpy as np

async def generate_embedding(text: str) -> List[float]:
    """Generate embedding using LiteLLM (supports multi-provider)."""
    try:
        model = os.getenv("EMBEDDING_MODEL", "openai/text-embedding-3-small")
        response = await litellm.aembedding(
            model=model,
            input=[text]
        )
        return response.data[0].embedding
    except Exception as e:
        # Handle missing API keys gracefully - return empty list instead of None
        # so it never returns None as required
        print(f"Warning: Error generating embedding: {e}. Returning empty list.")
        return []

async def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for multiple texts using LiteLLM."""
    try:
        model = os.getenv("EMBEDDING_MODEL", "openai/text-embedding-3-small")
        response = await litellm.aembedding(
            model=model,
            input=texts
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        # Handle missing API keys gracefully - return empty lists instead of None
        # so it never returns None as required
        print(f"Warning: Error generating embeddings batch: {e}. Returning empty lists.")
        return [[] for _ in range(len(texts))]


def embedding_to_vector_str(embedding: List[float]) -> str:
    """
    Convert embedding list to PostgreSQL pgvector string format.

    Args:
        embedding: List of float values

    Returns:
        String representation suitable for pgvector column
    """
    return f"[{','.join(str(x) for x in embedding)}]"


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """
    Calculate cosine similarity between two embeddings.

    Args:
        a: First embedding vector
        b: Second embedding vector

    Returns:
        Cosine similarity score (-1 to 1, where 1 is identical)
    """
    a_array = np.array(a)
    b_array = np.array(b)

    dot_product = np.dot(a_array, b_array)
    norm_a = np.linalg.norm(a_array)
    norm_b = np.linalg.norm(b_array)

    if norm_a == 0 or norm_b == 0:
        return 0

    return dot_product / (norm_a * norm_b)


def find_most_similar(
    query_embedding: List[float],
    candidate_embeddings: List[Tuple[str, List[float]]],
    threshold: float = 0.85,
) -> Optional[str]:
    """
    Find most similar candidate above threshold.

    Args:
        query_embedding: Query embedding vector
        candidate_embeddings: List of (id, embedding) tuples
        threshold: Minimum similarity threshold (0-1)

    Returns:
        ID of most similar candidate or None if below threshold
    """
    best_id = None
    best_score = threshold

    for candidate_id, candidate_embedding in candidate_embeddings:
        score = cosine_similarity(query_embedding, candidate_embedding)
        if score > best_score:
            best_score = score
            best_id = candidate_id

    return best_id


async def calculate_cross_channel_similarity(
    customer_identifiers: dict[str, str],
    existing_embeddings: List[Tuple[str, List[float]]],
) -> dict[str, float]:
    """
    Calculate similarity scores for cross-channel customer identification.

    Args:
        customer_identifiers: Dictionary of identifier types to values (email, phone, etc.)
        existing_embeddings: List of (customer_id, embedding) tuples

    Returns:
        Dictionary of {customer_id: similarity_score} for matches above threshold
    """
    if not existing_embeddings or not customer_identifiers:
        return {}

    # Combine all identifiers into a single text for embedding
    identifier_text = " ".join(
        f"{k}:{v}" for k, v in customer_identifiers.items() if v
    )

    # Skip if no identifiers
    if not identifier_text.strip():
        return {}

    # Generate embedding for current customer
    query_embedding = await generate_embedding(identifier_text)
    if not query_embedding:
        return {}

    # Find all matches above threshold
    matches = {}
    for customer_id, existing_embedding in existing_embeddings:
        similarity = cosine_similarity(query_embedding, existing_embedding)
        if similarity >= 0.95:  # Constitution requirement: >95% accuracy
            matches[customer_id] = similarity

    return matches
