"""Redis driver for caching and message queues."""

import asyncio
from typing import Any

import redis.asyncio as redis
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import get_settings
from src.core.exceptions import ConnectionError, RedisError
from src.core.logging import get_logger

logger = get_logger(__name__)


class RedisDriver:
    """Async Redis driver for caching and pub/sub."""

    def __init__(self) -> None:
        self._client: redis.Redis | None = None
        self._client_loop: asyncio.AbstractEventLoop | None = None
        self._connect_lock = asyncio.Lock()
        self._settings = get_settings()

    async def connect(self) -> None:
        """Establish connection to Redis."""
        current_loop = asyncio.get_running_loop()

        async with self._connect_lock:
            if (
                self._client is not None
                and self._client_loop is current_loop
                and not current_loop.is_closed()
            ):
                return

            if self._client is not None:
                try:
                    await self._client.aclose()
                except Exception as close_error:
                    logger.warning("redis_client_close_failed", error=str(close_error))
                finally:
                    self._client = None
                    self._client_loop = None

            try:
                self._client = redis.from_url(
                    self._settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=self._settings.redis_max_connections,
                )
                # Test connection
                await self._client.ping()
                self._client_loop = current_loop
                logger.info("redis_connected", url=self._settings.redis_url.split("@")[-1])
            except Exception as e:
                logger.error("redis_connection_failed", error=str(e))
                raise ConnectionError(f"Failed to connect to Redis: {e}") from e

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            self._client_loop = None
            logger.info("redis_disconnected")

    @property
    def client(self) -> redis.Redis:
        """Get the Redis client."""
        if self._client is None:
            raise ConnectionError("Redis client not initialized. Call connect() first.")
        return self._client

    async def _get_client(self) -> redis.Redis:
        """Get an initialized Redis client, connecting lazily if needed."""
        current_loop = asyncio.get_running_loop()
        if (
            self._client is None
            or self._client_loop is None
            or self._client_loop is not current_loop
            or current_loop.is_closed()
        ):
            await self.connect()
        return self.client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get(self, key: str) -> str | None:
        """Get a value by key."""
        try:
            client = await self._get_client()
            return await client.get(key)
        except Exception as e:
            raise RedisError(f"Get failed for key {key}: {e}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def set(
        self,
        key: str,
        value: str,
        expire: int | None = None,
    ) -> bool:
        """Set a value with optional expiration in seconds."""
        try:
            client = await self._get_client()
            if expire is not None:
                return await client.set(key, value, ex=expire)
            return await client.set(key, value)
        except Exception as e:
            raise RedisError(f"Set failed for key {key}: {e}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def delete(self, *keys: str) -> int:
        """Delete keys."""
        try:
            client = await self._get_client()
            return await client.delete(*keys)
        except Exception as e:
            raise RedisError(f"Delete failed: {e}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def exists(self, *keys: str) -> int:
        """Check if keys exist."""
        try:
            client = await self._get_client()
            return await client.exists(*keys)
        except Exception as e:
            raise RedisError(f"Exists check failed: {e}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on a key."""
        try:
            client = await self._get_client()
            return await client.expire(key, seconds)
        except Exception as e:
            raise RedisError(f"Expire failed for key {key}: {e}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def hget(self, name: str, key: str) -> str | None:
        """Get a hash field value."""
        try:
            client = await self._get_client()
            return await client.hget(name, key)
        except Exception as e:
            raise RedisError(f"Hget failed: {e}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def hset(
        self,
        name: str,
        key: str | None = None,
        value: str | None = None,
        mapping: dict[str, Any] | None = None,
    ) -> int:
        """Set hash field(s)."""
        try:
            client = await self._get_client()
            if mapping:
                return await client.hset(name, mapping=mapping)
            return await client.hset(name, key, value)
        except Exception as e:
            raise RedisError(f"Hset failed: {e}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def hgetall(self, name: str) -> dict[str, str]:
        """Get all fields in a hash."""
        try:
            client = await self._get_client()
            return await client.hgetall(name)
        except Exception as e:
            raise RedisError(f"Hgetall failed: {e}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def lpush(self, name: str, *values: str) -> int:
        """Push values to the left of a list."""
        try:
            client = await self._get_client()
            return await client.lpush(name, *values)
        except Exception as e:
            raise RedisError(f"Lpush failed: {e}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def rpush(self, name: str, *values: str) -> int:
        """Push values to the right of a list."""
        try:
            client = await self._get_client()
            return await client.rpush(name, *values)
        except Exception as e:
            raise RedisError(f"Rpush failed: {e}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def lpop(self, name: str) -> str | None:
        """Pop from the left of a list."""
        try:
            client = await self._get_client()
            return await client.lpop(name)
        except Exception as e:
            raise RedisError(f"Lpop failed: {e}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def rpop(self, name: str) -> str | None:
        """Pop from the right of a list."""
        try:
            client = await self._get_client()
            return await client.rpop(name)
        except Exception as e:
            raise RedisError(f"Rpop failed: {e}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def lrange(self, name: str, start: int, end: int) -> list[str]:
        """Get a range of values from a list."""
        try:
            client = await self._get_client()
            return await client.lrange(name, start, end)
        except Exception as e:
            raise RedisError(f"Lrange failed: {e}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def publish(self, channel: str, message: str) -> int:
        """Publish a message to a channel."""
        try:
            client = await self._get_client()
            return await client.publish(channel, message)
        except Exception as e:
            raise RedisError(f"Publish failed: {e}") from e

    async def subscribe(self, *channels: str) -> redis.client.PubSub:
        """Subscribe to channels."""
        client = await self._get_client()
        pubsub = client.pubsub()
        await pubsub.subscribe(*channels)
        return pubsub

    async def health_check(self) -> bool:
        """Check if Redis connection is healthy."""
        try:
            client = await self._get_client()
            await client.ping()
            return True
        except Exception:
            return False


# Global driver instance
_redis_driver: RedisDriver | None = None


def get_redis_driver() -> RedisDriver:
    """Get the global Redis driver instance."""
    global _redis_driver
    if _redis_driver is None:
        _redis_driver = RedisDriver()
    return _redis_driver
