"""Unit tests for PostgreSQL driver."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.db.postgres.driver import PostgresDriver


@pytest.fixture
def postgres_driver(mock_settings):
    """Create PostgreSQL driver instance."""
    return PostgresDriver()


class TestPostgresDriver:
    """Tests for PostgresDriver class."""

    @pytest.mark.asyncio
    async def test_connect_success(self, postgres_driver, mock_settings):
        """Test successful connection."""
        with patch("src.db.postgres.driver.asyncpg.create_pool") as mock_pool:
            mock_pool_instance = AsyncMock()
            mock_pool.return_value = mock_pool_instance
            
            await postgres_driver.connect()
            
            mock_pool.assert_called_once()
            assert postgres_driver._pool is not None

    @pytest.mark.asyncio
    async def test_connect_already_connected(self, postgres_driver, mock_settings):
        """Test connect when already connected."""
        postgres_driver._pool = MagicMock()
        
        await postgres_driver.connect()
        
        # Pool should remain the same
        assert postgres_driver._pool is not None

    @pytest.mark.asyncio
    async def test_disconnect(self, postgres_driver, mock_settings):
        """Test disconnection."""
        mock_pool = AsyncMock()
        postgres_driver._pool = mock_pool
        
        await postgres_driver.disconnect()
        
        mock_pool.close.assert_called_once()
        assert postgres_driver._pool is None

    def test_pool_property_not_initialized(self, postgres_driver, mock_settings):
        """Test pool property raises when not initialized."""
        from src.core.exceptions import ConnectionError
        
        with pytest.raises(ConnectionError):
            _ = postgres_driver.pool

    @pytest.mark.asyncio
    async def test_fetch(self, postgres_driver, mock_settings):
        """Test fetch query."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[{"id": 1, "name": "test"}])
        
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_pool.acquire.return_value.__aexit__.return_value = None
        postgres_driver._pool = mock_pool
        
        result = await postgres_driver.fetch("SELECT * FROM test")
        
        assert result == [{"id": 1, "name": "test"}]

    @pytest.mark.asyncio
    async def test_fetchval(self, postgres_driver, mock_settings):
        """Test fetchval query."""
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=42)
        
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_pool.acquire.return_value.__aexit__.return_value = None
        postgres_driver._pool = mock_pool
        
        result = await postgres_driver.fetchval("SELECT COUNT(*)")
        
        assert result == 42

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, postgres_driver, mock_settings):
        """Test health check when healthy."""
        with patch.object(postgres_driver, "fetchval", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = 1
            
            result = await postgres_driver.health_check()
            
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, postgres_driver, mock_settings):
        """Test health check when unhealthy."""
        with patch.object(postgres_driver, "fetchval", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = Exception("Connection failed")
            
            result = await postgres_driver.health_check()
            
            assert result is False
