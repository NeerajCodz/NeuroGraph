"""Unit tests for memory layers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestPersonalLayer:
    """Tests for PersonalLayer class."""

    @pytest.fixture
    def personal_layer(self, mock_settings, mock_neo4j_driver, mock_postgres_driver):
        """Create PersonalLayer instance."""
        from src.memory.layers.personal import PersonalLayer
        
        layer = PersonalLayer(mock_neo4j_driver, mock_postgres_driver)
        return layer

    def test_layer_name(self, personal_layer):
        """Test layer name."""
        assert personal_layer.name == "personal"

    @pytest.mark.asyncio
    async def test_store_memory(self, personal_layer, test_user_id):
        """Test storing memory in personal layer."""
        personal_layer._postgres.execute = AsyncMock(return_value="INSERT 1")
        personal_layer._neo4j.execute_write = AsyncMock(return_value=[{"id": "node_1"}])
        
        result = await personal_layer.store(
            content="Personal memory",
            user_id=test_user_id,
            embedding=[0.1] * 768,
        )
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_search_filters_by_user(self, personal_layer, test_user_id):
        """Test that search filters by user_id."""
        personal_layer._postgres.fetch = AsyncMock(return_value=[])
        
        await personal_layer.search(
            embedding=[0.1] * 768,
            user_id=test_user_id,
        )
        
        # Verify user_id was used in query
        personal_layer._postgres.fetch.assert_called_once()
        call_args = personal_layer._postgres.fetch.call_args
        assert str(test_user_id) in str(call_args)


class TestTenantLayer:
    """Tests for TenantLayer class."""

    @pytest.fixture
    def tenant_layer(self, mock_settings, mock_neo4j_driver, mock_postgres_driver):
        """Create TenantLayer instance."""
        from src.memory.layers.tenant import TenantLayer
        
        layer = TenantLayer(mock_neo4j_driver, mock_postgres_driver)
        return layer

    def test_layer_name(self, tenant_layer):
        """Test layer name."""
        assert tenant_layer.name == "tenant"

    @pytest.mark.asyncio
    async def test_store_requires_tenant_id(self, tenant_layer, test_user_id):
        """Test that storing requires tenant_id."""
        from src.core.exceptions import ValidationError
        
        with pytest.raises(ValidationError):
            await tenant_layer.store(
                content="Tenant memory",
                user_id=test_user_id,
                # Missing tenant_id
                embedding=[0.1] * 768,
            )

    @pytest.mark.asyncio
    async def test_store_with_tenant_id(self, tenant_layer, test_user_id, test_tenant_id):
        """Test storing with valid tenant_id."""
        tenant_layer._postgres.execute = AsyncMock(return_value="INSERT 1")
        tenant_layer._neo4j.execute_write = AsyncMock(return_value=[{"id": "node_1"}])
        
        result = await tenant_layer.store(
            content="Tenant memory",
            user_id=test_user_id,
            tenant_id=test_tenant_id,
            embedding=[0.1] * 768,
        )
        
        assert result is not None


class TestGlobalLayer:
    """Tests for GlobalLayer class."""

    @pytest.fixture
    def global_layer(self, mock_settings, mock_neo4j_driver, mock_postgres_driver):
        """Create GlobalLayer instance."""
        from src.memory.layers.global_layer import GlobalLayer
        
        layer = GlobalLayer(mock_neo4j_driver, mock_postgres_driver)
        return layer

    def test_layer_name(self, global_layer):
        """Test layer name."""
        assert global_layer.name == "global"

    def test_min_confidence(self, global_layer):
        """Test minimum confidence requirement."""
        assert global_layer.min_confidence == 0.85

    @pytest.mark.asyncio
    async def test_store_requires_high_confidence(self, global_layer, test_user_id):
        """Test that storing requires high confidence."""
        from src.core.exceptions import LayerAccessError
        
        with pytest.raises(LayerAccessError):
            await global_layer.store(
                content="Global memory",
                user_id=test_user_id,
                confidence=0.5,  # Below threshold
                embedding=[0.1] * 768,
            )

    @pytest.mark.asyncio
    async def test_store_with_high_confidence(self, global_layer, test_user_id):
        """Test storing with sufficient confidence."""
        global_layer._postgres.execute = AsyncMock(return_value="INSERT 1")
        global_layer._neo4j.execute_write = AsyncMock(return_value=[{"id": "node_1"}])
        
        result = await global_layer.store(
            content="Global memory",
            user_id=test_user_id,
            confidence=0.9,  # Above threshold
            embedding=[0.1] * 768,
        )
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_search_global_memories(self, global_layer, test_user_id):
        """Test searching global memories (no user filter)."""
        global_layer._postgres.fetch = AsyncMock(return_value=[])
        
        await global_layer.search(
            embedding=[0.1] * 768,
            user_id=test_user_id,  # Should not filter by user
        )
        
        # Global layer should not filter by user_id
        global_layer._postgres.fetch.assert_called_once()
