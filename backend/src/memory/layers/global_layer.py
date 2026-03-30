"""Global memory layer - high-confidence shared knowledge."""

from typing import Any
from uuid import UUID

from src.core.config import get_settings
from src.core.exceptions import MemoryAccessDeniedError
from src.core.logging import get_logger
from src.db.neo4j import get_neo4j_driver
from src.db.postgres import get_postgres_driver
from src.memory.layers.base import MemoryLayer
from src.models.gemini import get_gemini_client

logger = get_logger(__name__)

# Minimum confidence required for global memory writes
GLOBAL_WRITE_CONFIDENCE_THRESHOLD = 0.85


class GlobalLayer(MemoryLayer):
    """Global memory layer for high-confidence shared knowledge.
    
    Characteristics:
    - Accessible to all users (read-only for most)
    - Write requires high confidence (>0.85)
    - Contains verified, trusted information
    - Cross-user knowledge sharing
    """

    @property
    def name(self) -> str:
        return "global"

    async def can_read(self, user_id: UUID, tenant_id: UUID | None = None) -> bool:
        """All authenticated users can read global layer."""
        return True

    async def can_write(self, user_id: UUID, tenant_id: UUID | None = None) -> bool:
        """Write requires special permissions.
        
        In practice, writes to global layer typically come from:
        - System processes with high confidence facts
        - Admin users
        - Automated knowledge extraction with confidence > threshold
        """
        # TODO: Check if user has global write permission
        # For now, we'll rely on confidence threshold check at write time
        return True

    async def store(
        self,
        content: str,
        user_id: UUID,
        tenant_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
        confidence: float = 1.0,
    ) -> dict[str, Any]:
        """Store in global layer (requires high confidence)."""
        if confidence < GLOBAL_WRITE_CONFIDENCE_THRESHOLD:
            raise MemoryAccessDeniedError(
                f"Global layer requires confidence >= {GLOBAL_WRITE_CONFIDENCE_THRESHOLD}, "
                f"got {confidence}"
            )
        
        gemini = get_gemini_client()
        postgres = get_postgres_driver()
        
        from src.db.postgres.operations import PostgresOperations
        from uuid import uuid4
        
        # Generate embedding
        embedding = await gemini.embed(content)
        entities = await gemini.extract_entities(content)
        
        pg_ops = PostgresOperations(postgres)
        node_id = f"mem_global_{uuid4().hex[:12]}"
        
        await pg_ops.store_embedding(
            node_id=node_id,
            content=content,
            embedding=embedding[0],
            layer=self.name,
            user_id=None,  # Global memories are not user-specific
            tenant_id=None,  # Global memories are not tenant-specific
            metadata={
                **(metadata or {}),
                "contributed_by": str(user_id),
                "verification_status": "auto_high_confidence",
            },
            confidence=confidence,
        )
        
        # Create entities in Neo4j with global layer
        neo4j = get_neo4j_driver()
        from src.db.neo4j.operations import Neo4jOperations
        
        neo_ops = Neo4jOperations(neo4j)
        for entity in entities.get("entities", []):
            await neo_ops.create_entity(
                name=entity["name"],
                entity_type=entity["type"],
                properties={
                    **entity.get("properties", {}),
                    "global": True,
                },
                layer=self.name,
            )
        
        logger.info(
            "global_store",
            user_id=str(user_id),
            node_id=node_id,
            confidence=confidence,
        )
        
        return {
            "id": node_id,
            "content": content,
            "layer": self.name,
            "confidence": confidence,
            "entities": entities.get("entities", []),
        }

    async def retrieve(
        self,
        query: str,
        user_id: UUID,
        tenant_id: UUID | None = None,
        limit: int = 20,
        min_confidence: float = 0.7,  # Higher default for global layer
    ) -> list[dict[str, Any]]:
        """Retrieve from global layer."""
        gemini = get_gemini_client()
        postgres = get_postgres_driver()
        
        from src.db.postgres.operations import PostgresOperations
        
        query_embedding = await gemini.embed(query)
        
        pg_ops = PostgresOperations(postgres)
        results = await pg_ops.similarity_search(
            query_embedding=query_embedding[0],
            layer=self.name,
            # No user/tenant filter for global layer
            min_confidence=min_confidence,
            limit=limit,
        )
        
        logger.debug(
            "global_retrieve",
            user_id=str(user_id),
            results_count=len(results),
        )
        
        return results

    async def delete(
        self,
        memory_id: str,
        user_id: UUID,
        tenant_id: UUID | None = None,
    ) -> bool:
        """Delete from global layer (admin only)."""
        # TODO: Check if user is admin
        
        postgres = get_postgres_driver()
        from src.db.postgres.operations import PostgresOperations
        
        pg_ops = PostgresOperations(postgres)
        result = await pg_ops.delete_embedding(
            node_id=memory_id,
            layer=self.name,
        )
        
        if result:
            logger.warning(
                "global_delete",
                user_id=str(user_id),
                memory_id=memory_id,
            )
        
        return result

    def get_filter_conditions(
        self,
        user_id: UUID,
        tenant_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Get global layer filter conditions."""
        return {"layer": self.name}
