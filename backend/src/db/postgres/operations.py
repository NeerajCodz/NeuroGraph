"""PostgreSQL operations for embeddings and vector search."""

from typing import Any
from uuid import UUID, uuid4

import numpy as np

from src.core.exceptions import MemoryNotFoundError, PostgresError
from src.core.logging import get_logger
from src.db.postgres.driver import PostgresDriver

logger = get_logger(__name__)


class PostgresOperations:
    """High-level PostgreSQL operations for embeddings and vector search."""

    def __init__(self, driver: PostgresDriver) -> None:
        self._driver = driver

    async def store_embedding(
        self,
        node_id: str,
        content: str,
        embedding: list[float] | np.ndarray,
        layer: str = "personal",
        user_id: UUID | None = None,
        tenant_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
        confidence: float = 1.0,
    ) -> UUID:
        """Store an embedding in the vector store.
        
        Args:
            node_id: Identifier for the node/entity
            content: Original text content
            embedding: Vector embedding
            layer: Memory layer (personal, tenant, global)
            user_id: Owner user ID
            tenant_id: Owner tenant ID
            metadata: Additional metadata
            confidence: Confidence score
            
        Returns:
            UUID of the stored embedding
        """
        embedding_id = uuid4()
        
        # Convert numpy array to list if necessary
        if isinstance(embedding, np.ndarray):
            embedding = embedding.tolist()
        
        query = """
        INSERT INTO memory.embeddings 
            (id, node_id, content, embedding, layer, user_id, tenant_id, metadata, confidence)
        VALUES ($1, $2, $3, $4::vector, $5::memory.layer, $6, $7, $8, $9)
        ON CONFLICT (node_id, layer, user_id, tenant_id) 
        DO UPDATE SET 
            content = EXCLUDED.content,
            embedding = EXCLUDED.embedding,
            metadata = EXCLUDED.metadata,
            confidence = EXCLUDED.confidence,
            updated_at = NOW()
        RETURNING id
        """
        
        try:
            result = await self._driver.fetchval(
                query,
                embedding_id,
                node_id,
                content,
                embedding,
                layer,
                user_id,
                tenant_id,
                metadata or {},
                confidence,
            )
            logger.info("embedding_stored", node_id=node_id, layer=layer)
            return result
        except Exception as e:
            raise PostgresError(f"Failed to store embedding: {e}") from e

    async def get_embedding(
        self,
        node_id: str,
        layer: str | None = None,
        user_id: UUID | None = None,
        tenant_id: UUID | None = None,
    ) -> dict[str, Any] | None:
        """Get an embedding by node ID."""
        conditions = ["node_id = $1"]
        params: list[Any] = [node_id]
        param_idx = 2
        
        if layer:
            conditions.append(f"layer = ${param_idx}::memory.layer")
            params.append(layer)
            param_idx += 1
            
        if user_id:
            conditions.append(f"user_id = ${param_idx}")
            params.append(user_id)
            param_idx += 1
            
        if tenant_id:
            conditions.append(f"tenant_id = ${param_idx}")
            params.append(tenant_id)
            param_idx += 1
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
        SELECT id, node_id, content, embedding::text, layer, user_id, tenant_id, 
               metadata, confidence, created_at, updated_at
        FROM memory.embeddings
        WHERE {where_clause}
        LIMIT 1
        """
        
        row = await self._driver.fetchrow(query, *params)
        if row:
            return dict(row)
        return None

    async def delete_embedding(
        self,
        node_id: str,
        layer: str | None = None,
        user_id: UUID | None = None,
    ) -> bool:
        """Delete an embedding."""
        conditions = ["node_id = $1"]
        params: list[Any] = [node_id]
        param_idx = 2
        
        if layer:
            conditions.append(f"layer = ${param_idx}::memory.layer")
            params.append(layer)
            param_idx += 1
            
        if user_id:
            conditions.append(f"user_id = ${param_idx}")
            params.append(user_id)
        
        where_clause = " AND ".join(conditions)
        
        query = f"DELETE FROM memory.embeddings WHERE {where_clause}"
        result = await self._driver.execute(query, *params)
        return "DELETE" in result

    async def similarity_search(
        self,
        query_embedding: list[float] | np.ndarray,
        layer: str | None = None,
        user_id: UUID | None = None,
        tenant_id: UUID | None = None,
        layers: list[str] | None = None,
        min_confidence: float = 0.5,
        limit: int = 20,
        threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        """Perform cosine similarity search on embeddings.
        
        Args:
            query_embedding: Query vector
            layer: Single layer to search
            user_id: Filter by user
            tenant_id: Filter by tenant
            layers: Multiple layers to search
            min_confidence: Minimum confidence threshold
            limit: Maximum results
            threshold: Minimum similarity threshold
            
        Returns:
            List of similar embeddings with scores
        """
        # Convert numpy array to list if necessary
        if isinstance(query_embedding, np.ndarray):
            query_embedding = query_embedding.tolist()
        
        conditions = ["confidence >= $2"]
        params: list[Any] = [query_embedding, min_confidence]
        param_idx = 3
        
        # Layer filtering
        if layer:
            conditions.append(f"layer = ${param_idx}::memory.layer")
            params.append(layer)
            param_idx += 1
        elif layers:
            layer_placeholders = ", ".join(
                f"${param_idx + i}::memory.layer" for i in range(len(layers))
            )
            conditions.append(f"layer IN ({layer_placeholders})")
            params.extend(layers)
            param_idx += len(layers)
        
        # User filtering
        if user_id:
            conditions.append(f"(user_id = ${param_idx} OR user_id IS NULL)")
            params.append(user_id)
            param_idx += 1
            
        # Tenant filtering  
        if tenant_id:
            conditions.append(f"(tenant_id = ${param_idx} OR tenant_id IS NULL)")
            params.append(tenant_id)
            param_idx += 1
        
        where_clause = " AND ".join(conditions)
        params.extend([threshold, limit])
        
        query = f"""
        SELECT 
            id, node_id, content, layer, user_id, tenant_id, 
            metadata, confidence, created_at,
            1 - (embedding <=> $1::vector) AS similarity
        FROM memory.embeddings
        WHERE {where_clause}
          AND 1 - (embedding <=> $1::vector) >= ${param_idx}
        ORDER BY embedding <=> $1::vector
        LIMIT ${param_idx + 1}
        """
        
        try:
            rows = await self._driver.fetch(query, *params)
            results = []
            for row in rows:
                result = dict(row)
                results.append(result)
            return results
        except Exception as e:
            raise PostgresError(f"Similarity search failed: {e}") from e

    async def store_fact(
        self,
        entity1: str,
        relation: str,
        entity2: str,
        layer: str = "personal",
        user_id: UUID | None = None,
        tenant_id: UUID | None = None,
        reason: str | None = None,
        source: str | None = None,
        confidence: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> UUID:
        """Store a fact/relationship in PostgreSQL."""
        fact_id = uuid4()
        
        query = """
        INSERT INTO memory.facts 
            (id, entity1, relation, entity2, layer, user_id, tenant_id, 
             reason, source, confidence, metadata)
        VALUES ($1, $2, $3, $4, $5::memory.layer, $6, $7, $8, $9, $10, $11)
        RETURNING id
        """
        
        try:
            result = await self._driver.fetchval(
                query,
                fact_id,
                entity1,
                relation,
                entity2,
                layer,
                user_id,
                tenant_id,
                reason,
                source,
                confidence,
                metadata or {},
            )
            logger.info("fact_stored", entity1=entity1, relation=relation, entity2=entity2)
            return result
        except Exception as e:
            raise PostgresError(f"Failed to store fact: {e}") from e

    async def get_facts(
        self,
        layer: str | None = None,
        user_id: UUID | None = None,
        tenant_id: UUID | None = None,
        entity: str | None = None,
        min_confidence: float = 0.5,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get facts with filtering."""
        conditions = ["confidence >= $1"]
        params: list[Any] = [min_confidence]
        param_idx = 2
        
        if layer:
            conditions.append(f"layer = ${param_idx}::memory.layer")
            params.append(layer)
            param_idx += 1
            
        if user_id:
            conditions.append(f"user_id = ${param_idx}")
            params.append(user_id)
            param_idx += 1
            
        if tenant_id:
            conditions.append(f"tenant_id = ${param_idx}")
            params.append(tenant_id)
            param_idx += 1
            
        if entity:
            conditions.append(f"(entity1 ILIKE ${param_idx} OR entity2 ILIKE ${param_idx})")
            params.append(f"%{entity}%")
            param_idx += 1
        
        params.append(limit)
        where_clause = " AND ".join(conditions)
        
        query = f"""
        SELECT id, entity1, relation, entity2, layer, user_id, tenant_id,
               reason, source, confidence, metadata, created_at
        FROM memory.facts
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT ${param_idx}
        """
        
        rows = await self._driver.fetch(query, *params)
        return [dict(row) for row in rows]

    async def store_reasoning_path(
        self,
        query_id: UUID,
        path: list[dict[str, Any]],
        score: float,
    ) -> UUID:
        """Store a reasoning path for explainability."""
        path_id = uuid4()
        
        query = """
        INSERT INTO memory.reasoning_paths (id, query_id, path_json, score)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """
        
        import json
        result = await self._driver.fetchval(
            query,
            path_id,
            query_id,
            json.dumps(path),
            score,
        )
        return result

    async def get_reasoning_paths(
        self,
        query_id: UUID,
    ) -> list[dict[str, Any]]:
        """Get reasoning paths for a query."""
        query = """
        SELECT id, query_id, path_json, score, created_at
        FROM memory.reasoning_paths
        WHERE query_id = $1
        ORDER BY score DESC
        """
        
        rows = await self._driver.fetch(query, query_id)
        return [dict(row) for row in rows]
