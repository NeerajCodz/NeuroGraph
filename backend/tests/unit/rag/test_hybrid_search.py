"""Unit tests for hybrid search module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np


class TestHybridSearch:
    """Tests for HybridSearch class."""

    @pytest.fixture
    def hybrid_search(self, mock_settings, mock_neo4j_driver, mock_postgres_driver):
        """Create HybridSearch instance."""
        from src.rag.hybrid_search import HybridSearch
        
        search = HybridSearch(mock_neo4j_driver, mock_postgres_driver)
        return search

    @pytest.mark.asyncio
    async def test_vector_search(self, hybrid_search, sample_embedding):
        """Test vector search component."""
        hybrid_search._postgres.fetch = AsyncMock(return_value=[
            {"id": "1", "content": "Test", "similarity": 0.9},
            {"id": "2", "content": "Test 2", "similarity": 0.8},
        ])
        
        results = await hybrid_search._vector_search(
            embedding=sample_embedding.tolist(),
            user_id="user_1",
            limit=10,
        )
        
        assert len(results) == 2
        assert results[0]["similarity"] > results[1]["similarity"]

    @pytest.mark.asyncio
    async def test_graph_traversal(self, hybrid_search):
        """Test graph traversal component."""
        hybrid_search._neo4j.execute_read = AsyncMock(return_value=[
            {"n": {"id": "1", "name": "Node 1"}, "edge_count": 5, "hops": 0},
            {"n": {"id": "2", "name": "Node 2"}, "edge_count": 3, "hops": 1},
        ])
        
        results = await hybrid_search._graph_traversal(
            seed_nodes=["1"],
            max_hops=3,
        )
        
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_hybrid_search_combines_results(self, hybrid_search, sample_embedding):
        """Test that hybrid search combines vector and graph results."""
        # Mock vector search
        hybrid_search._postgres.fetch = AsyncMock(return_value=[
            {"id": "1", "content": "Test", "similarity": 0.9},
        ])
        
        # Mock graph traversal
        hybrid_search._neo4j.execute_read = AsyncMock(return_value=[
            {"n": {"id": "1", "name": "Node 1"}, "edge_count": 5, "hops": 0},
            {"n": {"id": "2", "name": "Node 2"}, "edge_count": 3, "hops": 1},
        ])
        
        results = await hybrid_search.search(
            embedding=sample_embedding.tolist(),
            user_id="user_1",
            limit=10,
        )
        
        # Should have combined results
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_hybrid_search_deduplicates(self, hybrid_search, sample_embedding):
        """Test that results are deduplicated."""
        # Same node in both results
        hybrid_search._postgres.fetch = AsyncMock(return_value=[
            {"id": "1", "content": "Test", "similarity": 0.9},
        ])
        
        hybrid_search._neo4j.execute_read = AsyncMock(return_value=[
            {"n": {"id": "1", "name": "Node 1"}, "edge_count": 5, "hops": 0},
        ])
        
        results = await hybrid_search.search(
            embedding=sample_embedding.tolist(),
            user_id="user_1",
            limit=10,
        )
        
        # Should not have duplicates
        ids = [r.get("id") or r.get("node_id") for r in results]
        assert len(ids) == len(set(ids))

    @pytest.mark.asyncio
    async def test_hybrid_search_with_layer_filter(self, hybrid_search, sample_embedding):
        """Test hybrid search with layer filter."""
        hybrid_search._postgres.fetch = AsyncMock(return_value=[])
        hybrid_search._neo4j.execute_read = AsyncMock(return_value=[])
        
        await hybrid_search.search(
            embedding=sample_embedding.tolist(),
            user_id="user_1",
            layer="personal",
            limit=10,
        )
        
        # Verify layer was passed to vector search
        call_args = str(hybrid_search._postgres.fetch.call_args)
        assert "personal" in call_args

    @pytest.mark.asyncio
    async def test_reasoning_paths(self, hybrid_search):
        """Test getting reasoning paths between nodes."""
        hybrid_search._neo4j.execute_read = AsyncMock(return_value=[
            {
                "path": ["A", "B", "C"],
                "reasons": ["connects to", "related to"],
                "confidences": [0.9, 0.8],
            },
        ])
        
        paths = await hybrid_search.get_reasoning_paths(
            start_node="A",
            end_node="C",
        )
        
        assert len(paths) >= 1
