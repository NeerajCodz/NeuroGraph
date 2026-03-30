"""Unit tests for Redis driver."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.db.redis.driver import RedisDriver


@pytest.fixture
def redis_driver(mock_settings):
    """Create Redis driver instance."""
    return RedisDriver()


class TestRedisDriver:
    """Tests for RedisDriver class."""

    @pytest.mark.asyncio
    async def test_connect_success(self, redis_driver, mock_settings):
        """Test successful connection."""
        with patch("src.db.redis.driver.Redis.from_url") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_redis.return_value = mock_client
            
            await redis_driver.connect()
            
            mock_redis.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect(self, redis_driver, mock_settings):
        """Test disconnection."""
        mock_client = AsyncMock()
        redis_driver._redis = mock_client
        
        await redis_driver.disconnect()
        
        mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_get(self, redis_driver, mock_settings):
        """Test get operation."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=b'{"key": "value"}')
        redis_driver._redis = mock_client
        
        result = await redis_driver.get("test_key")
        
        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_not_found(self, redis_driver, mock_settings):
        """Test get when key not found."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=None)
        redis_driver._redis = mock_client
        
        result = await redis_driver.get("test_key")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_set(self, redis_driver, mock_settings):
        """Test set operation."""
        mock_client = AsyncMock()
        mock_client.set = AsyncMock(return_value=True)
        redis_driver._redis = mock_client
        
        result = await redis_driver.set("test_key", {"key": "value"})
        
        assert result is True

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, redis_driver, mock_settings):
        """Test set with TTL."""
        mock_client = AsyncMock()
        mock_client.set = AsyncMock(return_value=True)
        redis_driver._redis = mock_client
        
        result = await redis_driver.set("test_key", {"key": "value"}, ttl=3600)
        
        assert result is True
        mock_client.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete(self, redis_driver, mock_settings):
        """Test delete operation."""
        mock_client = AsyncMock()
        mock_client.delete = AsyncMock(return_value=1)
        redis_driver._redis = mock_client
        
        result = await redis_driver.delete("test_key")
        
        assert result == 1

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, redis_driver, mock_settings):
        """Test health check when healthy."""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        redis_driver._redis = mock_client
        
        result = await redis_driver.health_check()
        
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, redis_driver, mock_settings):
        """Test health check when unhealthy."""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(side_effect=Exception("Connection failed"))
        redis_driver._redis = mock_client
        
        result = await redis_driver.health_check()
        
        assert result is False
