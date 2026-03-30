"""Cosine similarity search utilities."""

from typing import Any

import numpy as np

from src.core.logging import get_logger

logger = get_logger(__name__)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors.
    
    Args:
        a: First vector
        b: Second vector
        
    Returns:
        Cosine similarity (-1 to 1)
    """
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)


def batch_cosine_similarity(query: np.ndarray, candidates: np.ndarray) -> np.ndarray:
    """Calculate cosine similarity between query and multiple candidates.
    
    Args:
        query: Query vector (1D)
        candidates: Candidate matrix (2D, each row is a vector)
        
    Returns:
        Array of similarities
    """
    if candidates.size == 0:
        return np.array([])
    
    # Normalize query
    query_norm = np.linalg.norm(query)
    if query_norm == 0:
        return np.zeros(len(candidates))
    query_normalized = query / query_norm
    
    # Normalize candidates
    candidate_norms = np.linalg.norm(candidates, axis=1, keepdims=True)
    candidate_norms = np.where(candidate_norms == 0, 1, candidate_norms)
    candidates_normalized = candidates / candidate_norms
    
    # Compute similarities
    similarities = np.dot(candidates_normalized, query_normalized)
    
    return similarities


def top_k_similar(
    query: np.ndarray,
    candidates: np.ndarray,
    k: int = 10,
    threshold: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Find top-k most similar candidates to query.
    
    Args:
        query: Query vector
        candidates: Candidate vectors (2D array)
        k: Number of results
        threshold: Minimum similarity threshold
        
    Returns:
        Tuple of (indices, similarities) for top-k results
    """
    if candidates.size == 0:
        return np.array([]), np.array([])
    
    # Calculate all similarities
    similarities = batch_cosine_similarity(query, candidates)
    
    # Filter by threshold
    valid_mask = similarities >= threshold
    valid_indices = np.where(valid_mask)[0]
    valid_similarities = similarities[valid_indices]
    
    # Get top k
    if len(valid_similarities) == 0:
        return np.array([]), np.array([])
    
    k = min(k, len(valid_similarities))
    top_k_idx = np.argsort(valid_similarities)[::-1][:k]
    
    result_indices = valid_indices[top_k_idx]
    result_similarities = valid_similarities[top_k_idx]
    
    return result_indices, result_similarities


class SimilaritySearch:
    """In-memory similarity search (for small datasets or caching)."""

    def __init__(self) -> None:
        self._embeddings: list[np.ndarray] = []
        self._metadata: list[dict[str, Any]] = []

    def add(self, embedding: np.ndarray, metadata: dict[str, Any]) -> int:
        """Add an embedding with metadata.
        
        Args:
            embedding: Vector embedding
            metadata: Associated metadata
            
        Returns:
            Index of added item
        """
        self._embeddings.append(embedding)
        self._metadata.append(metadata)
        return len(self._embeddings) - 1

    def add_batch(
        self,
        embeddings: np.ndarray,
        metadata_list: list[dict[str, Any]],
    ) -> None:
        """Add multiple embeddings with metadata.
        
        Args:
            embeddings: 2D array of embeddings
            metadata_list: List of metadata dicts
        """
        for embedding, metadata in zip(embeddings, metadata_list):
            self.add(embedding, metadata)

    def search(
        self,
        query: np.ndarray,
        k: int = 10,
        threshold: float = 0.0,
    ) -> list[tuple[dict[str, Any], float]]:
        """Search for most similar items.
        
        Args:
            query: Query embedding
            k: Number of results
            threshold: Minimum similarity threshold
            
        Returns:
            List of (metadata, similarity) tuples
        """
        if not self._embeddings:
            return []
        
        embeddings_matrix = np.array(self._embeddings)
        similarities = batch_cosine_similarity(query, embeddings_matrix)
        
        # Filter by threshold
        valid_indices = np.where(similarities >= threshold)[0]
        valid_similarities = similarities[valid_indices]
        
        # Sort by similarity (descending)
        sorted_indices = np.argsort(valid_similarities)[::-1][:k]
        
        results = []
        for idx in sorted_indices:
            original_idx = valid_indices[idx]
            metadata = self._metadata[original_idx].copy()
            metadata["similarity"] = float(valid_similarities[idx])
            results.append((metadata, float(valid_similarities[idx])))
        
        return results

    def clear(self) -> None:
        """Clear all stored embeddings."""
        self._embeddings.clear()
        self._metadata.clear()

    def __len__(self) -> int:
        return len(self._embeddings)
