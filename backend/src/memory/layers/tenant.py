"""Tenant (organization) memory layer - shared team/org storage."""

from typing import Any
from uuid import UUID

from src.core.exceptions import MemoryAccessDeniedError
from src.core.logging import get_logger
from src.db.neo4j import get_neo4j_driver
from src.db.postgres import get_postgres_driver
from src.memory.layers.base import MemoryLayer
from src.models.gemini import get_gemini_client

logger = get_logger(__name__)


class TenantLayer(MemoryLayer):
    """Tenant memory layer for organization/team shared data.
    
    Characteristics:
    - Tenant-specific isolation
    - All tenant members can read
    - Write access based on role
    - Shared context within organization
    """

    @property
    def name(self) -> str:
        return "tenant"

    async def can_read(self, user_id: UUID, tenant_id: UUID | None = None) -> bool:
        """User can read if they are a member of the tenant."""
        if tenant_id is None:
            return False
        
        # TODO: Check tenant membership in database
        # For now, assume access if tenant_id is provided
        return True

    async def can_write(self, user_id: UUID, tenant_id: UUID | None = None) -> bool:
        """User can write if they have write permission in tenant."""
        if tenant_id is None:
            return False
        
        # TODO: Check tenant role/permissions
        # For now, assume access if tenant_id is provided
        return True

    async def store(
        self,
        content: str,
        user_id: UUID,
        tenant_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
        confidence: float = 1.0,
    ) -> dict[str, Any]:
        """Store information in tenant layer."""
        if not await self.can_write(user_id, tenant_id):
            raise MemoryAccessDeniedError("No write access to tenant layer")
        
        gemini = get_gemini_client()
        postgres = get_postgres_driver()
        
        from src.db.postgres.operations import PostgresOperations
        from uuid import uuid4
        
        # Generate embedding
        embedding = await gemini.embed(content)
        entities = await gemini.extract_entities(content)
        
        pg_ops = PostgresOperations(postgres)
        node_id = f"mem_tenant_{uuid4().hex[:12]}"
        
        await pg_ops.store_embedding(
            node_id=node_id,
            content=content,
            embedding=embedding[0],
            layer=self.name,
            user_id=user_id,
            tenant_id=tenant_id,
            metadata={
                **(metadata or {}),
                "created_by": str(user_id),
            },
            confidence=confidence,
        )
        
        logger.info(
            "tenant_store",
            user_id=str(user_id),
            tenant_id=str(tenant_id),
            node_id=node_id,
        )
        
        return {
            "id": node_id,
            "content": content,
            "layer": self.name,
            "tenant_id": str(tenant_id),
            "confidence": confidence,
            "entities": entities.get("entities", []),
        }

    async def retrieve(
        self,
        query: str,
        user_id: UUID,
        tenant_id: UUID | None = None,
        limit: int = 20,
        min_confidence: float = 0.5,
    ) -> list[dict[str, Any]]:
        """Retrieve from tenant layer."""
        if not await self.can_read(user_id, tenant_id):
            raise MemoryAccessDeniedError("No read access to tenant layer")
        
        gemini = get_gemini_client()
        postgres = get_postgres_driver()
        
        from src.db.postgres.operations import PostgresOperations
        
        query_embedding = await gemini.embed(query)
        
        pg_ops = PostgresOperations(postgres)
        results = await pg_ops.similarity_search(
            query_embedding=query_embedding[0],
            layer=self.name,
            tenant_id=tenant_id,
            min_confidence=min_confidence,
            limit=limit,
        )
        
        logger.debug(
            "tenant_retrieve",
            user_id=str(user_id),
            tenant_id=str(tenant_id),
            results_count=len(results),
        )
        
        return results

    async def delete(
        self,
        memory_id: str,
        user_id: UUID,
        tenant_id: UUID | None = None,
    ) -> bool:
        """Delete from tenant layer (requires admin role)."""
        # TODO: Check if user has admin role in tenant
        
        postgres = get_postgres_driver()
        from src.db.postgres.operations import PostgresOperations
        
        pg_ops = PostgresOperations(postgres)
        result = await pg_ops.delete_embedding(
            node_id=memory_id,
            layer=self.name,
        )
        
        if result:
            logger.info(
                "tenant_delete",
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                memory_id=memory_id,
            )
        
        return result

    def get_filter_conditions(
        self,
        user_id: UUID,
        tenant_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Get tenant layer filter conditions."""
        return {
            "layer": self.name,
            "tenant_id": tenant_id,
        }
