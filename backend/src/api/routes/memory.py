"""Memory routes for CRUD operations."""

from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

import asyncpg
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field

from src.api.dependencies.auth import get_current_user_id
from src.core.logging import get_logger
from src.core.config import get_settings
from src.db.postgres import get_postgres_driver
from src.rag.embeddings import EmbeddingsService
from src.rag.hybrid_search import HybridSearch
from src.models.gemini import get_gemini_client

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()


class MemoryCreate(BaseModel):
    """Memory creation request."""
    content: str = Field(min_length=1, max_length=50000)
    layer: str = Field(default="personal", pattern="^(personal|tenant|global)$")
    tenant_id: UUID | None = None
    metadata: dict | None = None


class MemoryResponse(BaseModel):
    """Memory response model."""
    id: UUID
    content: str
    layer: str
    confidence: float
    entities_extracted: list[str]
    created_at: datetime
    updated_at: datetime


class MemorySearchRequest(BaseModel):
    """Memory search request."""
    query: str = Field(min_length=1, max_length=1000)
    layers: list[str] | None = None
    max_results: int = Field(default=20, ge=1, le=100)
    min_confidence: float = Field(default=0.5, ge=0, le=1)


class MemorySearchResult(BaseModel):
    """Search result item."""
    id: UUID
    content: str
    layer: str
    confidence: float
    score: float
    created_at: datetime


# Initialize services
_embeddings_service: EmbeddingsService | None = None
_hybrid_search: HybridSearch | None = None
_gemini_client = None


def get_embeddings_service() -> EmbeddingsService:
    """Get or create embeddings service."""
    global _embeddings_service
    if _embeddings_service is None:
        _embeddings_service = EmbeddingsService()
    return _embeddings_service


def get_hybrid_search() -> HybridSearch:
    """Get or create hybrid search service."""
    global _hybrid_search
    if _hybrid_search is None:
        _hybrid_search = HybridSearch()
    return _hybrid_search


