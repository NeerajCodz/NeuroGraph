#!/usr/bin/env python3
"""
NeuroGraph MCP Server - Model Context Protocol server for memory system access.

This server provides direct access to NeuroGraph's memory system, enabling:
- Memory operations (remember, recall, search, forget)
- Graph operations (entities, relationships, traversal)
- Agent orchestration (chat, query processing)
- Workspace management

Authentication:
- API Key: Pass via NEUROGRAPH_API_KEY environment variable
- Web Login: OAuth flow via NeuroGraph web interface

Transports:
- stdio: For local integrations (Claude Desktop, Cursor)
- HTTP: For remote access with authentication
"""

import json
import os
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)

# Initialize FastMCP server
mcp = FastMCP("neurograph_mcp")

# Session state (managed per-connection)
_session_state: dict[str, Any] = {
    "user_id": None,
    "tenant_id": None,
    "api_key": None,
    "mode": "personal",
    "include_global": True,
    "initialized": False,
}


# =============================================================================
# Enums and Input Models
# =============================================================================


class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


class MemoryLayer(str, Enum):
    """Memory layer for storage operations."""
    PERSONAL = "personal"
    WORKSPACE = "workspace"
    TENANT = "tenant"


class SearchType(str, Enum):
    """Type of search to perform."""
    VECTOR = "vector"
    GRAPH = "graph"
    HYBRID = "hybrid"


# =============================================================================
# Memory Tool Input Models
# =============================================================================


class RememberInput(BaseModel):
    """Input for storing information in memory."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    content: str = Field(
        ...,
        description="Information to store in memory (e.g., 'Alice prefers morning meetings')",
        min_length=1,
        max_length=50000,
    )
    layer: MemoryLayer = Field(
        default=MemoryLayer.PERSONAL,
        description="Memory layer: 'personal' (private), 'workspace' (shared team), or 'tenant' (organization)",
    )
    workspace_id: Optional[str] = Field(
        default=None,
        description="Workspace ID for workspace/tenant layer storage",
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional context metadata (e.g., {'source': 'meeting_notes', 'date': '2024-01-15'})",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable, 'json' for machine-readable",
    )


class RecallInput(BaseModel):
    """Input for retrieving information from memory."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    query: str = Field(
        ...,
        description="Search query to find relevant memories (e.g., 'What does Alice prefer?')",
        min_length=1,
        max_length=1000,
    )
    layers: Optional[list[str]] = Field(
        default=None,
        description="Layers to search: ['personal'], ['personal', 'workspace'], etc.",
    )
    workspace_id: Optional[str] = Field(
        default=None,
        description="Workspace ID for workspace layer search",
    )
    max_results: int = Field(
        default=10,
        description="Maximum number of results to return",
        ge=1,
        le=100,
    )
    min_confidence: float = Field(
        default=0.3,
        description="Minimum confidence threshold (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable, 'json' for machine-readable",
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class SearchInput(BaseModel):
    """Input for hybrid search across memory systems."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    query: str = Field(
        ...,
        description="Search query for finding memories and connections",
        min_length=1,
        max_length=1000,
    )
    search_type: SearchType = Field(
        default=SearchType.HYBRID,
        description="Search type: 'vector' (semantic), 'graph' (structural), 'hybrid' (both)",
    )
    layers: Optional[list[str]] = Field(
        default=None,
        description="Memory layers to search",
    )
    workspace_id: Optional[str] = Field(
        default=None,
        description="Workspace ID for scoped search",
    )
    limit: int = Field(
        default=20,
        description="Maximum results to return",
        ge=1,
        le=100,
    )
    offset: int = Field(
        default=0,
        description="Number of results to skip for pagination",
        ge=0,
    )
    include_graph_paths: bool = Field(
        default=True,
        description="Include graph traversal paths in results",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format",
    )


class ForgetInput(BaseModel):
    """Input for deleting information from memory."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    memory_id: str = Field(
        ...,
        description="UUID of the memory to delete",
    )
    layer: MemoryLayer = Field(
        default=MemoryLayer.PERSONAL,
        description="Memory layer where the memory is stored",
    )
    workspace_id: Optional[str] = Field(
        default=None,
        description="Workspace ID for workspace/tenant memories",
    )


class ListMemoriesInput(BaseModel):
    """Input for listing memories."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    layer: MemoryLayer = Field(
        default=MemoryLayer.PERSONAL,
        description="Memory layer to list",
    )
    workspace_id: Optional[str] = Field(
        default=None,
        description="Workspace ID for workspace/tenant layer",
    )
    limit: int = Field(
        default=20,
        description="Maximum results to return",
        ge=1,
        le=100,
    )
    offset: int = Field(
        default=0,
        description="Number of results to skip",
        ge=0,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format",
    )


# =============================================================================
# Graph Tool Input Models
# =============================================================================


class AddEntityInput(BaseModel):
    """Input for creating a graph entity."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    name: str = Field(
        ...,
        description="Entity name (e.g., 'Alice', 'Project X', 'Terminal')",
        min_length=1,
        max_length=200,
    )
    entity_type: str = Field(
        ...,
        description="Entity type (e.g., 'Person', 'Project', 'Tool', 'Concept')",
        min_length=1,
        max_length=50,
    )
    properties: Optional[dict[str, Any]] = Field(
        default=None,
        description="Entity properties (e.g., {'role': 'Engineer', 'department': 'Backend'})",
    )
    layer: MemoryLayer = Field(
        default=MemoryLayer.PERSONAL,
        description="Memory layer for the entity",
    )
    workspace_id: Optional[str] = Field(
        default=None,
        description="Workspace ID for workspace/tenant entities",
    )


