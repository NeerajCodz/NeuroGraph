"""Minimal admin routes for Neo4j management."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict

from src.api.dependencies.auth import get_current_user_id
from src.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


class AdminResponse(BaseModel):
    """Admin operation response."""
    success: bool
    message: str
    data: Dict = {}


class ConfirmRequest(BaseModel):
    """Confirmation request for destructive operations."""
    confirm: str


@router.get("/status", response_model=AdminResponse)
async def admin_status(current_user_id = Depends(get_current_user_id)):
    """Get admin status and database counts."""
    try:
        from src.db.postgres import get_postgres_driver
        
        postgres = get_postgres_driver()
        async with postgres.connection() as conn:
            user_count = await conn.fetchval("SELECT COUNT(*) FROM auth.users")
            memory_count = await conn.fetchval("SELECT COUNT(*) FROM memory.embeddings") 
            edge_count = await conn.fetchval("SELECT COUNT(*) FROM memory.canvas_edges")
        
        return AdminResponse(
            success=True,
            message="Admin status retrieved",
            data={
                "postgres": {
                    "users": user_count,
                    "memories": memory_count, 
                    "edges": edge_count
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Admin status error: {e}")
        raise HTTPException(status_code=500, detail=f"Admin status failed: {str(e)}")


@router.post("/sync-neo4j", response_model=AdminResponse)
async def sync_neo4j(
    request: ConfirmRequest,
    current_user_id = Depends(get_current_user_id)
):
    """Sync data from Postgres to Neo4j."""
    
    if request.confirm != "SYNC_NEO4J":
        raise HTTPException(status_code=400, detail="Invalid confirmation. Use 'SYNC_NEO4J'")
    
    try:
        from src.db.postgres import get_postgres_driver
        from src.db.neo4j import get_neo4j_driver
        
        # Get data from Postgres
        postgres = get_postgres_driver()
        async with postgres.connection() as conn:
            memories = await conn.fetch("""
                SELECT id, node_id, content, layer, user_id, created_at
                FROM memory.embeddings ORDER BY created_at LIMIT 200
            """)
        
        # Clear and sync a subset to Neo4j (minimal test)
        neo4j = get_neo4j_driver() 
        async with neo4j.session() as session:
            await session.run("MATCH (n:Memory) DETACH DELETE n")
            
            for memory in memories:
                await session.run("""
                    CREATE (m:Memory {
                        id: $memory_id, node_id: $node_id, content: $content,
                        layer: $layer, created_at: $created_at
                    })
                """, 
                    memory_id=str(memory['id']), node_id=memory['node_id'],
                    content=memory['content'], layer=memory['layer'],
                    created_at=memory['created_at'].isoformat()
                )
            
            # Sync canvas edges for rich connections
            edges = await conn.fetch("""
                SELECT source_memory_id, target_memory_id, reason, confidence
                FROM memory.canvas_edges 
                WHERE layer = 'personal' 
                LIMIT 100
            """)
            
            edges_created = 0
            for edge in edges:
                try:
                    result = await session.run("""
                        MATCH (source:Memory {id: $source_id})
                        MATCH (target:Memory {id: $target_id})
                        CREATE (source)-[:CONNECTED_TO {
                            reason: $reason, 
                            confidence: $confidence,
                            created_at: datetime()
                        }]->(target)
                        RETURN source, target
                    """, 
                        source_id=str(edge['source_memory_id']),
                        target_id=str(edge['target_memory_id']),
                        reason=edge['reason'],
                        confidence=float(edge['confidence']) if edge['confidence'] else 0.8
                    )
                    if await result.single():
                        edges_created += 1
                except Exception as e:
                    logger.warning(f"Edge creation failed: {e}")
                    continue
        
        return AdminResponse(
            success=True,
            message="Neo4j sync completed with edges",
            data={
                "memories_created": len(memories),
                "edges_created": edges_created
            }
        )
        
    except Exception as e:
        logger.error(f"Neo4j sync error: {e}")
        raise HTTPException(status_code=500, detail=f"Neo4j sync failed: {str(e)}")