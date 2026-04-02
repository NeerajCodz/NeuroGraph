"""Admin endpoints for database management with secure authentication."""

import asyncio
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import JWTError, jwt
from datetime import datetime, timedelta

from src.core.config import get_settings
from src.core.logging import get_logger
from src.db.neo4j.driver import neo4j_driver
from src.db.postgres.driver import postgres_driver

logger = get_logger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminLoginRequest(BaseModel):
    """Admin login request."""
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    """Admin login response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ClearNeo4jRequest(BaseModel):
    """Request to clear Neo4j database."""
    confirm: str  # Must be "CLEAR_NEO4J"


class SyncNeo4jRequest(BaseModel):
    """Request to sync Postgres to Neo4j."""
    confirm: str  # Must be "SYNC_NEO4J"
    clear_first: bool = True


class AdminResponse(BaseModel):
    """Standard admin response."""
    success: bool
    message: str
    data: Dict[str, Any] | None = None


def create_admin_token(username: str) -> str:
    """Create JWT token for admin user."""
    settings = get_settings()
    if not settings.admin_jwt_secret:
        raise ValueError("Admin JWT secret not configured")
    
    payload = {
        "sub": username,
        "type": "admin",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(
        payload, 
        settings.admin_jwt_secret.get_secret_value(), 
        algorithm="HS256"
    )


def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify admin JWT token."""
    settings = get_settings()
    
    if not settings.admin_api_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin API is disabled"
        )
    
    if not settings.admin_jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin JWT secret not configured"
        )
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.admin_jwt_secret.get_secret_value(),
            algorithms=["HS256"]
        )
        
        if payload.get("type") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid admin token"
            )
        
        return payload.get("sub", "")
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token"
        )


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest) -> AdminLoginResponse:
    """Admin login endpoint."""
    settings = get_settings()
    
    if not settings.admin_api_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin API is disabled"
        )
    
    if not settings.admin_password:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin credentials not configured"
        )
    
    # Verify credentials
    if (request.username != settings.admin_username or 
        request.password != settings.admin_password.get_secret_value()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials"
        )
    
    # Create token
    token = create_admin_token(request.username)
    
    logger.info("admin_login_success", username=request.username)
    
    return AdminLoginResponse(
        access_token=token,
        expires_in=3600
    )


@router.post("/clear-neo4j", response_model=AdminResponse)
async def clear_neo4j(
    request: ClearNeo4jRequest,
    admin_user: str = Depends(verify_admin_token)
) -> AdminResponse:
    """Clear all data from Neo4j database."""
    if request.confirm != "CLEAR_NEO4J":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide confirm='CLEAR_NEO4J' to proceed"
        )
    
    logger.warning("admin_clearing_neo4j", user=admin_user)
    
    try:
        if not neo4j_driver.driver:
            await neo4j_driver.initialize()
        
        with neo4j_driver.driver.session() as session:
            # Delete all relationships first
            session.run("MATCH ()-[r]-() DELETE r")
            
            # Delete all nodes
            session.run("MATCH (n) DELETE n")
            
            # Verify empty
            node_count = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
        
        logger.info("admin_neo4j_cleared", user=admin_user, nodes=node_count, relationships=rel_count)
        
        return AdminResponse(
            success=True,
            message=f"Neo4j cleared successfully: {node_count} nodes, {rel_count} relationships",
            data={"nodes": node_count, "relationships": rel_count}
        )
    
    except Exception as e:
        logger.error("admin_clear_neo4j_failed", user=admin_user, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear Neo4j: {str(e)}"
        )


