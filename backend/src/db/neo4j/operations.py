"""Neo4j graph operations for entities and relationships."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from src.core.exceptions import MemoryNotFoundError, Neo4jError
from src.core.logging import get_logger
from src.db.neo4j.driver import Neo4jDriver

logger = get_logger(__name__)


class Neo4jOperations:
    """High-level Neo4j operations for the knowledge graph."""

    def __init__(self, driver: Neo4jDriver) -> None:
        self._driver = driver

    async def create_entity(
        self,
        name: str,
        entity_type: str,
        properties: dict[str, Any] | None = None,
        layer: str = "personal",
        user_id: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new entity node in the graph.
        
        Args:
            name: Entity name
            entity_type: Entity type (Person, Project, Document, etc.)
            properties: Additional properties
            layer: Memory layer (personal, tenant, global)
            user_id: Owner user ID
            tenant_id: Owner tenant ID
            
        Returns:
            Created entity data
        """
        entity_id = f"ent_{entity_type.lower()}_{uuid4().hex[:8]}"
        props = properties or {}
        
        query = """
        CREATE (e:Entity:$entity_type {
            id: $entity_id,
            name: $name,
            type: $entity_type,
            layer: $layer,
            user_id: $user_id,
            tenant_id: $tenant_id,
            created_at: datetime(),
            updated_at: datetime()
        })
        SET e += $props
        RETURN e {.*, labels: labels(e)} AS entity
        """.replace("$entity_type", entity_type)
        
        try:
            results = await self._driver.execute_write(
                query,
                {
                    "entity_id": entity_id,
                    "name": name,
                    "entity_type": entity_type,
                    "layer": layer,
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                    "props": props,
                },
            )
            logger.info("entity_created", entity_id=entity_id, type=entity_type)
            return results[0]["entity"] if results else {}
        except Exception as e:
            raise Neo4jError(f"Failed to create entity: {e}") from e

    async def get_entity(self, entity_id: str) -> dict[str, Any]:
        """Get an entity by ID."""
        query = """
        MATCH (e:Entity {id: $entity_id})
        RETURN e {.*, labels: labels(e)} AS entity
        """
        results = await self._driver.execute_read(query, {"entity_id": entity_id})
        if not results:
            raise MemoryNotFoundError(f"Entity not found: {entity_id}")
        return results[0]["entity"]

    async def update_entity(
        self,
        entity_id: str,
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        """Update entity properties."""
        query = """
        MATCH (e:Entity {id: $entity_id})
        SET e += $props, e.updated_at = datetime()
        RETURN e {.*, labels: labels(e)} AS entity
        """
        results = await self._driver.execute_write(
            query,
            {"entity_id": entity_id, "props": properties},
        )
        if not results:
            raise MemoryNotFoundError(f"Entity not found: {entity_id}")
        return results[0]["entity"]

    async def delete_entity(self, entity_id: str) -> bool:
        """Delete an entity and its relationships."""
        query = """
        MATCH (e:Entity {id: $entity_id})
        DETACH DELETE e
        RETURN count(e) AS deleted
        """
        results = await self._driver.execute_write(query, {"entity_id": entity_id})
        return results[0]["deleted"] > 0 if results else False

    async def create_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: dict[str, Any] | None = None,
        reason: str | None = None,
        confidence: float = 1.0,
    ) -> dict[str, Any]:
        """Create a relationship between two entities.
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            relationship_type: Type of relationship (e.g., WORKS_ON, MANAGES)
            properties: Additional relationship properties
            reason: Reasoning behind this relationship
            confidence: Confidence score (0.0 to 1.0)
            
        Returns:
            Created relationship data
        """
        rel_id = f"rel_{uuid4().hex[:8]}"
        props = properties or {}
        
        query = f"""
        MATCH (source:Entity {{id: $source_id}})
        MATCH (target:Entity {{id: $target_id}})
        CREATE (source)-[r:{relationship_type} {{
            id: $rel_id,
            reason: $reason,
            confidence: $confidence,
            created_at: datetime()
        }}]->(target)
        SET r += $props
        RETURN {{
            id: r.id,
            type: type(r),
            source: source.id,
            target: target.id,
            reason: r.reason,
            confidence: r.confidence,
            properties: properties(r)
        }} AS relationship
        """
        
        try:
            results = await self._driver.execute_write(
                query,
                {
                    "source_id": source_id,
                    "target_id": target_id,
                    "rel_id": rel_id,
                    "reason": reason,
                    "confidence": confidence,
                    "props": props,
                },
            )
            if not results:
                raise Neo4jError("Failed to create relationship: entities not found")
            logger.info(
                "relationship_created",
                rel_id=rel_id,
                type=relationship_type,
                source=source_id,
                target=target_id,
            )
            return results[0]["relationship"]
        except Exception as e:
            raise Neo4jError(f"Failed to create relationship: {e}") from e

    async def get_relationships(
        self,
        entity_id: str,
        direction: str = "both",
        relationship_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get relationships for an entity.
        
        Args:
            entity_id: Entity ID
            direction: "incoming", "outgoing", or "both"
            relationship_types: Filter by relationship types
            
        Returns:
            List of relationships
        """
        type_filter = ""
        if relationship_types:
            types = "|".join(relationship_types)
            type_filter = f":{types}"
        
        if direction == "outgoing":
            pattern = f"(e)-[r{type_filter}]->(other)"
        elif direction == "incoming":
            pattern = f"(e)<-[r{type_filter}]-(other)"
        else:
            pattern = f"(e)-[r{type_filter}]-(other)"
        
        query = f"""
        MATCH (e:Entity {{id: $entity_id}})
        MATCH {pattern}
        RETURN {{
            id: r.id,
            type: type(r),
            source: startNode(r).id,
            target: endNode(r).id,
            reason: r.reason,
            confidence: r.confidence,
            other_entity: other {{.id, .name, .type}}
        }} AS relationship
        """
        
        results = await self._driver.execute_read(query, {"entity_id": entity_id})
        return [r["relationship"] for r in results]

    async def delete_relationship(self, relationship_id: str) -> bool:
        """Delete a relationship by ID."""
        query = """
        MATCH ()-[r {id: $rel_id}]->()
        DELETE r
        RETURN count(r) AS deleted
        """
        results = await self._driver.execute_write(query, {"rel_id": relationship_id})
        return results[0]["deleted"] > 0 if results else False

    async def traverse(
        self,
        seed_nodes: list[str],
        max_hops: int = 3,
        relationship_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Traverse the graph from seed nodes.
        
        Args:
            seed_nodes: Starting entity IDs or names
            max_hops: Maximum traversal depth
            relationship_types: Filter by relationship types
            
        Returns:
            List of paths with nodes and relationships
        """
        type_filter = ""
        if relationship_types:
            types = "|".join(relationship_types)
            type_filter = f":{types}"
        
        query = f"""
        MATCH path = (start:Entity)-[r{type_filter}*1..{max_hops}]-(connected:Entity)
        WHERE start.id IN $seeds OR start.name IN $seeds
        RETURN 
            [n IN nodes(path) | n {{.id, .name, .type}}] AS nodes,
            [rel IN relationships(path) | {{
                type: type(rel),
                reason: rel.reason,
                confidence: rel.confidence
            }}] AS relationships,
            length(path) AS hops
        ORDER BY length(path)
        LIMIT 100
        """
        
        results = await self._driver.execute_read(query, {"seeds": seed_nodes})
        return results

    async def find_shortest_path(
        self,
        source_id: str,
        target_id: str,
    ) -> dict[str, Any] | None:
        """Find the shortest path between two entities."""
        query = """
        MATCH path = shortestPath(
            (source:Entity {id: $source_id})-[*]-(target:Entity {id: $target_id})
        )
        RETURN 
            [n IN nodes(path) | n {.id, .name, .type}] AS nodes,
            [r IN relationships(path) | {
                type: type(r),
                reason: r.reason,
                confidence: r.confidence
            }] AS relationships,
            length(path) AS hops
        """
        
        results = await self._driver.execute_read(
            query,
            {"source_id": source_id, "target_id": target_id},
        )
        return results[0] if results else None

    async def get_centrality(
        self,
        entity_ids: list[str],
    ) -> dict[str, int]:
        """Get edge count (degree centrality) for entities."""
        query = """
        MATCH (e:Entity)-[r]-(neighbor)
        WHERE e.id IN $entity_ids
        RETURN e.id AS entity_id, count(r) AS edge_count
        ORDER BY edge_count DESC
        """
        results = await self._driver.execute_read(query, {"entity_ids": entity_ids})
        return {r["entity_id"]: r["edge_count"] for r in results}

    async def search_entities(
        self,
        name_pattern: str,
        entity_types: list[str] | None = None,
        layer: str | None = None,
        user_id: str | None = None,
        tenant_id: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search entities by name pattern."""
        conditions = ["e.name =~ $pattern"]
        params: dict[str, Any] = {"pattern": f"(?i).*{name_pattern}.*", "limit": limit}
        
        if entity_types:
            conditions.append("e.type IN $types")
            params["types"] = entity_types
        
        if layer:
            conditions.append("e.layer = $layer")
            params["layer"] = layer
            
        if user_id:
            conditions.append("e.user_id = $user_id")
            params["user_id"] = user_id
            
        if tenant_id:
            conditions.append("e.tenant_id = $tenant_id")
            params["tenant_id"] = tenant_id
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
        MATCH (e:Entity)
        WHERE {where_clause}
        RETURN e {{.*, labels: labels(e)}} AS entity
        ORDER BY e.name
        LIMIT $limit
        """
        
        results = await self._driver.execute_read(query, params)
        return [r["entity"] for r in results]