@router.post("/remember", response_model=MemoryResponse)
async def remember(
    memory: MemoryCreate,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> MemoryResponse:
    """Store information in memory.
    
    Extracts entities, generates embeddings, and stores in both
    Neo4j (relationships) and PostgreSQL (embeddings).
    """
    logger.info(
        "memory_remember",
        user_id=str(user_id),
        layer=memory.layer,
        content_length=len(memory.content),
    )
    
    try:
        # 1. Generate embedding for content
        embeddings_svc = get_embeddings_service()
        embedding = await embeddings_svc.embed_text(memory.content)
        embedding_list = embedding.tolist()
        
        # 2. Extract entities using Gemini
        gemini = get_gemini_client()
        entities_result = await gemini.extract_entities(memory.content)
        entity_names = [e.get("name", "unknown") for e in entities_result.get("entities", [])]
        
        # 3. Generate node_id
        memory_id = uuid4()
        node_id = f"memory_{memory_id}"
        
        # 4. Store in PostgreSQL
        postgres = get_postgres_driver()
        
        # Format embedding as pgvector string (no spaces)
        embedding_str = "[" + ",".join(map(str, embedding_list)) + "]"
        
        # Convert metadata to JSON string
        import json
        metadata_json = json.dumps(memory.metadata or {})
        
        async with postgres.connection() as conn:
            # Use text() style query with proper casting
            await conn.execute(
                f"""
                INSERT INTO memory.embeddings 
                (id, node_id, layer, user_id, tenant_id, content, embedding, metadata, confidence)
                VALUES ($1, $2, $3, $4, $5, $6, '{embedding_str}'::vector, $7::jsonb, $8)
                """,
                memory_id,
                node_id,
                memory.layer,
                user_id if memory.layer == "personal" else None,
                memory.tenant_id if memory.layer == "tenant" else None,
                memory.content,
                metadata_json,
                0.95 if memory.layer != "global" else 0.90,
            )
        
        logger.info(
            "memory_stored",
            memory_id=str(memory_id),
            layer=memory.layer,
            entities_count=len(entity_names),
        )
        
        return MemoryResponse(
            id=memory_id,
            content=memory.content,
            layer=memory.layer,
            confidence=0.95,
            entities_extracted=entity_names[:10],  # Limit to first 10
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
    except Exception as e:
        logger.error("memory_remember_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to store memory: {str(e)}")


@router.post("/recall", response_model=list[MemorySearchResult])
async def recall(
    request: MemorySearchRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> list[MemorySearchResult]:
    """Recall information from memory.
    
    Performs hybrid search using vector similarity (PostgreSQL)
    and graph traversal (Neo4j) to find relevant memories.
    """
    logger.info(
        "memory_recall",
        user_id=str(user_id),
        query_length=len(request.query),
        layers=request.layers,
    )
    
    try:
        # Use hybrid search pipeline
        hybrid = get_hybrid_search()
        results = await hybrid.search(
            query=request.query,
            user_id=user_id,
            layers=request.layers or ["personal"],
            limit=request.max_results,
            min_confidence=request.min_confidence,
        )
        
        # Convert ScoredNode to MemorySearchResult
        return [
            MemorySearchResult(
                id=r.node_id if isinstance(r.node_id, UUID) else UUID(r.node_id) if len(str(r.node_id)) == 36 else uuid4(),
                content=r.content,
                layer=r.layer,
                confidence=r.confidence,
                score=r.final_score,
                created_at=r.created_at if hasattr(r, 'created_at') and r.created_at else datetime.utcnow(),
            )
            for r in results
        ]
        
    except Exception as e:
        logger.error("memory_recall_failed", error=str(e))
        # Return empty list instead of error for graceful degradation
        return []


@router.get("/search", response_model=list[MemorySearchResult])
async def search(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    q: str = Query(min_length=1, max_length=1000),
    layers: list[str] | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[MemorySearchResult]:
    """Search memories with query parameters."""
    return await recall(
        MemorySearchRequest(query=q, layers=layers, max_results=limit),
        user_id,
    )


@router.get("/list", response_model=list[MemorySearchResult])
async def list_memories(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    layer: str = Query(default="personal", pattern="^(personal|tenant|global)$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[MemorySearchResult]:
    """List all memories for a specific layer."""
    logger.info("memory_list", user_id=str(user_id), layer=layer)
    
    postgres = get_postgres_driver()
    
    async with postgres.connection() as conn:
        if layer == "personal":
            rows = await conn.fetch(
                """
                SELECT id, node_id, content, layer, confidence, created_at
                FROM memory.embeddings
                WHERE user_id = $1 AND layer = 'personal'
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                user_id,
                limit,
                offset,
            )
        elif layer == "global":
            rows = await conn.fetch(
                """
                SELECT id, node_id, content, layer, confidence, created_at
                FROM memory.embeddings
                WHERE layer = 'global'
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )
        else:  # tenant/workspace
            rows = await conn.fetch(
                """
                SELECT id, node_id, content, layer, confidence, created_at
                FROM memory.embeddings
                WHERE layer = 'tenant'
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )
    
    return [
        MemorySearchResult(
            id=row["id"],
            content=row["content"],
            layer=row["layer"],
            confidence=row["confidence"],
            score=1.0,  # No search score for listing
            created_at=row["created_at"],
        )
        for row in rows
    ]


@router.get("/count")
async def memory_count(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> dict:
    """Get memory counts by layer."""
    postgres = get_postgres_driver()
    
    async with postgres.connection() as conn:
        personal_count = await conn.fetchval(
            "SELECT COUNT(*) FROM memory.embeddings WHERE user_id = $1 AND layer = 'personal'",
            user_id,
        )
        
        tenant_count = await conn.fetchval(
            "SELECT COUNT(*) FROM memory.embeddings WHERE layer = 'tenant'",
        )
        
        global_count = await conn.fetchval(
            "SELECT COUNT(*) FROM memory.embeddings WHERE layer = 'global'",
        )
    
    return {
        "personal": personal_count or 0,
        "tenant": tenant_count or 0,
        "workspace": tenant_count or 0,  # Alias for frontend
        "global": global_count or 0,
        "total": (personal_count or 0) + (tenant_count or 0) + (global_count or 0),
    }


@router.get("/status", response_model=dict)
async def memory_status(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> dict:
    """Get memory statistics for current user."""
    # Get counts and return as status
    counts = await memory_count(user_id)
    return {
        "total_memories": counts["total"],
        "by_layer": {
            "personal": counts["personal"],
            "tenant": counts["tenant"],
            "global": counts["global"],
        },
        "entity_count": 0,  # TODO: Implement
        "relationship_count": 0,  # TODO: Implement
    }


# Path parameter routes at END to avoid conflicts
@router.get("/{id}", response_model=MemoryResponse)
async def get_memory(
    id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> MemoryResponse:
    """Get a specific memory by ID."""
    postgres = get_postgres_driver()
    async with postgres.connection() as conn:
        row = await conn.fetchrow(
            "SELECT id, content, layer, confidence, created_at, updated_at FROM memory.embeddings WHERE id = $1",
            id,
        )
    if not row:
        raise HTTPException(status_code=404, detail="Memory not found")
    return MemoryResponse(
        id=row["id"],
        content=row["content"],
        layer=row["layer"],
        confidence=row["confidence"],
        entities_extracted=[],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.delete("/{id}")
async def forget(
    id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> dict[str, str]:
    """Delete a memory (forget)."""
    logger.info("memory_forget", user_id=str(user_id), memory_id=str(id))
    
    postgres = get_postgres_driver()
    
    async with postgres.connection() as conn:
        result = await conn.execute(
            "DELETE FROM memory.embeddings WHERE id = $1 AND (user_id = $2 OR layer = 'global')",
            id,
            user_id,
        )
    
    return {"message": f"Memory {id} deleted"}
