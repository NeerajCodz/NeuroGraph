"""PostgreSQL database driver with pgvector support."""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import asyncpg
from pgvector.asyncpg import register_vector
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import get_settings
from src.core.exceptions import ConnectionError, PostgresError
from src.core.logging import get_logger

logger = get_logger(__name__)


class PostgresDriver:
    """Async PostgreSQL driver with connection pooling and pgvector support."""

    def __init__(self) -> None:
        self._pool: asyncpg.Pool | None = None
        self._pool_loop: asyncio.AbstractEventLoop | None = None
        self._connect_lock = asyncio.Lock()
        self._settings = get_settings()

    async def connect(self) -> None:
        """Establish connection pool to PostgreSQL."""
        current_loop = asyncio.get_running_loop()

        async with self._connect_lock:
            if (
                self._pool is not None
                and self._pool_loop is current_loop
                and not current_loop.is_closed()
            ):
                return

            if self._pool is not None:
                try:
                    await self._pool.close()
                except Exception as close_error:
                    logger.warning("postgres_pool_close_failed", error=str(close_error))
                finally:
                    self._pool = None
                    self._pool_loop = None

            try:
                self._pool = await asyncpg.create_pool(
                    host=self._settings.postgres_host,
                    port=self._settings.postgres_port,
                    user=self._settings.postgres_user,
                    password=self._settings.postgres_password.get_secret_value(),
                    database=self._settings.postgres_db,
                    min_size=self._settings.postgres_min_pool_size,
                    max_size=self._settings.postgres_max_pool_size,
                    init=self._init_connection,
                )
                self._pool_loop = current_loop
                logger.info(
                    "postgres_connected",
                    host=self._settings.postgres_host,
                    database=self._settings.postgres_db,
                )
            except Exception as e:
                logger.error("postgres_connection_failed", error=str(e))
                raise ConnectionError(f"Failed to connect to PostgreSQL: {e}") from e

    async def _init_connection(self, conn: asyncpg.Connection) -> None:
        """Initialize connection with pgvector extension."""
        await register_vector(conn)

    async def disconnect(self) -> None:
        """Close PostgreSQL connection pool."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            self._pool_loop = None
            logger.info("postgres_disconnected")

    @property
    def pool(self) -> asyncpg.Pool:
        """Get the connection pool."""
        if self._pool is None:
            raise ConnectionError("PostgreSQL pool not initialized. Call connect() first.")
        return self._pool

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Get a connection from the pool."""
        current_loop = asyncio.get_running_loop()
        if (
            self._pool is None
            or self._pool_loop is None
            or self._pool_loop is not current_loop
            or current_loop.is_closed()
        ):
            await self.connect()
        async with self.pool.acquire() as conn:
            yield conn

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Get a connection with a transaction."""
        async with self.connection() as conn:
            async with conn.transaction():
                yield conn

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def execute(
        self,
        query: str,
        *args: Any,
    ) -> str:
        """Execute a query without returning results."""
        try:
            async with self.connection() as conn:
                return await conn.execute(query, *args)
        except Exception as e:
            logger.error("postgres_execute_failed", query=query[:100], error=str(e))
            raise PostgresError(f"Query execution failed: {e}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def fetch(
        self,
        query: str,
        *args: Any,
    ) -> list[asyncpg.Record]:
        """Execute a query and fetch all results."""
        try:
            async with self.connection() as conn:
                return await conn.fetch(query, *args)
        except Exception as e:
            logger.error("postgres_fetch_failed", query=query[:100], error=str(e))
            raise PostgresError(f"Query fetch failed: {e}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def fetchrow(
        self,
        query: str,
        *args: Any,
    ) -> asyncpg.Record | None:
        """Execute a query and fetch a single row."""
        try:
            async with self.connection() as conn:
                return await conn.fetchrow(query, *args)
        except Exception as e:
            logger.error("postgres_fetchrow_failed", query=query[:100], error=str(e))
            raise PostgresError(f"Query fetchrow failed: {e}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def fetchval(
        self,
        query: str,
        *args: Any,
    ) -> Any:
        """Execute a query and fetch a single value."""
        try:
            async with self.connection() as conn:
                return await conn.fetchval(query, *args)
        except Exception as e:
            logger.error("postgres_fetchval_failed", query=query[:100], error=str(e))
            raise PostgresError(f"Query fetchval failed: {e}") from e

    async def health_check(self) -> bool:
        """Check if PostgreSQL connection is healthy."""
        try:
            await self.fetchval("SELECT 1")
            return True
        except Exception:
            return False


# Global driver instance
_postgres_driver: PostgresDriver | None = None


def get_postgres_driver() -> PostgresDriver:
    """Get the global PostgreSQL driver instance."""
    global _postgres_driver
    if _postgres_driver is None:
        _postgres_driver = PostgresDriver()
    return _postgres_driver
