"""Memory routes for CRUD operations."""

import asyncio
from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

import asyncpg
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field

from src.api.dependencies.auth import get_current_user_id
from src.core.logging import get_logger
from src.db.postgres import get_postgres_driver
from src.memory.enrichment_queue import (
    build_entity_metadata_patch,
    enqueue_memory_enrichment,
    extract_entity_names,
    merge_entity_metadata,
)
from src.rag.embeddings import EmbeddingsService
from src.rag.hybrid_search import HybridSearch
from src.models.gemini import get_gemini_client

router = APIRouter()
logger = get_logger(__name__)


class MemoryCreate(BaseModel):
    """Memory creation request."""
    content: str = Field(min_length=1, max_length=50000)
    layer: str = Field(default="personal", pattern="^(personal|tenant|global)$")
    tenant_id: UUID | None = None
    workspace_id: UUID | None = None
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
    workspace_id: UUID | None = None
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

ENTITY_EXTRACTION_TIMEOUT_SECONDS = 2.5


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


async def _has_workspace_access(
    conn: asyncpg.Connection,
    workspace_id: UUID,
    user_id: UUID,
    require_write: bool = False,
) -> bool:
    """Check whether user can read/write a workspace."""
    row = await conn.fetchrow(
        """
        SELECT 1
        WHERE EXISTS (
            SELECT 1
            FROM chat.workspaces w
            LEFT JOIN chat.workspace_members wm ON w.id = wm.workspace_id
            WHERE w.id = $1
              AND w.status = 'active'
              AND (
                w.owner_id = $2
                OR (
                  wm.user_id = $2
                  AND ($3 = FALSE OR wm.can_write = TRUE)
                )
              )
        )
        OR EXISTS (
            SELECT 1
            FROM auth.tenant_members tm
            WHERE tm.tenant_id = $1
              AND tm.user_id = $2
        )
        LIMIT 1
        """,
        workspace_id,
        user_id,
        require_write,
    )
    return bool(row)


def _workspace_id_from_metadata(metadata: dict | None) -> UUID | None:
    """Extract workspace UUID from metadata payload."""
    if not metadata:
        return None

    workspace_value = metadata.get("workspace_id")
    if not workspace_value:
        return None

    try:
        return UUID(str(workspace_value))
    except ValueError:
        return None


