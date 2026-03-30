"""Personal memory layer - user-specific isolated storage."""

from typing import Any
from uuid import UUID

from src.core.logging import get_logger
from src.db.neo4j import get_neo4j_driver
from src.db.postgres import get_postgres_driver
from src.memory.layers.base import MemoryLayer
from src.models.gemini import get_gemini_client

logger = get_logger(__name__)


class PersonalLayer(MemoryLayer):
    """Personal memory layer for user-specific data.
    
    Characteristics:
    - User-specific isolation
    - Only the owning user can read/write
    - No cross-user access permitted
    - Default layer for new memories
    """

    @property
    def name(self) -> str:
        return "personal"

    async def can_read(self, user_id: UUID, tenant_id: UUID | None = None) -> bool:
        """User can always read their own personal layer."""
        return True

    async def can_write(self, user_id: UUID, tenant_id: UUID | None = None) -> bool:
        """User can always write to their own personal layer."""
        return True

    async def store(
        self,
        content: str,
        user_id: UUID,
        tenant_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
        confidence: float = 1.0,
    ) -> dict[str, Any]:
        """Store information in personal layer."""
        gemini = get_gemini_client()
        postgres = get_postgres_driver()
        neo4j = get_neo4j_driver()
        
        # Generate embedding
        from src.db.postgres.operations import PostgresOperations
        from src.db.neo4j.operations import Neo4jOperations
        
        embedding = await gemini.embed(content)
        entities = await gemini.extract_entities(content)
        
        # Store embedding in PostgreSQL
        pg_ops = PostgresOperations(postgres)
        from uuid import uuid4
        node_id = f"mem_{uuid4().hex[:12]}"
        
        await pg_ops.store_embedding(
            node_id=node_id,
            content=content,
            embedding=embedding[0],
            layer=self.name,
            user_id=user_id,
            metadata=metadata,
            confidence=confidence,
        )
        
        # Create entities and relationships in Neo4j
        neo_ops = Neo4jOperations(neo4j)
        created_entities = []
        
        for entity in entities.get("entities", []):
            result = await neo_ops.create_entity(
                name=entity["name"],
                entity_type=entity["type"],
                properties=entity.get("properties", {}),
                layer=self.name,
                user_id=str(user_id),
            )
            created_entities.append(result)
        
        for rel in entities.get("relationships", []):
            # Find source and target entity IDs
            # This is simplified - in production we'd do proper entity resolution
            pass
        
        logger.info(
            "personal_store",
            user_id=str(user_id),
            node_id=node_id,
            entities_count=len(created_entities),
        )
        
        return {
            "id": node_id,
            "content": content,
            "layer": self.name,
            "confidence": confidence,
            "entities": created_entities,
        }

    async def retrieve(
        self,
        query: str,
        user_id: UUID,
        tenant_id: UUID | None = None,
        limit: int = 20,
        min_confidence: float = 0.5,
    ) -> list[dict[str, Any]]:
        """Retrieve from personal layer using vector similarity."""
        gemini = get_gemini_client()
        postgres = get_postgres_driver()
        
        from src.db.postgres.operations import PostgresOperations
        
        # Generate query embedding
        query_embedding = await gemini.embed(query)
        
        # Search PostgreSQL
        pg_ops = PostgresOperations(postgres)
        results = await pg_ops.similarity_search(
            query_embedding=query_embedding[0],
            layer=self.name,
            user_id=user_id,
            min_confidence=min_confidence,
            limit=limit,
        )
        
        logger.debug(
            "personal_retrieve",
            user_id=str(user_id),
            query_length=len(query),
            results_count=len(results),
        )
        
        return results

    async def delete(
        self,
        memory_id: str,
        user_id: UUID,
        tenant_id: UUID | None = None,
    ) -> bool:
        """Delete from personal layer."""
        postgres = get_postgres_driver()
        
        from src.db.postgres.operations import PostgresOperations
        
        pg_ops = PostgresOperations(postgres)
        result = await pg_ops.delete_embedding(
            node_id=memory_id,
            layer=self.name,
            user_id=user_id,
        )
        
        if result:
            logger.info("personal_delete", user_id=str(user_id), memory_id=memory_id)
        
        return result

    def get_filter_conditions(
        self,
        user_id: UUID,
        tenant_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Get personal layer filter conditions."""
        return {
            "layer": self.name,
            "user_id": user_id,
        }
