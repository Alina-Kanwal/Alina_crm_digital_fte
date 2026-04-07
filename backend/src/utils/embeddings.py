"""
pgvector embedding generation and similarity search utilities.

This module provides functions for generating embeddings using OpenAI
and performing similarity search with PostgreSQL pgvector extension.
"""

import os
from typing import List, Optional, Tuple
import numpy as np

# OpenAI client for embeddings
try:
    from openai import AsyncOpenAI, OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None
    OpenAI = None

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSIONS = 1536


def get_openai_client() -> Optional[OpenAI]:
    """
    Get synchronous OpenAI client.
    """
    if not OPENAI_AVAILABLE or not OPENAI_API_KEY:
        return None
    return OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)


async def get_async_openai_client() -> Optional[AsyncOpenAI]:
    """
    Get asynchronous OpenAI client.
    """
    if not OPENAI_AVAILABLE or not OPENAI_API_KEY:
        return None
    return AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)


async def generate_embedding(text: str) -> Optional[List[float]]:
    """
    Generate embedding for text using OpenAI.

    Args:
        text: Text to generate embedding for

    Returns:
        List of float values representing the embedding, or None if failed
    """
    client = await get_async_openai_client()
    if not client:
        return None

    try:
        response = await client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None


async def generate_embeddings_batch(texts: List[str]) -> List[Optional[List[float]]]:
    """
    Generate embeddings for multiple texts.

    Args:
        texts: List of texts to generate embeddings for

    Returns:
        List of embeddings (or None for failed generations)
    """
    client = await get_async_openai_client()
    if not client:
        return [None] * len(texts)

    try:
        response = await client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts,
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        print(f"Error generating embeddings batch: {e}")
        return [None] * len(texts)


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
