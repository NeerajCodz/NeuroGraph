"""Unit tests for memory manager."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestMemoryManager:
    """Tests for MemoryManager class."""

    @pytest.fixture
    def memory_manager(self, mock_settings, mock_neo4j_driver, mock_postgres_driver):
        """Create MemoryManager instance."""
        with patch("src.memory.manager.Neo4jDriver", return_value=mock_neo4j_driver), \
             patch("src.memory.manager.PostgresDriver", return_value=mock_postgres_driver):
            from src.memory.manager import MemoryManager
            
            manager = MemoryManager()
            manager._neo4j = mock_neo4j_driver
            manager._postgres = mock_postgres_driver
            return manager

    @pytest.mark.asyncio
    async def test_remember_personal_layer(self, memory_manager, test_user_id):
        """Test storing a memory in personal layer."""
        memory_manager._postgres.execute = AsyncMock(return_value="INSERT 1")
        memory_manager._neo4j.execute_write = AsyncMock(return_value=[{"id": "node_1"}])
        
        result = await memory_manager.remember(
            content="Test memory content",
            user_id=test_user_id,
            layer="personal",
        )
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_remember_tenant_layer(self, memory_manager, test_user_id, test_tenant_id):
        """Test storing a memory in tenant layer."""
        memory_manager._postgres.execute = AsyncMock(return_value="INSERT 1")
        memory_manager._neo4j.execute_write = AsyncMock(return_value=[{"id": "node_1"}])
        
        result = await memory_manager.remember(
            content="Shared memory content",
            user_id=test_user_id,
            tenant_id=test_tenant_id,
            layer="tenant",
        )
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_remember_global_requires_high_confidence(self, memory_manager, test_user_id):
        """Test that global layer requires high confidence."""
        from src.core.exceptions import LayerAccessError
        
        # Low confidence should fail for global layer
        with pytest.raises(LayerAccessError):
            await memory_manager.remember(
                content="Global memory",
                user_id=test_user_id,
                layer="global",
                confidence=0.5,  # Below 0.85 threshold
            )

    @pytest.mark.asyncio
    async def test_recall_returns_scored_nodes(self, memory_manager, test_user_id):
        """Test recalling memories returns scored nodes."""
        memory_manager._postgres.fetch = AsyncMock(return_value=[
            {"id": "1", "content": "Test", "embedding": [0.1] * 768, "confidence": 0.9},
        ])
        memory_manager._neo4j.execute_read = AsyncMock(return_value=[
            {"n": {"id": "1", "name": "Test"}, "edge_count": 5, "hops": 0},
        ])
        
        with patch("src.memory.manager.GeminiClient") as mock_gemini:
            mock_gemini_instance = AsyncMock()
            mock_gemini_instance.embed = AsyncMock(return_value=[[0.1] * 768])
            mock_gemini.return_value = mock_gemini_instance
            
            result = await memory_manager.recall(
                query="test query",
                user_id=test_user_id,
            )
        
        # Should return a list of scored nodes
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_forget_removes_memory(self, memory_manager, test_user_id):
        """Test forgetting a memory."""
        memory_manager._postgres.execute = AsyncMock(return_value="DELETE 1")
        memory_manager._neo4j.execute_write = AsyncMock(return_value=[])
        
        result = await memory_manager.forget(
            memory_id="node_1",
            user_id=test_user_id,
        )
        
        assert result is True

    @pytest.mark.asyncio
    async def test_search_hybrid(self, memory_manager, test_user_id):
        """Test hybrid search combining vector and graph."""
        memory_manager._postgres.fetch = AsyncMock(return_value=[
            {"id": "1", "content": "Test", "similarity": 0.9},
        ])
        memory_manager._neo4j.execute_read = AsyncMock(return_value=[
            {"n": {"id": "1"}, "edge_count": 5},
        ])
        
        with patch("src.memory.manager.GeminiClient") as mock_gemini:
            mock_gemini_instance = AsyncMock()
            mock_gemini_instance.embed = AsyncMock(return_value=[[0.1] * 768])
            mock_gemini.return_value = mock_gemini_instance
            
            result = await memory_manager.search(
                query="search query",
                user_id=test_user_id,
            )
        
        assert isinstance(result, list)