class AddRelationshipInput(BaseModel):
    """Input for creating a relationship between entities."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    source_entity: str = Field(
        ...,
        description="Source entity name or ID",
    )
    target_entity: str = Field(
        ...,
        description="Target entity name or ID",
    )
    relationship_type: str = Field(
        ...,
        description="Relationship type (e.g., 'WORKS_WITH', 'USES', 'PREFERS', 'MANAGES')",
        min_length=1,
        max_length=50,
    )
    properties: Optional[dict[str, Any]] = Field(
        default=None,
        description="Relationship properties (e.g., {'reason': 'Daily collaboration', 'since': '2024'})",
    )
    confidence: float = Field(
        default=0.8,
        description="Confidence score for this relationship",
        ge=0.0,
        le=1.0,
    )


class TraverseGraphInput(BaseModel):
    """Input for graph traversal."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    start_entity: str = Field(
        ...,
        description="Starting entity name or ID for traversal",
    )
    max_hops: int = Field(
        default=3,
        description="Maximum number of relationship hops",
        ge=1,
        le=5,
    )
    relationship_types: Optional[list[str]] = Field(
        default=None,
        description="Filter by relationship types (e.g., ['USES', 'PREFERS'])",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format",
    )


class ExplainNodeInput(BaseModel):
    """Input for explaining a node's connections."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    node_id: str = Field(
        ...,
        description="Node ID or name to explain",
    )
    include_paths: bool = Field(
        default=True,
        description="Include reasoning paths",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format",
    )


# =============================================================================
# Agent/Chat Tool Input Models
# =============================================================================


class ChatInput(BaseModel):
    """Input for chat with AI using memory context."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    message: str = Field(
        ...,
        description="User message to send to the AI",
        min_length=1,
        max_length=10000,
    )
    use_memory: bool = Field(
        default=True,
        description="Whether to search memory for context",
    )
    workspace_id: Optional[str] = Field(
        default=None,
        description="Workspace ID for workspace context",
    )
    provider: Optional[str] = Field(
        default=None,
        description="LLM provider: 'gemini', 'nvidia', 'groq'",
    )
    model: Optional[str] = Field(
        default=None,
        description="Model ID to use (e.g., 'gemini-2.0-flash', 'llama-3.3-70b-versatile')",
    )


class MemoryStatusInput(BaseModel):
    """Input for getting memory status."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    workspace_id: Optional[str] = Field(
        default=None,
        description="Workspace ID for workspace statistics",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format",
    )


# =============================================================================
# Session Management Input Models
# =============================================================================


class AuthenticateInput(BaseModel):
    """Input for authentication."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    api_key: Optional[str] = Field(
        default=None,
        description="NeuroGraph API key for authentication",
    )
    access_token: Optional[str] = Field(
        default=None,
        description="JWT access token from web login",
    )