@router.post("/sync-neo4j", response_model=AdminResponse)
async def sync_neo4j(
    request: SyncNeo4jRequest,
    admin_user: str = Depends(verify_admin_token)
) -> AdminResponse:
    """Sync data from Postgres to Neo4j."""
    if request.confirm != "SYNC_NEO4J":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide confirm='SYNC_NEO4J' to proceed"
        )
    
    logger.info("admin_syncing_neo4j", user=admin_user, clear_first=request.clear_first)
    
    try:
        # Initialize connections
        if not neo4j_driver.driver:
            await neo4j_driver.initialize()
        
        # Clear Neo4j first if requested
        if request.clear_first:
            with neo4j_driver.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
                logger.info("neo4j_cleared_before_sync")
        
        # Load data from Postgres
        async with postgres_driver.connection() as conn:
            memories = await conn.fetch("""
                SELECT 
                    e.id,
                    e.node_id,
                    e.content,
                    e.layer,
                    e.user_id,
                    e.tenant_id,
                    u.email as user_email,
                    t.name as tenant_name
                FROM memory.embeddings e
                LEFT JOIN auth.users u ON e.user_id = u.id
                LEFT JOIN auth.tenants t ON e.tenant_id = t.id
                ORDER BY e.created_at
            """)
            
            edges = await conn.fetch("""
                SELECT 
                    ce.source_memory_id,
                    ce.target_memory_id,
                    ce.reason,
                    ce.weight,
                    ce.confidence
                FROM memory.canvas_edges ce
            """)
        
        # Create memory nodes in Neo4j
        logger.info("creating_neo4j_nodes", count=len(memories))
        with neo4j_driver.driver.session() as session:
            # Create unique constraint
            try:
                session.run("CREATE CONSTRAINT memory_id_unique IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE")
            except:
                pass
                
            for i, memory in enumerate(memories):
                session.run("""
                    MERGE (m:Memory {id: $id})
                    SET m.node_id = $node_id,
                        m.content = $content,
                        m.layer = $layer,
                        m.user_id = $user_id,
                        m.tenant_id = $tenant_id,
                        m.user_email = $user_email,
                        m.tenant_name = $tenant_name
                """, dict(memory))
                
                if (i + 1) % 50 == 0:
                    logger.info("neo4j_nodes_progress", created=i + 1, total=len(memories))
        
        # Create relationships in Neo4j
        logger.info("creating_neo4j_relationships", count=len(edges))
        with neo4j_driver.driver.session() as session:
            for i, edge in enumerate(edges):
                session.run("""
                    MATCH (source:Memory {id: $source_id})
                    MATCH (target:Memory {id: $target_id})
                    MERGE (source)-[:CONNECTED {
                        reason: $reason,
                        weight: $weight,
                        confidence: $confidence
                    }]->(target)
                """, {
                    "source_id": str(edge["source_memory_id"]),
                    "target_id": str(edge["target_memory_id"]),
                    "reason": edge["reason"],
                    "weight": edge["weight"],
                    "confidence": edge["confidence"]
                })
                
                if (i + 1) % 50 == 0:
                    logger.info("neo4j_relationships_progress", created=i + 1, total=len(edges))
        
        # Final verification
        with neo4j_driver.driver.session() as session:
            node_count = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
        
        logger.info("admin_neo4j_sync_complete", user=admin_user, nodes=node_count, relationships=rel_count)
        
        return AdminResponse(
            success=True,
            message=f"Neo4j sync complete: {node_count} nodes, {rel_count} relationships",
            data={"nodes": node_count, "relationships": rel_count}
        )
    
    except Exception as e:
        logger.error("admin_sync_neo4j_failed", user=admin_user, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync Neo4j: {str(e)}"
        )


@router.get("/status", response_model=AdminResponse)
async def admin_status(admin_user: str = Depends(verify_admin_token)) -> AdminResponse:
    """Get admin status and database counts."""
    try:
        # Check Postgres
        postgres_data = {}
        async with postgres_driver.connection() as conn:
            users_count = await conn.fetchval("SELECT COUNT(*) FROM auth.users")
            memories_count = await conn.fetchval("SELECT COUNT(*) FROM memory.embeddings")
            edges_count = await conn.fetchval("SELECT COUNT(*) FROM memory.canvas_edges")
            postgres_data = {
                "users": users_count,
                "memories": memories_count,
                "edges": edges_count
            }
        
        # Check Neo4j
        neo4j_data = {"nodes": 0, "relationships": 0}
        try:
            if not neo4j_driver.driver:
                await neo4j_driver.initialize()
            
            with neo4j_driver.driver.session() as session:
                node_count = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
                rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
                neo4j_data = {"nodes": node_count, "relationships": rel_count}
        except Exception as e:
            logger.warning("neo4j_status_check_failed", error=str(e))
            neo4j_data = {"error": str(e)}
        
        return AdminResponse(
            success=True,
            message="Admin status retrieved",
            data={
                "postgres": postgres_data,
                "neo4j": neo4j_data,
                "admin_user": admin_user
            }
        )
    
    except Exception as e:
        logger.error("admin_status_failed", user=admin_user, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get admin status: {str(e)}"
        )
    """Generic admin response."""
    success: bool
    message: str
    details: dict[str, Any] = {}


@router.post("/clear-neo4j", response_model=AdminResponse)
async def clear_neo4j(
    request: ClearNeo4jRequest,
    current_user: User = Depends(get_current_user),
) -> AdminResponse:
    """
    Clear all data from Neo4j graph database.
    
    WARNING: This deletes all nodes and relationships!
    
    Requires admin authentication.
    """
    # Check if user has role attribute (older schema compatibility)
    user_role = getattr(current_user, 'role', None)
    if user_role != "admin" and not getattr(current_user, 'is_superuser', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    if request.confirm != "CLEAR_NEO4J":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid confirmation string",
        )
    
    logger.warning("neo4j_clear_requested", user_id=str(current_user.id))
    
    try:
        async with neo4j_driver.session() as session:
            # Get counts before clearing
            result = await session.run("MATCH (n) RETURN count(n) as count")
            record = await result.single()
            node_count_before = record["count"]
            
            result = await session.run("MATCH ()-[r]->() RETURN count(r) as count")
            record = await result.single()
            rel_count_before = record["count"]
            
            # Clear all
            await session.run("MATCH (n) DETACH DELETE n")
            
            logger.info(
                "neo4j_cleared",
                nodes_deleted=node_count_before,
                relationships_deleted=rel_count_before,
            )
        
        return AdminResponse(
            success=True,
            message="Neo4j database cleared successfully",
            details={
                "nodes_deleted": node_count_before,
                "relationships_deleted": rel_count_before,
            },
        )
    
    except Exception as e:
        logger.error("neo4j_clear_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear Neo4j: {str(e)}",
        )


