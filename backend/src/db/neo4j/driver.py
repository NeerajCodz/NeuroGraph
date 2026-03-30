"""Neo4j database driver and connection management."""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncSession, AsyncTransaction
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import get_settings
from src.core.exceptions import ConnectionError, Neo4jError
from src.core.logging import get_logger

logger = get_logger(__name__)


class Neo4jDriver:
    """Async Neo4j driver with connection pooling."""

    def __init__(self) -> None:
        self._driver: AsyncDriver | None = None
        self._settings = get_settings()

    async def connect(self) -> None:
        """Establish connection to Neo4j."""
        if self._driver is not None:
            return

        try:
            self._driver = AsyncGraphDatabase.driver(
                self._settings.neo4j_uri,
                auth=(
                    self._settings.neo4j_username,
                    self._settings.neo4j_password.get_secret_value(),
                ),
                max_connection_pool_size=self._settings.neo4j_max_connection_pool_size,
            )
            # Verify connectivity
            await self._driver.verify_connectivity()
            logger.info("neo4j_connected", uri=self._settings.neo4j_uri)
        except Exception as e:
            logger.error("neo4j_connection_failed", error=str(e))
            raise ConnectionError(f"Failed to connect to Neo4j: {e}") from e

    async def disconnect(self) -> None:
        """Close Neo4j connection."""
        if self._driver is not None:
            await self._driver.close()
            self._driver = None
            logger.info("neo4j_disconnected")

    @property
    def driver(self) -> AsyncDriver:
        """Get the Neo4j driver instance."""
        if self._driver is None:
            raise ConnectionError("Neo4j driver not initialized. Call connect() first.")
        return self._driver

    @asynccontextmanager
    async def session(self, database: str | None = None) -> AsyncGenerator[AsyncSession, None]:
        """Get a Neo4j session."""
        db = database or self._settings.neo4j_database
        session = self.driver.session(database=db)
        try:
            yield session
        finally:
            await session.close()

    @asynccontextmanager
    async def transaction(
        self, database: str | None = None
    ) -> AsyncGenerator[AsyncTransaction, None]:
        """Get a Neo4j transaction."""
        async with self.session(database) as session:
            tx = await session.begin_transaction()
            try:
                yield tx
                await tx.commit()
            except Exception:
                await tx.rollback()
                raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def execute_read(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        database: str | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a read query with retry logic."""
        try:
            async with self.session(database) as session:
                result = await session.run(query, parameters or {})
                records = await result.data()
                return records
        except Exception as e:
            logger.error("neo4j_read_failed", query=query[:100], error=str(e))
            raise Neo4jError(f"Read query failed: {e}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def execute_write(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        database: str | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a write query with retry logic."""
        try:
            async with self.session(database) as session:
                result = await session.run(query, parameters or {})
                records = await result.data()
                return records
        except Exception as e:
            logger.error("neo4j_write_failed", query=query[:100], error=str(e))
            raise Neo4jError(f"Write query failed: {e}") from e

    async def health_check(self) -> bool:
        """Check if Neo4j connection is healthy."""
        try:
            await self.execute_read("RETURN 1 AS health")
            return True
        except Exception:
            return False


# Global driver instance
_neo4j_driver: Neo4jDriver | None = None


def get_neo4j_driver() -> Neo4jDriver:
    """Get the global Neo4j driver instance."""
    global _neo4j_driver
    if _neo4j_driver is None:
        _neo4j_driver = Neo4jDriver()
    return _neo4j_driver
