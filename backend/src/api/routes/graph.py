"""Graph routes for visualization and traversal."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from src.api.dependencies.auth import get_current_user_id
from src.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


class EntityCreate(BaseModel):
    """Entity creation request."""
    name: str = Field(min_length=1, max_length=255)
    entity_type: str = Field(min_length=1, max_length=50)
    properties: dict | None = None
    layer: str = Field(default="personal", pattern="^(personal|tenant|global)$")


class EntityResponse(BaseModel):
    """Entity response model."""
    id: str
    name: str
    type: str
    layer: str
    properties: dict


class RelationshipCreate(BaseModel):
    """Relationship creation request."""
    source_id: str
    target_id: str
    relationship_type: str = Field(min_length=1, max_length=50)
    properties: dict | None = None
    reason: str | None = None
    confidence: float = Field(default=1.0, ge=0, le=1)


class RelationshipResponse(BaseModel):
    """Relationship response model."""
    id: str
    source_id: str
    target_id: str
    type: str
    reason: str | None
    confidence: float


class GraphSubset(BaseModel):
    """Graph visualization data."""
    nodes: list[dict]
    edges: list[dict]
    reasoning_paths: list[dict] | None = None


@router.post("/entities", response_model=EntityResponse)
async def create_entity(
    entity: EntityCreate,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> EntityResponse:
    """Create a new entity in the knowledge graph."""
    logger.info(
        "entity_create",
        user_id=str(user_id),
        name=entity.name,
        type=entity.entity_type,
    )
    
    # TODO: Implement entity creation in Neo4j
    
    return EntityResponse(
        id="ent_placeholder",
        name=entity.name,
        type=entity.entity_type,
        layer=entity.layer,
        properties=entity.properties or {},
    )


@router.get("/entities/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: str,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> EntityResponse:
    """Get an entity by ID."""
    # TODO: Fetch from Neo4j with access check
    return EntityResponse(
        id=entity_id,
        name="Entity name",
        type="Person",
        layer="personal",
        properties={},
    )


@router.get("/entities", response_model=list[EntityResponse])
async def search_entities(
    request: Request,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    q: str = Query(default="", max_length=255),
    types: list[str] | None = Query(default=None),
    layer: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[EntityResponse]:
    """Search entities in the graph."""
    neo4j = request.app.state.neo4j
    
    # Build query based on filters
    where_clauses = []
    params = {"limit": limit}
    
    if q:
        where_clauses.append("e.name CONTAINS $query")
        params["query"] = q
    
    if types:
        where_clauses.append("e.type IN $types")
        params["types"] = types
    
    if layer:
        where_clauses.append("e.layer = $layer")
        params["layer"] = layer
    
    where_clause = " AND ".join(where_clauses) if where_clauses else "true"
    
    query = f"""
    MATCH (e:Entity)
    WHERE {where_clause}
    RETURN e.id as id, e.name as name, e.type as type, 
           coalesce(e.layer, 'global') as layer,
           e.description as description
    LIMIT $limit
    """
    
    records = await neo4j.execute_read(query, params)
    
    entities = []
    for record in records:
        props = {}
        if record.get("description"):
            props["description"] = record["description"]
        
        entities.append(EntityResponse(
            id=record["id"] or record["name"],
            name=record["name"],
            type=record["type"],
            layer=record["layer"],
            properties=props,
        ))
    
    logger.info("entities_search", count=len(entities), query=q)
    return entities


@router.delete("/entities/{entity_id}")
async def delete_entity(
    entity_id: str,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> dict[str, str]:
    """Delete an entity and its relationships."""
    logger.info("entity_delete", user_id=str(user_id), entity_id=entity_id)
    
    # TODO: Implement deletion in Neo4j
    
    return {"message": f"Entity {entity_id} deleted"}


@router.post("/relationships", response_model=RelationshipResponse)
async def create_relationship(
    relationship: RelationshipCreate,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> RelationshipResponse:
    """Create a relationship between entities."""
    logger.info(
        "relationship_create",
        user_id=str(user_id),
        source=relationship.source_id,
        target=relationship.target_id,
        type=relationship.relationship_type,
    )
    
    # TODO: Implement relationship creation in Neo4j
    
    return RelationshipResponse(
        id="rel_placeholder",
        source_id=relationship.source_id,
        target_id=relationship.target_id,
        type=relationship.relationship_type,
        reason=relationship.reason,
        confidence=relationship.confidence,
    )


@router.get("/relationships/{entity_id}", response_model=list[RelationshipResponse])
async def get_relationships(
    request: Request,
    entity_id: str,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    direction: str = Query(default="both", pattern="^(incoming|outgoing|both)$"),
    types: list[str] | None = Query(default=None),
) -> list[RelationshipResponse]:
    """Get relationships for an entity."""
    neo4j = request.app.state.neo4j
    
    # Build direction clause
    if direction == "outgoing":
        pattern = "(e)-[r]->(other)"
    elif direction == "incoming":
        pattern = "(e)<-[r]-(other)"
    else:
        pattern = "(e)-[r]-(other)"
    
    # Build type filter
    type_filter = ""
    params = {"entity_id": entity_id}
    if types:
        type_filter = "AND type(r) IN $types"
        params["types"] = types
    
    query = f"""
    MATCH {pattern}
    WHERE (e.id = $entity_id OR e.name = $entity_id) {type_filter}
    RETURN 
        coalesce(r.id, id(r)) as id,
        coalesce(startNode(r).id, startNode(r).name) as source_id,
        coalesce(endNode(r).id, endNode(r).name) as target_id,
        type(r) as type,
        r.reason as reason,
        coalesce(r.confidence, 1.0) as confidence
    """
    
    records = await neo4j.execute_read(query, params)
    
    relationships = [
        RelationshipResponse(
            id=str(r["id"]),
            source_id=r["source_id"],
            target_id=r["target_id"],
            type=r["type"],
            reason=r["reason"],
            confidence=r["confidence"],
        )
        for r in records
    ]
    
    return relationships


@router.delete("/relationships/{relationship_id}")
async def delete_relationship(
    relationship_id: str,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> dict[str, str]:
    """Delete a relationship."""
    logger.info("relationship_delete", user_id=str(user_id), relationship_id=relationship_id)
    
    # TODO: Implement deletion in Neo4j
    
    return {"message": f"Relationship {relationship_id} deleted"}


@router.get("/visualize", response_model=GraphSubset)
async def visualize_graph(
    request: Request,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    center_entity: str | None = Query(default=None),
    depth: int = Query(default=2, ge=1, le=5),
    max_nodes: int = Query(default=100, ge=10, le=500),
) -> GraphSubset:
    """Get graph data for visualization.
    
    Returns nodes and edges suitable for D3.js rendering.
    """
    neo4j = request.app.state.neo4j
    
    # Get all entities with relationships
    query = """
    MATCH (n:Entity)
    OPTIONAL MATCH (n)-[r]-(m:Entity)
    WITH collect(DISTINCT {
        id: coalesce(n.id, n.name),
        name: n.name,
        type: n.type,
        layer: coalesce(n.layer, 'global')
    }) as nodes,
    collect(DISTINCT {
        source: coalesce(startNode(r).id, startNode(r).name),
        target: coalesce(endNode(r).id, endNode(r).name),
        type: type(r),
        reason: r.reason,
        confidence: coalesce(r.confidence, 1.0)
    }) as edges
    RETURN nodes[$skip..$max_nodes] as nodes, [e in edges WHERE e.source IS NOT NULL][$skip..$max_edges] as edges
    """
    params = {"max_nodes": max_nodes, "max_edges": max_nodes * 2, "skip": 0}
    
    records = await neo4j.execute_read(query, params)
    
    if records:
        nodes = records[0].get("nodes", [])
        edges = records[0].get("edges", [])
    else:
        nodes = []
        edges = []
    
    logger.info("graph_visualize", nodes_count=len(nodes), edges_count=len(edges))
    
    return GraphSubset(
        nodes=nodes,
        edges=edges,
        reasoning_paths=None,
    )


@router.get("/paths/{source_id}/{target_id}")
async def find_paths(
    source_id: str,
    target_id: str,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    max_depth: int = Query(default=5, ge=1, le=10),
) -> dict:
    """Find paths between two entities."""
    # TODO: Implement path finding in Neo4j
    return {
        "paths": [],
        "shortest_path": None,
    }


@router.get("/centrality")
async def get_centrality(
    request: Request,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    entity_ids: list[str] = Query(default=[]),
) -> dict[str, int]:
    """Get degree centrality for entities."""
    neo4j = request.app.state.neo4j
    
    if entity_ids:
        query = """
        MATCH (e:Entity)-[r]-()
        WHERE e.id IN $entity_ids OR e.name IN $entity_ids
        RETURN coalesce(e.id, e.name) as id, count(r) as degree
        """
        params = {"entity_ids": entity_ids}
    else:
        query = """
        MATCH (e:Entity)-[r]-()
        RETURN coalesce(e.id, e.name) as id, count(r) as degree
        ORDER BY degree DESC
        LIMIT 50
        """
        params = {}
    
    records = await neo4j.execute_read(query, params)
    
    return {r["id"]: r["degree"] for r in records}
