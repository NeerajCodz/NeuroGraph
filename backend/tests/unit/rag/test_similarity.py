"""Unit tests for similarity module."""

import pytest
import numpy as np


class TestCosineSimilarity:
    """Tests for cosine similarity function."""

    def test_identical_vectors(self):
        """Test similarity of identical vectors is 1.0."""
        from src.rag.similarity import cosine_similarity
        
        vec = np.array([1.0, 2.0, 3.0])
        result = cosine_similarity(vec, vec)
        
        assert abs(result - 1.0) < 0.0001

    def test_orthogonal_vectors(self):
        """Test similarity of orthogonal vectors is 0.0."""
        from src.rag.similarity import cosine_similarity
        
        vec1 = np.array([1.0, 0.0])
        vec2 = np.array([0.0, 1.0])
        result = cosine_similarity(vec1, vec2)
        
        assert abs(result) < 0.0001

    def test_opposite_vectors(self):
        """Test similarity of opposite vectors is -1.0."""
        from src.rag.similarity import cosine_similarity
        
        vec1 = np.array([1.0, 2.0, 3.0])
        vec2 = -vec1
        result = cosine_similarity(vec1, vec2)
        
        assert abs(result + 1.0) < 0.0001

    def test_similar_vectors(self):
        """Test similarity of similar vectors."""
        from src.rag.similarity import cosine_similarity
        
        vec1 = np.array([1.0, 2.0, 3.0])
        vec2 = np.array([1.1, 2.1, 3.1])
        result = cosine_similarity(vec1, vec2)
        
        assert result > 0.99  # Very similar

    def test_zero_vector(self):
        """Test handling of zero vector."""
        from src.rag.similarity import cosine_similarity
        
        vec1 = np.array([1.0, 2.0, 3.0])
        vec2 = np.array([0.0, 0.0, 0.0])
        result = cosine_similarity(vec1, vec2)
        
        assert result == 0.0  # Should handle gracefully


class TestBatchSimilarity:
    """Tests for batch similarity computation."""

    def test_batch_similarity(self):
        """Test batch similarity computation."""
        from src.rag.similarity import batch_cosine_similarity
        
        query = np.array([1.0, 0.0, 0.0])
        vectors = np.array([
            [1.0, 0.0, 0.0],  # Same as query
            [0.0, 1.0, 0.0],  # Orthogonal
            [0.5, 0.5, 0.0],  # Partial similarity
        ])
        
        results = batch_cosine_similarity(query, vectors)
        
        assert len(results) == 3
        assert abs(results[0] - 1.0) < 0.0001
        assert abs(results[1]) < 0.0001
        assert 0.5 < results[2] < 1.0

    def test_empty_batch(self):
        """Test with empty batch."""
        from src.rag.similarity import batch_cosine_similarity
        
        query = np.array([1.0, 0.0, 0.0])
        vectors = np.array([]).reshape(0, 3)
        
        results = batch_cosine_similarity(query, vectors)
        
        assert len(results) == 0


class TestTopKSimilar:
    """Tests for top-k similar retrieval."""

    def test_top_k(self):
        """Test retrieving top-k similar vectors."""
        from src.rag.similarity import top_k_similar
        
        query = np.array([1.0, 0.0, 0.0])
        vectors = np.array([
            [1.0, 0.0, 0.0],
            [0.9, 0.1, 0.0],
            [0.0, 1.0, 0.0],
            [0.5, 0.5, 0.0],
        ])
        
        indices, scores = top_k_similar(query, vectors, k=2)
        
        assert len(indices) == 2
        assert indices[0] == 0  # Most similar
        assert indices[1] == 1  # Second most similar

    def test_top_k_with_threshold(self):
        """Test top-k with similarity threshold."""
        from src.rag.similarity import top_k_similar
        
        query = np.array([1.0, 0.0, 0.0])
        vectors = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],  # Below threshold
            [0.8, 0.2, 0.0],
        ])
        
        indices, scores = top_k_similar(query, vectors, k=3, threshold=0.5)
        
        # Should only return vectors above threshold
        assert 1 not in indices  # Orthogonal vector excluded