@router.post("/sync-neo4j", response_model=AdminResponse)
async def sync_neo4j(
    request: SyncNeo4jRequest,
    current_user: User = Depends(get_current_user),
) -> AdminResponse:
    """
    Sync Postgres memory data to Neo4j graph.
    
    Creates graph nodes from memory.embeddings and relationships from memory.canvas_edges.
    
    Requires admin authentication.
    """
    # Check if user has role attribute (older schema compatibility)
    user_role = getattr(current_user, 'role', None)
    if user_role != "admin" and not getattr(current_user, 'is_superuser', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    if request.confirm != "SYNC_NEO4J":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid confirmation string",
        )
    
    logger.warning(
        "neo4j_sync_requested",
        user_id=str(current_user.id),
        clear_first=request.clear_first,
    )
    
    try:
        # Clear Neo4j first if requested
        if request.clear_first:
            async with neo4j_driver.session() as session:
                await session.run("MATCH (n) DETACH DELETE n")
                logger.info("neo4j_cleared_for_sync")
        
        # Fetch all memories from Postgres
        async with postgres_driver.pool.acquire() as conn:
            memories = await conn.fetch(
                """SELECT id, node_id, content, layer, user_id, tenant_id, confidence, created_at
                   FROM memory.embeddings
                   ORDER BY created_at"""
            )
            
            edges = await conn.fetch(
                """SELECT id, source_memory_id, target_memory_id, layer, user_id, tenant_id, 
                          reason, confidence
                   FROM memory.canvas_edges"""
            )
        
        logger.info(
            "postgres_data_fetched",
            memory_count=len(memories),
            edge_count=len(edges),
        )
        
        # Create nodes in Neo4j
        nodes_created = 0
        async with neo4j_driver.session() as session:
            for mem in memories:
                await session.run(
                    """CREATE (n:Entity {
                        id: $node_id,
                        memory_id: $memory_id,
                        name: $content,
                        type: 'Memory',
                        layer: $layer,
                        user_id: $user_id,
                        tenant_id: $tenant_id,
                        confidence: $confidence,
                        created_at: datetime($created_at)
                    })""",
                    node_id=mem["node_id"],
                    memory_id=str(mem["id"]),
                    content=mem["content"],
                    layer=mem["layer"],
                    user_id=str(mem["user_id"]) if mem["user_id"] else None,
                    tenant_id=str(mem["tenant_id"]) if mem["tenant_id"] else None,
                    confidence=float(mem["confidence"]),
                    created_at=mem["created_at"].isoformat(),
                )
                nodes_created += 1
                
                if nodes_created % 100 == 0:
                    logger.info("neo4j_nodes_progress", created=nodes_created)
        
        logger.info("neo4j_nodes_created", count=nodes_created)
        
        # Create relationships in Neo4j
        rels_created = 0
        async with neo4j_driver.session() as session:
            for edge in edges:
                # Get node_ids for source and target
                async with postgres_driver.pool.acquire() as conn:
                    source_node = await conn.fetchrow(
                        "SELECT node_id FROM memory.embeddings WHERE id = $1",
                        edge["source_memory_id"],
                    )
                    target_node = await conn.fetchrow(
                        "SELECT node_id FROM memory.embeddings WHERE id = $1",
                        edge["target_memory_id"],
                    )
                
                if source_node and target_node:
                    await session.run(
                        """MATCH (a:Entity {id: $source_id})
                           MATCH (b:Entity {id: $target_id})
                           CREATE (a)-[:RELATES_TO {
                               edge_id: $edge_id,
                               reason: $reason,
                               confidence: $confidence,
                               layer: $layer
                           }]->(b)""",
                        source_id=source_node["node_id"],
                        target_id=target_node["node_id"],
                        edge_id=str(edge["id"]),
                        reason=edge["reason"],
                        confidence=float(edge["confidence"]),
                        layer=edge["layer"],
                    )
                    rels_created += 1
                    
                    if rels_created % 100 == 0:
                        logger.info("neo4j_rels_progress", created=rels_created)
        
        logger.info("neo4j_relationships_created", count=rels_created)
        
        # Verify Neo4j data
        async with neo4j_driver.session() as session:
            result = await session.run("MATCH (n) RETURN count(n) as count")
            record = await result.single()
            final_node_count = record["count"]
            
            result = await session.run("MATCH ()-[r]->() RETURN count(r) as count")
            record = await result.single()
            final_rel_count = record["count"]
        
        return AdminResponse(
            success=True,
            message="Neo4j sync completed successfully",
            details={
                "nodes_created": nodes_created,
                "relationships_created": rels_created,
                "final_node_count": final_node_count,
                "final_relationship_count": final_rel_count,
            },
        )
    
    except Exception as e:
        logger.error("neo4j_sync_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync Neo4j: {str(e)}",
        )
