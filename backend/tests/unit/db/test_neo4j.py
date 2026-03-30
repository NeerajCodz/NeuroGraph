"""Unit tests for Neo4j driver."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.db.neo4j.driver import Neo4jDriver


@pytest.fixture
def neo4j_driver(mock_settings):
    """Create Neo4j driver instance."""
    return Neo4jDriver()


class TestNeo4jDriver:
    """Tests for Neo4jDriver class."""

    @pytest.mark.asyncio
    async def test_connect_success(self, neo4j_driver, mock_settings):
        """Test successful connection."""
        with patch("src.db.neo4j.driver.AsyncGraphDatabase") as mock_db:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock()
            mock_db.driver.return_value = mock_driver
            
            await neo4j_driver.connect()
            
            mock_db.driver.assert_called_once()
            mock_driver.verify_connectivity.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_already_connected(self, neo4j_driver, mock_settings):
        """Test connect when already connected."""
        neo4j_driver._driver = MagicMock()
        
        await neo4j_driver.connect()
        
        # Should not try to create new connection
        assert neo4j_driver._driver is not None

    @pytest.mark.asyncio
    async def test_disconnect(self, neo4j_driver, mock_settings):
        """Test disconnection."""
        mock_driver = AsyncMock()
        neo4j_driver._driver = mock_driver
        
        await neo4j_driver.disconnect()
        
        mock_driver.close.assert_called_once()
        assert neo4j_driver._driver is None

    @pytest.mark.asyncio
    async def test_disconnect_not_connected(self, neo4j_driver, mock_settings):
        """Test disconnect when not connected."""
        neo4j_driver._driver = None
        
        # Should not raise
        await neo4j_driver.disconnect()

    def test_driver_property_not_initialized(self, neo4j_driver, mock_settings):
        """Test driver property raises when not initialized."""
        from src.core.exceptions import ConnectionError
        
        with pytest.raises(ConnectionError):
            _ = neo4j_driver.driver

    @pytest.mark.asyncio
    async def test_execute_read(self, neo4j_driver, mock_settings):
        """Test read query execution."""
        # Setup mock
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.data = AsyncMock(return_value=[{"count": 1}])
        mock_session.run = AsyncMock(return_value=mock_result)
        mock_session.close = AsyncMock()
        
        mock_driver_instance = MagicMock()
        mock_driver_instance.session.return_value = mock_session
        neo4j_driver._driver = mock_driver_instance
        
        result = await neo4j_driver.execute_read("RETURN 1 AS count")
        
        assert result == [{"count": 1}]

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, neo4j_driver, mock_settings):
        """Test health check when healthy."""
        with patch.object(neo4j_driver, "execute_read", new_callable=AsyncMock) as mock_read:
            mock_read.return_value = [{"health": 1}]
            
            result = await neo4j_driver.health_check()
            
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, neo4j_driver, mock_settings):
        """Test health check when unhealthy."""
        with patch.object(neo4j_driver, "execute_read", new_callable=AsyncMock) as mock_read:
            mock_read.side_effect = Exception("Connection failed")
            
            result = await neo4j_driver.health_check()
            
            assert result is False