@router.post("/remember", response_model=MemoryResponse)
async def remember(
    memory: MemoryCreate,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> MemoryResponse:
    """Store information in memory.
    
    Generates embeddings synchronously for immediate recall accuracy.
    Entity extraction runs in a short inline window, then falls back to queue.
    """
    logger.info(
        "memory_remember",
        user_id=str(user_id),
        layer=memory.layer,
        content_length=len(memory.content),
    )
    
    try:
        workspace_id = memory.workspace_id or memory.tenant_id

        if memory.layer == "tenant":
            if not workspace_id:
                raise HTTPException(
                    status_code=400,
                    detail="workspace_id is required for workspace memory",
                )

            postgres = get_postgres_driver()
            async with postgres.connection() as conn:
                if not await _has_workspace_access(conn, workspace_id, user_id, require_write=True):
                    raise HTTPException(status_code=403, detail="No write access to workspace")

        # 1. Generate embedding for content
        embeddings_svc = get_embeddings_service()
        embedding = await embeddings_svc.embed_text(memory.content)
        embedding_list = embedding.tolist()
        
        # 2. Attempt fast entity extraction; defer to queue on timeout/failure
        gemini = get_gemini_client()
        entity_names: list[str] = []
        extraction_status = "queued"
        extraction_source = "queue"
        extraction_error: str | None = None
        entities_result: dict | None = None
        try:
            extracted = await asyncio.wait_for(
                gemini.extract_entities(memory.content),
                timeout=ENTITY_EXTRACTION_TIMEOUT_SECONDS,
            )
            if isinstance(extracted, dict):
                entities_result = extracted
            entity_names = extract_entity_names(entities_result)[:10]
            extraction_status = "completed"
            extraction_source = "inline"
        except asyncio.TimeoutError:
            extraction_error = (
                f"entity extraction exceeded {ENTITY_EXTRACTION_TIMEOUT_SECONDS:.1f}s"
            )
            logger.warning(
                "entity_extraction_deferred",
                reason="timeout",
                timeout_s=ENTITY_EXTRACTION_TIMEOUT_SECONDS,
            )
        except Exception as e:
            extraction_error = str(e)
            logger.warning("entity_extraction_fallback_used", error=str(e))
        
        # 3. Generate node_id
        memory_id = uuid4()
        node_id = f"memory_{memory_id}"
        
        # 4. Store in PostgreSQL
        postgres = get_postgres_driver()
        
        # Prepare metadata with entity extraction status
        import json
        metadata_obj = dict(memory.metadata or {})
        metadata_obj.update(
            build_entity_metadata_patch(
                status=extraction_status,
                source=extraction_source,
                entities_result=entities_result,
                error=extraction_error,
            )
        )
        metadata_json = json.dumps(metadata_obj)
        
        async with postgres.connection() as conn:
            await conn.execute(
                """
                INSERT INTO memory.embeddings 
                (id, node_id, layer, user_id, tenant_id, content, embedding, metadata, confidence)
                VALUES ($1, $2, $3, $4, $5, $6, $7::vector, $8::jsonb, $9)
                """,
                memory_id,
                node_id,
                memory.layer,
                user_id if memory.layer == "personal" else None,
                workspace_id if memory.layer == "tenant" else None,
                memory.content,
                embedding_list,
                metadata_json,
                0.95 if memory.layer != "global" else 0.90,
            )

        # Queue deferred enrichment if inline extraction was skipped/failure
        if extraction_status != "completed":
            queued = await enqueue_memory_enrichment(
                memory_id=memory_id,
                user_id=user_id,
                layer=memory.layer,
                tenant_id=workspace_id if memory.layer == "tenant" else None,
                attempt=1,
            )
            if not queued:
                await merge_entity_metadata(
                    memory_id,
                    build_entity_metadata_patch(
                        status="failed",
                        source="queue",
                        error="failed to enqueue enrichment job",
                    ),
                )
        
        logger.info(
            "memory_stored",
            memory_id=str(memory_id),
            layer=memory.layer,
            entities_count=len(entity_names),
            entity_extraction_status=extraction_status,
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
        
    except HTTPException:
        raise
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
        workspace_id = request.workspace_id
        if "tenant" in (request.layers or []):
            if not workspace_id:
                raise HTTPException(
                    status_code=400,
                    detail="workspace_id is required when querying workspace memory",
                )

            postgres = get_postgres_driver()
            async with postgres.connection() as conn:
                if not await _has_workspace_access(conn, workspace_id, user_id, require_write=False):
                    raise HTTPException(status_code=403, detail="No access to workspace")

        # Use hybrid search pipeline
        hybrid = get_hybrid_search()
        results = await hybrid.search(
            query=request.query,
            user_id=user_id,
            tenant_id=workspace_id,
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("memory_recall_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to recall memories: {str(e)}")


@router.get("/search", response_model=list[MemorySearchResult])
async def search(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    q: str = Query(min_length=1, max_length=1000),
    layers: list[str] | None = Query(default=None),
    workspace_id: UUID | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[MemorySearchResult]:
    """Search memories with query parameters."""
    return await recall(
        MemorySearchRequest(query=q, layers=layers, workspace_id=workspace_id, max_results=limit),
        user_id,
    )


@router.get("/list", response_model=list[MemorySearchResult])
async def list_memories(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    layer: str = Query(default="personal", pattern="^(personal|tenant|global)$"),
    workspace_id: UUID | None = Query(default=None),
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
            if not workspace_id:
                raise HTTPException(
                    status_code=400,
                    detail="workspace_id is required for workspace memory",
                )

            if not await _has_workspace_access(conn, workspace_id, user_id, require_write=False):
                raise HTTPException(status_code=403, detail="No access to workspace")

            rows = await conn.fetch(
                """
                SELECT id, node_id, content, layer, confidence, created_at
                FROM memory.embeddings
                WHERE layer = 'tenant' AND tenant_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                workspace_id,
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
    workspace_id: UUID | None = Query(default=None),
) -> dict:
    """Get memory counts by layer."""
    postgres = get_postgres_driver()
    
    async with postgres.connection() as conn:
        personal_count = await conn.fetchval(
            "SELECT COUNT(*) FROM memory.embeddings WHERE user_id = $1 AND layer = 'personal'",
            user_id,
        )

        if workspace_id:
            if not await _has_workspace_access(conn, workspace_id, user_id, require_write=False):
                raise HTTPException(status_code=403, detail="No access to workspace")
            tenant_count = await conn.fetchval(
                "SELECT COUNT(*) FROM memory.embeddings WHERE layer = 'tenant' AND tenant_id = $1",
                workspace_id,
            )
        else:
            tenant_count = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM memory.embeddings e
                WHERE e.layer = 'tenant'
                  AND EXISTS (
                    SELECT 1 FROM (
                        SELECT wm.workspace_id AS workspace_id
                        FROM chat.workspace_members wm
                        JOIN chat.workspaces w ON w.id = wm.workspace_id
                        WHERE wm.user_id = $1
                          AND w.status = 'active'
                        UNION
                        SELECT tm.tenant_id AS workspace_id
                        FROM auth.tenant_members tm
                        WHERE tm.user_id = $1
                    ) allowed
                    WHERE allowed.workspace_id = e.tenant_id
                  )
                """,
                user_id,
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
    workspace_id: UUID | None = Query(default=None),
) -> dict:
    """Get memory statistics for current user."""
    # Get counts and return as status
    counts = await memory_count(user_id, workspace_id)
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


# ---------------------------------------------------------------------------
# Canvas model classes (must be before routes that use them)
# ---------------------------------------------------------------------------


class CanvasPositionUpdate(BaseModel):
    """Update canvas position for a memory."""
    x: float
    y: float


class CanvasEdgeCreate(BaseModel):
    """Create an edge between two memories."""
    source_id: UUID
    target_id: UUID
    reason: str | None = None
    confidence: float = Field(default=0.8, ge=0, le=1)


class CanvasEdgeResponse(BaseModel):
    """Canvas edge response."""
    id: UUID
    source_id: UUID
    target_id: UUID
    reason: str | None
    confidence: float
    weight: float
    connection_count: int
    created_at: datetime


class MemoryDetailResponse(BaseModel):
    """Detailed memory response including embedding preview."""
    id: UUID
    content: str
    layer: str
    confidence: float
    is_locked: bool
    canvas_x: float | None
    canvas_y: float | None
    embedding_preview: list[float]  # First 10 dimensions
    embedding_dim: int
    metadata: dict
    entities_extracted: list[str]
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Canvas edges (memory-to-memory links) - MUST be before /{id} routes!
# ---------------------------------------------------------------------------


@router.post("/edges", response_model=CanvasEdgeResponse)
async def create_edge(
    edge: CanvasEdgeCreate,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> CanvasEdgeResponse:
    """Create an edge between two memories with optional reasoning."""
    postgres = get_postgres_driver()

    async with postgres.connection() as conn:
        # Verify both memories exist and user has access
        source = await conn.fetchrow(
            "SELECT id, layer, user_id, tenant_id FROM memory.embeddings WHERE id = $1",
            edge.source_id,
        )
        target = await conn.fetchrow(
            "SELECT id, layer, user_id, tenant_id FROM memory.embeddings WHERE id = $1",
            edge.target_id,
        )

        if not source or not target:
            raise HTTPException(status_code=404, detail="Source or target memory not found")

        # They must be in the same layer/scope
        if source["layer"] != target["layer"]:
            raise HTTPException(status_code=400, detail="Cannot connect memories across layers")

        layer = source["layer"]
        mem_user_id = source["user_id"] if layer == "personal" else None
        mem_tenant_id = source["tenant_id"] if layer == "tenant" else None

        if layer == "personal":
            if source["user_id"] != user_id or target["user_id"] != user_id:
                raise HTTPException(status_code=403, detail="Access denied")
        elif layer == "tenant":
            if not await _has_workspace_access(conn, source["tenant_id"], user_id, require_write=True):
                raise HTTPException(status_code=403, detail="No write access to workspace")
        # global edges can be created by authenticated users

        # Check for existing edge and increment connection count
        existing = await conn.fetchrow(
            """
            SELECT id, connection_count, weight FROM memory.canvas_edges
            WHERE source_memory_id = $1 AND target_memory_id = $2
              AND layer = $3 AND (user_id = $4 OR user_id IS NULL)
              AND (tenant_id = $5 OR tenant_id IS NULL)
            """,
            edge.source_id,
            edge.target_id,
            layer,
            mem_user_id,
            mem_tenant_id,
        )

        if existing:
            # Increment connection count and boost weight
            new_count = existing["connection_count"] + 1
            new_weight = min(2.0, existing["weight"] + 0.15)
            await conn.execute(
                """
                UPDATE memory.canvas_edges
                SET connection_count = $1, weight = $2, reason = COALESCE($3, reason), updated_at = NOW()
                WHERE id = $4
                """,
                new_count,
                new_weight,
                edge.reason,
                existing["id"],
            )
            return CanvasEdgeResponse(
                id=existing["id"],
                source_id=edge.source_id,
                target_id=edge.target_id,
                reason=edge.reason,
                confidence=edge.confidence,
                weight=new_weight,
                connection_count=new_count,
                created_at=datetime.utcnow(),
            )

        # Create new edge
        edge_id = uuid4()
        await conn.execute(
            """
            INSERT INTO memory.canvas_edges
            (id, source_memory_id, target_memory_id, layer, user_id, tenant_id, reason, confidence, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            edge_id,
            edge.source_id,
            edge.target_id,
            layer,
            mem_user_id,
            mem_tenant_id,
            edge.reason,
            edge.confidence,
            user_id,
        )

    return CanvasEdgeResponse(
        id=edge_id,
        source_id=edge.source_id,
        target_id=edge.target_id,
        reason=edge.reason,
        confidence=edge.confidence,
        weight=1.0,
        connection_count=1,
        created_at=datetime.utcnow(),
    )


@router.get("/edges", response_model=list[CanvasEdgeResponse])
async def list_edges(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    layer: str = Query(default="personal", pattern="^(personal|tenant)$"),
    workspace_id: UUID | None = Query(default=None),
) -> list[CanvasEdgeResponse]:
    """List canvas edges for a layer."""
    postgres = get_postgres_driver()

    async with postgres.connection() as conn:
        if layer == "personal":
            rows = await conn.fetch(
                """
                SELECT id, source_memory_id, target_memory_id, reason, confidence, weight, connection_count, created_at
                FROM memory.canvas_edges
                WHERE layer = 'personal' AND user_id = $1
                ORDER BY created_at DESC
                """,
                user_id,
            )
        else:  # tenant/workspace
            if not workspace_id:
                raise HTTPException(status_code=400, detail="workspace_id required for workspace edges")
            if not await _has_workspace_access(conn, workspace_id, user_id, require_write=False):
                raise HTTPException(status_code=403, detail="No access to workspace")
            rows = await conn.fetch(
                """
                SELECT id, source_memory_id, target_memory_id, reason, confidence, weight, connection_count, created_at
                FROM memory.canvas_edges
                WHERE layer = 'tenant' AND tenant_id = $1
                ORDER BY created_at DESC
                """,
                workspace_id,
            )

    return [
        CanvasEdgeResponse(
            id=r["id"],
            source_id=r["source_memory_id"],
            target_id=r["target_memory_id"],
            reason=r["reason"],
            confidence=r["confidence"],
            weight=r["weight"],
            connection_count=r["connection_count"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


@router.delete("/edges/{edge_id}")
async def delete_edge(
    edge_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> dict:
    """Delete a canvas edge."""
    postgres = get_postgres_driver()

    async with postgres.connection() as conn:
        row = await conn.fetchrow(
            "SELECT id, layer, user_id, tenant_id FROM memory.canvas_edges WHERE id = $1",
            edge_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Edge not found")

        if row["layer"] == "personal" and row["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        if row["layer"] == "tenant":
            if not await _has_workspace_access(conn, row["tenant_id"], user_id, require_write=True):
                raise HTTPException(status_code=403, detail="No write access")

        await conn.execute("DELETE FROM memory.canvas_edges WHERE id = $1", edge_id)

    return {"message": f"Edge {edge_id} deleted"}


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
            """
            SELECT id, content, layer, confidence, created_at, updated_at, user_id, tenant_id
            FROM memory.embeddings
            WHERE id = $1
            """,
            id,
        )
    if not row:
        raise HTTPException(status_code=404, detail="Memory not found")

    if row["layer"] == "personal" and row["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if row["layer"] == "tenant":
        if row["tenant_id"] is None:
            raise HTTPException(status_code=500, detail="Invalid workspace memory")
        async with postgres.connection() as conn:
            if not await _has_workspace_access(conn, row["tenant_id"], user_id, require_write=False):
                raise HTTPException(status_code=403, detail="Access denied")

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
        row = await conn.fetchrow(
            "SELECT id, layer, user_id, tenant_id FROM memory.embeddings WHERE id = $1",
            id,
        )

        if not row:
            raise HTTPException(status_code=404, detail="Memory not found")

        if row["layer"] == "personal":
            if row["user_id"] != user_id:
                raise HTTPException(status_code=403, detail="Access denied")
        elif row["layer"] == "tenant":
            if row["tenant_id"] is None:
                raise HTTPException(status_code=500, detail="Invalid workspace memory")
            if not await _has_workspace_access(conn, row["tenant_id"], user_id, require_write=True):
                raise HTTPException(status_code=403, detail="No write access to workspace")
        # global memories are deletable by authenticated users in this implementation

        await conn.execute("DELETE FROM memory.embeddings WHERE id = $1", id)

    return {"message": f"Memory {id} deleted"}


# ---------------------------------------------------------------------------
# Path parameter routes - MUST be AFTER /edges, /count, /status routes
# ---------------------------------------------------------------------------


@router.patch("/{id}/lock")
async def toggle_lock(
    id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> dict:
    """Toggle lock state of a memory."""
    postgres = get_postgres_driver()

    async with postgres.connection() as conn:
        row = await conn.fetchrow(
            "SELECT id, layer, user_id, tenant_id, is_locked FROM memory.embeddings WHERE id = $1",
            id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Memory not found")

        if row["layer"] == "personal" and row["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        if row["layer"] == "tenant":
            if not await _has_workspace_access(conn, row["tenant_id"], user_id, require_write=True):
                raise HTTPException(status_code=403, detail="No write access")

        new_locked = not (row["is_locked"] or False)
        await conn.execute(
            "UPDATE memory.embeddings SET is_locked = $1 WHERE id = $2",
            new_locked,
            id,
        )

    return {"id": str(id), "is_locked": new_locked}


@router.patch("/{id}/position")
async def update_position(
    id: UUID,
    pos: CanvasPositionUpdate,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> dict:
    """Update canvas position of a memory."""
    postgres = get_postgres_driver()

    async with postgres.connection() as conn:
        row = await conn.fetchrow(
            "SELECT id, layer, user_id, tenant_id FROM memory.embeddings WHERE id = $1",
            id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Memory not found")

        if row["layer"] == "personal" and row["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        if row["layer"] == "tenant":
            if not await _has_workspace_access(conn, row["tenant_id"], user_id, require_write=True):
                raise HTTPException(status_code=403, detail="No write access")

        await conn.execute(
            "UPDATE memory.embeddings SET canvas_x = $1, canvas_y = $2 WHERE id = $3",
            pos.x,
            pos.y,
            id,
        )

    return {"id": str(id), "x": pos.x, "y": pos.y}


@router.post("/{id}/duplicate", response_model=MemoryResponse)
async def duplicate_memory(
    id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> MemoryResponse:
    """Duplicate a memory (creates a copy with new ID)."""
    postgres = get_postgres_driver()

    async with postgres.connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, node_id, layer, user_id, tenant_id, content, embedding, metadata, confidence
            FROM memory.embeddings WHERE id = $1
            """,
            id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Memory not found")

        if row["layer"] == "personal" and row["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        if row["layer"] == "tenant":
            if not await _has_workspace_access(conn, row["tenant_id"], user_id, require_write=True):
                raise HTTPException(status_code=403, detail="No write access")

        new_id = uuid4()
        new_node_id = f"memory_{new_id}"

        await conn.execute(
            """
            INSERT INTO memory.embeddings 
            (id, node_id, layer, user_id, tenant_id, content, embedding, metadata, confidence)
            SELECT $1, $2, layer, user_id, tenant_id, content, embedding, metadata, confidence
            FROM memory.embeddings WHERE id = $3
            """,
            new_id,
            new_node_id,
            id,
        )

    return MemoryResponse(
        id=new_id,
        content=row["content"],
        layer=row["layer"],
        confidence=row["confidence"],
        entities_extracted=[],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@router.get("/{id}/detail", response_model=MemoryDetailResponse)
async def get_memory_detail(
    id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> MemoryDetailResponse:
    """Get detailed memory including embedding preview."""
    postgres = get_postgres_driver()

    async with postgres.connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, content, layer, confidence, is_locked, canvas_x, canvas_y,
                   embedding, metadata, created_at, updated_at, user_id, tenant_id
            FROM memory.embeddings WHERE id = $1
            """,
            id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Memory not found")

        if row["layer"] == "personal" and row["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        if row["layer"] == "tenant":
            if not await _has_workspace_access(conn, row["tenant_id"], user_id, require_write=False):
                raise HTTPException(status_code=403, detail="No access")

    # Parse embedding string to get preview
    embedding_preview: list[float] = []
    embedding_dim = 0
    embedding_value = row["embedding"]
    if embedding_value is not None:
        try:
            # pgvector may return string/list/ndarray depending on driver adaptation.
            vector_values: list[float] = []
            if isinstance(embedding_value, (list, tuple)):
                vector_values = [float(value) for value in embedding_value]
            elif hasattr(embedding_value, "tolist"):
                converted = embedding_value.tolist()
                if isinstance(converted, (list, tuple)):
                    vector_values = [float(value) for value in converted]
            if not vector_values:
                emb_str = str(embedding_value).strip()
                if emb_str.startswith("[") and emb_str.endswith("]"):
                    body = emb_str[1:-1].replace("\n", " ").strip()
                    if body:
                        parts = body.split(",") if "," in body else body.split()
                        vector_values = [float(part) for part in parts if part]
            embedding_dim = len(vector_values)
            embedding_preview = vector_values[:10]
        except (TypeError, ValueError) as e:
            logger.warning("memory_embedding_preview_parse_failed", memory_id=str(id), error=str(e))

    metadata = row["metadata"] if isinstance(row["metadata"], dict) else {}

    return MemoryDetailResponse(
        id=row["id"],
        content=row["content"],
        layer=row["layer"],
        confidence=row["confidence"] or 0.5,
        is_locked=row["is_locked"] or False,
        canvas_x=row["canvas_x"],
        canvas_y=row["canvas_y"],
        embedding_preview=embedding_preview,
        embedding_dim=embedding_dim,
        metadata=metadata,
        entities_extracted=[],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