class SwitchWorkspaceInput(BaseModel):
    """Input for switching workspace context."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    workspace_id: str = Field(
        ...,
        description="Workspace ID to switch to",
    )


# =============================================================================
# Helper Functions
# =============================================================================


async def _get_session_context() -> dict[str, Any]:
    """Get current session context with lazy initialization."""
    global _session_state
    
    if not _session_state["initialized"]:
        # Try to load from environment
        api_key = os.environ.get("NEUROGRAPH_API_KEY")
        if api_key:
            await _authenticate_api_key(api_key)
        else:
            # Default to anonymous session with UUID(0) user
            _session_state["user_id"] = UUID(int=0)
            _session_state["initialized"] = True
    
    return _session_state


async def _authenticate_api_key(api_key: str) -> dict[str, Any]:
    """Authenticate using API key."""
    global _session_state
    
    from src.db.postgres import get_postgres_driver
    
    postgres = get_postgres_driver()
    await postgres.connect()
    
    async with postgres.connection() as conn:
        # Look up API key in database
        row = await conn.fetchrow(
            """
            SELECT ak.user_id, ak.tenant_id, ak.scopes, u.email
            FROM auth.api_keys ak
            JOIN auth.users u ON u.id = ak.user_id
            WHERE ak.key_hash = crypt($1, ak.key_hash)
              AND ak.is_active = true
              AND (ak.expires_at IS NULL OR ak.expires_at > NOW())
            """,
            api_key,
        )
        
        if not row:
            # Try direct key match (for development)
            row = await conn.fetchrow(
                """
                SELECT ak.user_id, ak.tenant_id, ak.scopes, u.email
                FROM auth.api_keys ak
                JOIN auth.users u ON u.id = ak.user_id
                WHERE ak.key_prefix = $1
                  AND ak.is_active = true
                """,
                api_key[:8] if len(api_key) >= 8 else api_key,
            )
        
        if row:
            _session_state["user_id"] = row["user_id"]
            _session_state["tenant_id"] = row["tenant_id"]
            _session_state["api_key"] = api_key
            _session_state["initialized"] = True
            
            logger.info(
                "mcp_authenticated",
                user_id=str(row["user_id"]),
                email=row["email"],
            )
            
            return {"authenticated": True, "user_id": str(row["user_id"])}
        
        raise ValueError("Invalid API key")


async def _authenticate_token(access_token: str) -> dict[str, Any]:
    """Authenticate using JWT access token."""
    global _session_state
    
    from src.auth.jwt import decode_token
    
    try:
        payload = decode_token(access_token)
        user_id = UUID(payload["sub"])
        
        _session_state["user_id"] = user_id
        _session_state["initialized"] = True
        
        logger.info("mcp_authenticated_jwt", user_id=str(user_id))
        
        return {"authenticated": True, "user_id": str(user_id)}
        
    except Exception as e:
        raise ValueError(f"Invalid access token: {e}")


def _format_memory_result(result: dict[str, Any], fmt: ResponseFormat) -> str:
    """Format a memory result for output."""
    if fmt == ResponseFormat.JSON:
        return json.dumps(result, indent=2, default=str)
    
    # Markdown format
    lines = []
    score = result.get("score", result.get("final_score", result.get("similarity", 0)))
    content = result.get("content", "")
    layer = result.get("layer", "personal")
    confidence = result.get("confidence", 1.0)
    
    lines.append(f"**[{score:.2f}]** {content[:200]}{'...' if len(content) > 200 else ''}")
    lines.append(f"  - Layer: {layer} | Confidence: {confidence:.0%}")
    
    if result.get("entities_extracted"):
        lines.append(f"  - Entities: {', '.join(result['entities_extracted'][:5])}")
    
    return "\n".join(lines)


def _format_error(error: str) -> str:
    """Format error message with suggestions."""
    suggestions = {
        "not found": "Check the memory ID is correct.",
        "unauthorized": "Run neurograph_authenticate with your API key.",
        "permission": "You don't have access to this resource.",
        "rate limit": "Wait a moment before making more requests.",
    }
    
    for key, suggestion in suggestions.items():
        if key in error.lower():
            return f"Error: {error}. {suggestion}"
    
    return f"Error: {error}"


# =============================================================================
# Memory Tools
# =============================================================================


@mcp.tool(
    name="neurograph_remember",
    annotations={
        "title": "Store Memory",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def neurograph_remember(params: RememberInput) -> str:
    """Store information in NeuroGraph memory.
    
    Creates a memory entry with automatic entity extraction and embedding generation.
    The content is processed to identify entities and relationships, which are stored
    in both the vector database (for semantic search) and graph database (for structural queries).
    
    Args:
        params: RememberInput with content, layer, and optional metadata
        
    Returns:
        Confirmation with memory ID and extracted entities
        
    Examples:
        - "Alice prefers morning meetings" -> Extracts Alice entity, stores preference
        - "Project X uses React and TypeScript" -> Extracts Project X, React, TypeScript entities
    """
    ctx = await _get_session_context()
    
    if not ctx.get("user_id"):
        return _format_error("Not authenticated. Run neurograph_authenticate first.")
    
    try:
        from src.memory.manager import MemoryManager
        from src.db.neo4j import get_neo4j_driver
        from src.db.postgres import get_postgres_driver
        
        # Ensure connections
        neo4j = get_neo4j_driver()
        postgres = get_postgres_driver()
        await neo4j.connect()
        await postgres.connect()
        
        manager = MemoryManager()
        
        # Map layer
        layer = params.layer.value
        if layer == "workspace":
            layer = "tenant"
        
        result = await manager.remember(
            content=params.content,
            user_id=ctx["user_id"],
            layer=layer,
            tenant_id=UUID(params.workspace_id) if params.workspace_id else ctx.get("tenant_id"),
            metadata=params.metadata or {},
        )
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({
                "success": True,
                "memory_id": str(result.get("id")),
                "entities_extracted": [e.get("name") for e in result.get("entities", [])],
                "confidence": result.get("confidence", 1.0),
                "layer": result.get("layer", layer),
            }, indent=2)
        
        # Markdown format
        entities = [e.get("name") for e in result.get("entities", [])]
        return (
            f"✅ **Memory Stored**\n\n"
            f"- **ID**: `{result.get('id')}`\n"
            f"- **Layer**: {result.get('layer', layer)}\n"
            f"- **Confidence**: {result.get('confidence', 1.0):.0%}\n"
            f"- **Entities Extracted**: {', '.join(entities) if entities else 'None detected'}"
        )
        
    except Exception as e:
        logger.error("mcp_remember_error", error=str(e))
        return _format_error(str(e))


@mcp.tool(
    name="neurograph_recall",
    annotations={
        "title": "Recall Memory",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def neurograph_recall(params: RecallInput) -> str:
    """Retrieve information from NeuroGraph memory using semantic search.
    
    Performs hybrid search combining vector similarity (semantic meaning) with
    graph traversal (structural relationships) to find the most relevant memories.
    Results are ranked by a composite score considering similarity, confidence, and recency.
    
    Args:
        params: RecallInput with query, layers, and search parameters
        
    Returns:
        Ranked list of relevant memories with scores and metadata
        
    Examples:
        - "What does Frank prefer?" -> Finds memories about Frank's preferences
        - "Who works with Alice?" -> Finds relationship-based memories
    """
    ctx = await _get_session_context()
    
    if not ctx.get("user_id"):
        return _format_error("Not authenticated")
    
    try:
        from src.rag.hybrid_search import HybridSearch
        from src.db.neo4j import get_neo4j_driver
        from src.db.postgres import get_postgres_driver
        
        neo4j = get_neo4j_driver()
        postgres = get_postgres_driver()
        await neo4j.connect()
        await postgres.connect()
        
        search = HybridSearch()
        
        # Determine layers
        layers = params.layers or ["personal"]
        if "workspace" in layers:
            layers = [l if l != "workspace" else "tenant" for l in layers]
        
        results = await search.search(
            query=params.query,
            user_id=ctx["user_id"],
            tenant_id=UUID(params.workspace_id) if params.workspace_id else ctx.get("tenant_id"),
            layers=layers,
            limit=params.max_results,
            min_confidence=params.min_confidence,
        )
        
        if not results:
            return "No memories found matching your query."
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({
                "query": params.query,
                "count": len(results),
                "results": [
                    {
                        "id": str(r.node_id),
                        "content": r.content,
                        "score": round(r.final_score, 3),
                        "confidence": round(r.confidence, 2),
                        "layer": r.layer,
                    }
                    for r in results
                ],
            }, indent=2, default=str)
        
        # Markdown format
        lines = [f"## Recall Results for: \"{params.query}\"\n"]
        lines.append(f"Found **{len(results)}** relevant memories:\n")
        
        for i, r in enumerate(results, 1):
            score = getattr(r, 'final_score', getattr(r, 'similarity', 0))
            lines.append(f"### {i}. [{score:.2f}] {r.content[:100]}{'...' if len(r.content) > 100 else ''}")
            lines.append(f"- Layer: `{r.layer}` | Confidence: {r.confidence:.0%}")
            lines.append("")
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.error("mcp_recall_error", error=str(e))
        return _format_error(str(e))


@mcp.tool(
    name="neurograph_search",
    annotations={
        "title": "Search Memory",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def neurograph_search(params: SearchInput) -> str:
    """Perform advanced hybrid search across NeuroGraph memory systems.
    
    Combines vector search (semantic similarity) with graph traversal (structural paths)
    to find memories and their connections. Supports pagination for large result sets.
    
    Args:
        params: SearchInput with query, search type, and pagination
        
    Returns:
        Search results with optional graph paths showing how memories connect
    """
    ctx = await _get_session_context()
    
    if not ctx.get("user_id"):
        return _format_error("Not authenticated")
    
    try:
        from src.rag.hybrid_search import HybridSearch
        from src.db.neo4j import get_neo4j_driver
        from src.db.postgres import get_postgres_driver
        
        neo4j = get_neo4j_driver()
        postgres = get_postgres_driver()
        await neo4j.connect()
        await postgres.connect()
        
        search = HybridSearch()
        
        layers = params.layers or ["personal"]
        if "workspace" in layers:
            layers = [l if l != "workspace" else "tenant" for l in layers]
        
        results = await search.search(
            query=params.query,
            user_id=ctx["user_id"],
            tenant_id=UUID(params.workspace_id) if params.workspace_id else ctx.get("tenant_id"),
            layers=layers,
            limit=params.limit,
        )
        
        if not results:
            return "No results found."
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({
                "query": params.query,
                "search_type": params.search_type.value,
                "total": len(results),
                "offset": params.offset,
                "count": len(results),
                "has_more": len(results) == params.limit,
                "results": [
                    {
                        "id": str(r.node_id),
                        "content": r.content,
                        "score": round(getattr(r, 'final_score', 0), 3),
                        "layer": r.layer,
                    }
                    for r in results
                ],
            }, indent=2, default=str)
        
        # Markdown
        lines = [f"## Search Results\n"]
        lines.append(f"Query: \"{params.query}\" | Type: {params.search_type.value}\n")
        
        for i, r in enumerate(results, 1):
            score = getattr(r, 'final_score', 0)
            lines.append(f"{i}. **[{score:.2f}]** {r.content[:150]}...")
        
        if len(results) == params.limit:
            lines.append(f"\n*More results available. Use offset={params.offset + params.limit}*")
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.error("mcp_search_error", error=str(e))
        return _format_error(str(e))


@mcp.tool(
    name="neurograph_forget",
    annotations={
        "title": "Delete Memory",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def neurograph_forget(params: ForgetInput) -> str:
    """Delete a memory from NeuroGraph.
    
    Permanently removes the specified memory from both vector and graph databases.
    This action cannot be undone.
    
    Args:
        params: ForgetInput with memory_id and layer
        
    Returns:
        Confirmation of deletion
    """
    ctx = await _get_session_context()
    
    if not ctx.get("user_id"):
        return _format_error("Not authenticated")
    
    try:
        from src.db.postgres import get_postgres_driver
        
        postgres = get_postgres_driver()
        await postgres.connect()
        
        layer = params.layer.value
        if layer == "workspace":
            layer = "tenant"
        
        async with postgres.connection() as conn:
            # Verify ownership before delete
            row = await conn.fetchrow(
                """
                SELECT id, user_id, layer FROM memory.embeddings
                WHERE id = $1 AND layer = $2
                """,
                UUID(params.memory_id),
                layer,
            )
            
            if not row:
                return _format_error(f"Memory {params.memory_id} not found")
            
            if row["layer"] == "personal" and row["user_id"] != ctx["user_id"]:
                return _format_error("Permission denied - not your memory")
            
            await conn.execute(
                "DELETE FROM memory.embeddings WHERE id = $1",
                UUID(params.memory_id),
            )
        
        return f"✅ Memory `{params.memory_id}` deleted successfully."
        
    except Exception as e:
        logger.error("mcp_forget_error", error=str(e))
        return _format_error(str(e))


@mcp.tool(
    name="neurograph_list_memories",
    annotations={
        "title": "List Memories",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def neurograph_list_memories(params: ListMemoriesInput) -> str:
    """List memories in a specific layer with pagination.
    
    Args:
        params: ListMemoriesInput with layer, pagination options
        
    Returns:
        Paginated list of memories
    """
    ctx = await _get_session_context()
    
    if not ctx.get("user_id"):
        return _format_error("Not authenticated")
    
    try:
        from src.db.postgres import get_postgres_driver
        
        postgres = get_postgres_driver()
        await postgres.connect()
        
        layer = params.layer.value
        if layer == "workspace":
            layer = "tenant"
        
        async with postgres.connection() as conn:
            if layer == "personal":
                rows = await conn.fetch(
                    """
                    SELECT id, content, confidence, created_at
                    FROM memory.embeddings
                    WHERE user_id = $1 AND layer = 'personal'
                    ORDER BY created_at DESC
                    LIMIT $2 OFFSET $3
                    """,
                    ctx["user_id"],
                    params.limit,
                    params.offset,
                )
            else:
                workspace_id = UUID(params.workspace_id) if params.workspace_id else ctx.get("tenant_id")
                rows = await conn.fetch(
                    """
                    SELECT id, content, confidence, created_at
                    FROM memory.embeddings
                    WHERE tenant_id = $1 AND layer = $2
                    ORDER BY created_at DESC
                    LIMIT $3 OFFSET $4
                    """,
                    workspace_id,
                    layer,
                    params.limit,
                    params.offset,
                )
        
        if not rows:
            return f"No memories found in {params.layer.value} layer."
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({
                "layer": params.layer.value,
                "count": len(rows),
                "offset": params.offset,
                "has_more": len(rows) == params.limit,
                "memories": [
                    {
                        "id": str(r["id"]),
                        "content": r["content"][:200],
                        "confidence": float(r["confidence"]),
                        "created_at": r["created_at"].isoformat(),
                    }
                    for r in rows
                ],
            }, indent=2)
        
        # Markdown
        lines = [f"## {params.layer.value.title()} Memories\n"]
        for r in rows:
            lines.append(f"- **{str(r['id'])[:8]}...** {r['content'][:100]}...")
        
        if len(rows) == params.limit:
            lines.append(f"\n*Use offset={params.offset + params.limit} for more*")
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.error("mcp_list_error", error=str(e))
        return _format_error(str(e))


# =============================================================================
# Graph Tools
# =============================================================================


@mcp.tool(
    name="neurograph_add_entity",
    annotations={
        "title": "Add Graph Entity",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def neurograph_add_entity(params: AddEntityInput) -> str:
    """Create a new entity in the NeuroGraph knowledge graph.
    
    Entities are nodes that represent things like people, projects, tools, or concepts.
    They can have properties and form relationships with other entities.
    
    Args:
        params: AddEntityInput with name, type, and optional properties
        
    Returns:
        Confirmation with entity ID
    """
    ctx = await _get_session_context()
    
    if not ctx.get("user_id"):
        return _format_error("Not authenticated")
    
    try:
        from src.db.neo4j import get_neo4j_driver
        
        neo4j = get_neo4j_driver()
        await neo4j.connect()
        
        entity_id = str(uuid4())
        properties = params.properties or {}
        properties["created_at"] = datetime.utcnow().isoformat()
        properties["user_id"] = str(ctx["user_id"])
        
        async with neo4j.session() as session:
            await session.run(
                """
                CREATE (e:Entity {
                    id: $id,
                    name: $name,
                    type: $type,
                    layer: $layer,
                    user_id: $user_id
                })
                SET e += $properties
                """,
                id=entity_id,
                name=params.name,
                type=params.entity_type,
                layer=params.layer.value,
                user_id=str(ctx["user_id"]),
                properties=properties,
            )
        
        return (
            f"✅ **Entity Created**\n\n"
            f"- **ID**: `{entity_id}`\n"
            f"- **Name**: {params.name}\n"
            f"- **Type**: {params.entity_type}\n"
            f"- **Layer**: {params.layer.value}"
        )
        
    except Exception as e:
        logger.error("mcp_add_entity_error", error=str(e))
        return _format_error(str(e))


@mcp.tool(
    name="neurograph_add_relationship",
    annotations={
        "title": "Add Relationship",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def neurograph_add_relationship(params: AddRelationshipInput) -> str:
    """Create a relationship between two entities in the knowledge graph.
    
    Relationships connect entities and can have properties like reason and confidence.
    Common relationship types: USES, PREFERS, WORKS_WITH, MANAGES, KNOWS.
    
    Args:
        params: AddRelationshipInput with source, target, type, and properties
        
    Returns:
        Confirmation of relationship creation
    """
    ctx = await _get_session_context()
    
    if not ctx.get("user_id"):
        return _format_error("Not authenticated")
    
    try:
        from src.db.neo4j import get_neo4j_driver
        
        neo4j = get_neo4j_driver()
        await neo4j.connect()
        
        rel_type = params.relationship_type.upper().replace(" ", "_")
        properties = params.properties or {}
        properties["confidence"] = params.confidence
        properties["created_at"] = datetime.utcnow().isoformat()
        
        async with neo4j.session() as session:
            result = await session.run(
                f"""
                MATCH (a:Entity), (b:Entity)
                WHERE (a.name = $source OR a.id = $source)
                  AND (b.name = $target OR b.id = $target)
                CREATE (a)-[r:{rel_type} $props]->(b)
                RETURN a.name AS source, b.name AS target
                """,
                source=params.source_entity,
                target=params.target_entity,
                props=properties,
            )
            record = await result.single()
            
            if not record:
                return _format_error("One or both entities not found")
        
        return (
            f"✅ **Relationship Created**\n\n"
            f"`{record['source']}` → **{rel_type}** → `{record['target']}`\n"
            f"Confidence: {params.confidence:.0%}"
        )
        
    except Exception as e:
        logger.error("mcp_add_relationship_error", error=str(e))
        return _format_error(str(e))


@mcp.tool(
    name="neurograph_traverse_graph",
    annotations={
        "title": "Traverse Graph",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def neurograph_traverse_graph(params: TraverseGraphInput) -> str:
    """Traverse the knowledge graph from a starting entity.
    
    Explores connections up to N hops away, showing the relationship paths
    and connected entities. Useful for understanding how entities relate.
    
    Args:
        params: TraverseGraphInput with start entity and traversal options
        
    Returns:
        Graph traversal results showing paths and connections
    """
    ctx = await _get_session_context()
    
    if not ctx.get("user_id"):
        return _format_error("Not authenticated")
    
    try:
        from src.db.neo4j import get_neo4j_driver
        
        neo4j = get_neo4j_driver()
        await neo4j.connect()
        
        async with neo4j.session() as session:
            result = await session.run(
                """
                MATCH path = (start:Entity)-[r*1..$hops]-(connected:Entity)
                WHERE start.name = $start_name OR start.id = $start_name
                RETURN 
                    [n IN nodes(path) | {name: n.name, type: n.type}] AS nodes,
                    [rel IN relationships(path) | {type: type(rel), confidence: rel.confidence}] AS relationships,
                    length(path) AS hops
                ORDER BY length(path)
                LIMIT 50
                """,
                start_name=params.start_entity,
                hops=params.max_hops,
            )
            records = await result.data()
        
        if not records:
            return f"No connections found for entity '{params.start_entity}'"
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({
                "start_entity": params.start_entity,
                "max_hops": params.max_hops,
                "paths_found": len(records),
                "paths": records,
            }, indent=2)
        
        # Markdown format
        lines = [f"## Graph Traversal from '{params.start_entity}'\n"]
        
        seen_paths = set()
        for record in records:
            nodes = record["nodes"]
            rels = record["relationships"]
            
            path_parts = []
            for i, node in enumerate(nodes):
                path_parts.append(f"**{node['name']}**")
                if i < len(rels):
                    rel = rels[i]
                    path_parts.append(f" →[{rel['type']}]→ ")
            
            path_str = "".join(path_parts)
            if path_str not in seen_paths:
                lines.append(f"- {path_str}")
                seen_paths.add(path_str)
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.error("mcp_traverse_error", error=str(e))
        return _format_error(str(e))


@mcp.tool(
    name="neurograph_explain",
    annotations={
        "title": "Explain Node",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def neurograph_explain(params: ExplainNodeInput) -> str:
    """Explain how a node is connected in the knowledge graph.
    
    Provides reasoning about why a node exists and how it connects to other nodes.
    Shows the derivation path and confidence scores.
    
    Args:
        params: ExplainNodeInput with node ID
        
    Returns:
        Explanation of node connections and reasoning
    """
    ctx = await _get_session_context()
    
    if not ctx.get("user_id"):
        return _format_error("Not authenticated")
    
    try:
        from src.db.neo4j import get_neo4j_driver
        
        neo4j = get_neo4j_driver()
        await neo4j.connect()
        
        async with neo4j.session() as session:
            # Get node info
            node_result = await session.run(
                """
                MATCH (n:Entity)
                WHERE n.id = $node_id OR n.name = $node_id
                RETURN n {.*, labels: labels(n)} AS node
                """,
                node_id=params.node_id,
            )
            node_record = await node_result.single()
            
            if not node_record:
                return _format_error(f"Node '{params.node_id}' not found")
            
            node = node_record["node"]
            
            # Get connections
            conn_result = await session.run(
                """
                MATCH (n:Entity)-[r]-(connected:Entity)
                WHERE n.id = $node_id OR n.name = $node_id
                RETURN 
                    type(r) AS relationship,
                    r.reason AS reason,
                    r.confidence AS confidence,
                    connected.name AS connected_to,
                    connected.type AS connected_type,
                    CASE WHEN startNode(r) = n THEN 'outgoing' ELSE 'incoming' END AS direction
                ORDER BY r.confidence DESC
                LIMIT 20
                """,
                node_id=params.node_id,
            )
            connections = await conn_result.data()
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({
                "node": node,
                "connections": connections,
            }, indent=2)
        
        # Markdown
        lines = [f"## Explanation: {node.get('name', params.node_id)}\n"]
        lines.append(f"**Type**: {node.get('type', 'Unknown')}")
        lines.append(f"**Layer**: {node.get('layer', 'personal')}")
        
        if node.get("created_at"):
            lines.append(f"**Created**: {node['created_at']}")
        
        lines.append("\n### Connections\n")
        
        if connections:
            for conn in connections:
                direction = "→" if conn["direction"] == "outgoing" else "←"
                confidence = conn.get("confidence", 0.8)
                reason = conn.get("reason", "")
                
                lines.append(
                    f"- {direction} **{conn['relationship']}** {direction} "
                    f"{conn['connected_to']} ({conn['connected_type']}) "
                    f"[{confidence:.0%}]"
                )
                if reason:
                    lines.append(f"  - Reason: {reason}")
        else:
            lines.append("*No connections found*")
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.error("mcp_explain_error", error=str(e))
        return _format_error(str(e))


# =============================================================================
# Chat/Agent Tools
# =============================================================================


@mcp.tool(
    name="neurograph_chat",
    annotations={
        "title": "Chat with AI",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def neurograph_chat(params: ChatInput) -> str:
    """Send a message to NeuroGraph AI with memory context.
    
    Uses the full pipeline: memory search → graph traversal → context assembly → LLM.
    The AI has access to your memories and can reason about connections.
    
    Args:
        params: ChatInput with message and optional configuration
        
    Returns:
        AI response with reasoning and cited sources
    """
    ctx = await _get_session_context()
    
    if not ctx.get("user_id"):
        return _format_error("Not authenticated")
    
    try:
        from src.rag.hybrid_search import HybridSearch
        from src.rag.context_assembly import ContextAssembler
        from src.models.unified_llm import get_unified_llm
        from src.core.config import get_settings
        from src.db.neo4j import get_neo4j_driver
        from src.db.postgres import get_postgres_driver
        
        settings = get_settings()
        neo4j = get_neo4j_driver()
        postgres = get_postgres_driver()
        await neo4j.connect()
        await postgres.connect()
        
        context = ""
        sources = []
        
        if params.use_memory:
            # Search memory for context
            search = HybridSearch()
            layers = ["personal"]
            if params.workspace_id:
                layers.append("tenant")
            
            results = await search.search(
                query=params.message,
                user_id=ctx["user_id"],
                tenant_id=UUID(params.workspace_id) if params.workspace_id else ctx.get("tenant_id"),
                layers=layers,
                limit=10,
            )
            
            if results:
                assembler = ContextAssembler()
                context = assembler.assemble(scored_nodes=results)
                sources = [
                    {
                        "content": r.content[:100],
                        "score": round(getattr(r, 'final_score', 0), 2),
                    }
                    for r in results[:5]
                ]
        
        # Generate response
        provider = params.provider or settings.default_llm_provider
        model = params.model or settings.default_llm_model
        
        llm = get_unified_llm()
        
        if context:
            prompt = (
                f"Context:\n{context}\n\n---\n\n"
                f"User: {params.message}\n\n"
                "Answer using the context above. Cite relevant memories."
            )
            system = "You are NeuroGraph AI with structured memory. Use context to answer."
        else:
            prompt = params.message
            system = "You are NeuroGraph AI, a helpful assistant."
        
        response = await llm.generate(
            prompt=prompt,
            system_instruction=system,
            provider=provider,
            model=model,
        )
        
        # Format response
        output = f"## Response\n\n{response}\n"
        
        if sources:
            output += "\n### Sources Used\n"
            for s in sources:
                output += f"- [{s['score']:.2f}] {s['content']}...\n"
        
        return output
        
    except Exception as e:
        logger.error("mcp_chat_error", error=str(e))
        return _format_error(str(e))


@mcp.tool(
    name="neurograph_status",
    annotations={
        "title": "Memory Status",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def neurograph_status(params: MemoryStatusInput) -> str:
    """Get NeuroGraph memory system status and statistics.
    
    Shows memory counts, entity counts, and system health information.
    
    Args:
        params: MemoryStatusInput with optional workspace scope
        
    Returns:
        Memory statistics and status information
    """
    ctx = await _get_session_context()
    
    if not ctx.get("user_id"):
        return _format_error("Not authenticated")
    
    try:
        from src.db.postgres import get_postgres_driver
        from src.db.neo4j import get_neo4j_driver
        
        postgres = get_postgres_driver()
        neo4j = get_neo4j_driver()
        await postgres.connect()
        await neo4j.connect()
        
        stats = {}
        
        # Get memory counts from postgres
        async with postgres.connection() as conn:
            personal_count = await conn.fetchval(
                "SELECT COUNT(*) FROM memory.embeddings WHERE user_id = $1 AND layer = 'personal'",
                ctx["user_id"],
            )
            stats["personal_memories"] = personal_count
            
            if params.workspace_id or ctx.get("tenant_id"):
                ws_id = UUID(params.workspace_id) if params.workspace_id else ctx["tenant_id"]
                workspace_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM memory.embeddings WHERE tenant_id = $1 AND layer = 'tenant'",
                    ws_id,
                )
                stats["workspace_memories"] = workspace_count
        
        # Get entity counts from neo4j
        async with neo4j.session() as session:
            result = await session.run(
                """
                MATCH (e:Entity)
                WHERE e.user_id = $user_id
                RETURN count(e) AS entity_count
                """,
                user_id=str(ctx["user_id"]),
            )
            record = await result.single()
            stats["entities"] = record["entity_count"] if record else 0
            
            rel_result = await session.run(
                """
                MATCH (e:Entity)-[r]-()
                WHERE e.user_id = $user_id
                RETURN count(DISTINCT r) AS relationship_count
                """,
                user_id=str(ctx["user_id"]),
            )
            rel_record = await rel_result.single()
            stats["relationships"] = rel_record["relationship_count"] if rel_record else 0
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({
                "user_id": str(ctx["user_id"]),
                "statistics": stats,
                "status": "healthy",
            }, indent=2)
        
        # Markdown
        lines = [
            "## NeuroGraph Status\n",
            f"**User**: `{str(ctx['user_id'])[:8]}...`\n",
            "### Memory Statistics",
            f"- Personal Memories: **{stats.get('personal_memories', 0)}**",
        ]
        
        if "workspace_memories" in stats:
            lines.append(f"- Workspace Memories: **{stats['workspace_memories']}**")
        
        lines.extend([
            f"- Graph Entities: **{stats.get('entities', 0)}**",
            f"- Relationships: **{stats.get('relationships', 0)}**",
            "\n✅ System Status: **Healthy**",
        ])
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.error("mcp_status_error", error=str(e))
        return _format_error(str(e))


# =============================================================================
# Authentication Tools
# =============================================================================


@mcp.tool(
    name="neurograph_authenticate",
    annotations={
        "title": "Authenticate",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def neurograph_authenticate(params: AuthenticateInput) -> str:
    """Authenticate with NeuroGraph using API key or access token.
    
    Required before using other tools. You can authenticate using:
    - API Key: Generated in NeuroGraph settings
    - Access Token: JWT from web login
    
    Args:
        params: AuthenticateInput with api_key or access_token
        
    Returns:
        Authentication status
    """
    try:
        if params.api_key:
            result = await _authenticate_api_key(params.api_key)
            return f"✅ Authenticated with API key.\nUser ID: `{result['user_id']}`"
        
        if params.access_token:
            result = await _authenticate_token(params.access_token)
            return f"✅ Authenticated with access token.\nUser ID: `{result['user_id']}`"
        
        # Try environment variable
        api_key = os.environ.get("NEUROGRAPH_API_KEY")
        if api_key:
            result = await _authenticate_api_key(api_key)
            return f"✅ Authenticated from NEUROGRAPH_API_KEY.\nUser ID: `{result['user_id']}`"
        
        return _format_error(
            "No credentials provided. "
            "Pass api_key, access_token, or set NEUROGRAPH_API_KEY environment variable."
        )
        
    except Exception as e:
        return _format_error(str(e))


@mcp.tool(
    name="neurograph_switch_workspace",
    annotations={
        "title": "Switch Workspace",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def neurograph_switch_workspace(params: SwitchWorkspaceInput) -> str:
    """Switch to a different workspace context.
    
    Changes the active workspace for subsequent operations.
    Memories stored/recalled will be scoped to this workspace.
    
    Args:
        params: SwitchWorkspaceInput with workspace_id
        
    Returns:
        Confirmation of workspace switch
    """
    global _session_state
    
    ctx = await _get_session_context()
    
    if not ctx.get("user_id"):
        return _format_error("Not authenticated")
    
    try:
        from src.db.postgres import get_postgres_driver
        
        postgres = get_postgres_driver()
        await postgres.connect()
        
        # Verify workspace access
        async with postgres.connection() as conn:
            access = await conn.fetchrow(
                """
                SELECT w.id, w.name FROM chat.workspaces w
                LEFT JOIN chat.workspace_members wm ON wm.workspace_id = w.id
                WHERE w.id = $1 AND (wm.user_id = $2 OR w.created_by = $2)
                """,
                UUID(params.workspace_id),
                ctx["user_id"],
            )
            
            if not access:
                return _format_error(f"Workspace {params.workspace_id} not found or no access")
        
        _session_state["tenant_id"] = UUID(params.workspace_id)
        _session_state["mode"] = "workspace"
        
        return f"✅ Switched to workspace: **{access['name']}**\n`{params.workspace_id}`"
        
    except Exception as e:
        return _format_error(str(e))


# =============================================================================
# Server Entry Points
# =============================================================================


def run_stdio() -> None:
    """Run MCP server with stdio transport (for Claude Desktop, Cursor)."""
    import asyncio
    asyncio.run(mcp.run_stdio_async())


def run_http(host: str = "127.0.0.1", port: int = 8001) -> None:
    """Run MCP server with HTTP transport (for remote access)."""
    import uvicorn
    from mcp.server.fastmcp import create_sse_server
    
    app = create_sse_server(mcp)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--http":
        host = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
        port = int(sys.argv[3]) if len(sys.argv) > 3 else 8001
        print(f"Starting NeuroGraph MCP server on http://{host}:{port}")
        run_http(host, port)
    else:
        run_stdio()
