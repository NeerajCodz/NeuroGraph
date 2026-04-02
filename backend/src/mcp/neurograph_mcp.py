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
from urllib.parse import quote
from uuid import UUID, uuid4

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.auth.jwt import create_access_token
from src.core.config import get_settings
from src.core.logging import get_logger
from src.mcp.backend_routes import BackendRouteError, BackendRoutesClient

logger = get_logger(__name__)

# Initialize FastMCP server
mcp = FastMCP("neurograph_mcp")

# Session state (managed per-connection)
_session_state: dict[str, Any] = {
    "user_id": None,
    "tenant_id": None,
    "api_key": None,
    "access_token": None,
    "backend_url": None,
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
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format",
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


class GetMemoryInput(BaseModel):
    """Input for fetching a single memory by ID."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    memory_id: str = Field(
        ...,
        description="UUID of the memory to fetch",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format",
    )


class MemoryDetailInput(BaseModel):
    """Input for fetching detailed memory payload by ID."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    memory_id: str = Field(
        ...,
        description="UUID of the memory to fetch detailed metadata for",
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
    conversation_id: Optional[str] = Field(
        default=None,
        description="Conversation ID to continue an existing thread",
    )
    layer: Optional[str] = Field(
        default=None,
        description="Chat layer: personal, workspace, or global",
    )
    include_global: bool = Field(
        default=False,
        description="Whether to include global memory context",
    )
    provider: Optional[str] = Field(
        default=None,
        description="LLM provider: 'gemini', 'nvidia', 'groq'",
    )
    model: Optional[str] = Field(
        default=None,
        description="Model ID to use (e.g., 'gemini-2.0-flash', 'llama-3.3-70b-versatile')",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format",
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
        access_token = os.environ.get("NEUROGRAPH_ACCESS_TOKEN")
        api_key = os.environ.get("NEUROGRAPH_API_KEY")
        if access_token:
            await _authenticate_token(access_token)
        elif api_key:
            await _authenticate_api_key(api_key)
        else:
            _session_state["initialized"] = True
    
    return _session_state


def _normalize_memory_layer(layer: str) -> str:
    """Map MCP-facing memory layer values to backend route values."""
    clean = layer.strip().lower()
    if clean == "workspace":
        return "tenant"
    if clean in {"personal", "tenant", "global"}:
        return clean
    return "personal"


def _resolve_workspace_id(workspace_id: Optional[str], ctx: dict[str, Any]) -> Optional[str]:
    """Resolve workspace ID from explicit input or active session context."""
    if workspace_id and workspace_id.strip():
        return workspace_id.strip()

    tenant_id = ctx.get("tenant_id")
    if isinstance(tenant_id, UUID):
        return str(tenant_id)
    if isinstance(tenant_id, str) and tenant_id.strip():
        return tenant_id.strip()
    return None


def _normalize_layers(layers: Optional[list[str]], ctx: dict[str, Any]) -> list[str]:
    """Normalize and deduplicate layer values for backend search routes."""
    source_layers = layers
    if not source_layers:
        if ctx.get("mode") == "workspace" and _resolve_workspace_id(None, ctx):
            source_layers = ["tenant"]
        else:
            source_layers = ["personal"]

    normalized: list[str] = []
    seen: set[str] = set()
    for layer in source_layers:
        mapped = _normalize_memory_layer(str(layer))
        if mapped not in seen:
            normalized.append(mapped)
            seen.add(mapped)
    return normalized


async def _call_backend(
    ctx: dict[str, Any],
    method: str,
    path: str,
    *,
    params: Any = None,
    json_body: Optional[dict[str, Any]] = None,
) -> Any:
    """Call backend API routes through the MCP route client."""
    client = BackendRoutesClient(ctx)
    return await client.request(method, path, params=params, json_body=json_body)


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
        
        row_for_mode = row
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
            row_for_mode = row
        
        workspace_row = None
        if row_for_mode:
            workspace_row = await conn.fetchrow(
                """
                SELECT workspace_id
                FROM (
                    SELECT wm.workspace_id AS workspace_id
                    FROM chat.workspace_members wm
                    JOIN chat.workspaces w ON w.id = wm.workspace_id
                    WHERE wm.user_id = $1
                      AND w.status = 'active'
                    UNION
                    SELECT tm.tenant_id AS workspace_id
                    FROM auth.tenant_members tm
                    WHERE tm.user_id = $1
                ) ws
                ORDER BY workspace_id
                LIMIT 1
                """,
                row_for_mode["user_id"],
            )
        
        if row:
            minted_access_token = create_access_token(
                data={
                    "sub": str(row["user_id"]),
                    "email": row["email"],
                    "type": "access",
                }
            )
            _session_state["user_id"] = row["user_id"]
            _session_state["tenant_id"] = row["tenant_id"]
            _session_state["api_key"] = api_key
            _session_state["access_token"] = minted_access_token
            _session_state["initialized"] = True
            if row["tenant_id"]:
                _session_state["mode"] = "workspace"
            elif workspace_row and workspace_row["workspace_id"]:
                _session_state["mode"] = "workspace"
                workspace_id = workspace_row["workspace_id"]
                if isinstance(workspace_id, UUID):
                    _session_state["tenant_id"] = workspace_id
                else:
                    try:
                        _session_state["tenant_id"] = UUID(str(workspace_id))
                    except ValueError:
                        _session_state["tenant_id"] = None
            else:
                _session_state["mode"] = "personal"
            
            logger.info(
                "mcp_authenticated",
                user_id=str(row["user_id"]),
                email=row["email"],
            )
            
            return {
                "authenticated": True,
                "user_id": str(row["user_id"]),
                "access_token": minted_access_token,
            }
        
        raise ValueError("Invalid API key")


async def _authenticate_token(access_token: str) -> dict[str, Any]:
    """Authenticate using JWT access token."""
    global _session_state
    
    from src.auth.jwt import decode_token
    
    try:
        payload = decode_token(access_token)
        user_id = UUID(payload["sub"])
        tenant_id_raw = payload.get("tenant_id") or payload.get("workspace_id")
        tenant_id: Optional[UUID] = None
        if tenant_id_raw:
            try:
                tenant_id = UUID(str(tenant_id_raw))
            except ValueError:
                tenant_id = None
        
        _session_state["user_id"] = user_id
        _session_state["tenant_id"] = tenant_id
        _session_state["api_key"] = None
        _session_state["access_token"] = access_token
        _session_state["mode"] = "workspace" if tenant_id else "personal"
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


def _to_float(value: Any, default: float = 0.0) -> float:
    """Best-effort float conversion with fallback."""
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


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
        layer = _normalize_memory_layer(params.layer.value)
        workspace_id = _resolve_workspace_id(params.workspace_id, ctx)

        payload: dict[str, Any] = {
            "content": params.content,
            "layer": layer,
            "metadata": params.metadata or {},
        }
        if layer == "tenant":
            if not workspace_id:
                return _format_error("workspace_id is required for workspace memory")
            payload["workspace_id"] = workspace_id
            payload["tenant_id"] = workspace_id

        result = await _call_backend(ctx, "POST", "/memory/remember", json_body=payload)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(result, indent=2, default=str)

        entities = result.get("entities_extracted") or []
        confidence = result.get("confidence", 1.0)
        if isinstance(confidence, (int, float)):
            confidence_text = f"{confidence:.0%}"
        else:
            confidence_text = str(confidence)
        return (
            f"✅ **Memory Stored**\n\n"
            f"- **ID**: `{result.get('id')}`\n"
            f"- **Layer**: {result.get('layer', layer)}\n"
            f"- **Confidence**: {confidence_text}\n"
            f"- **Entities Extracted**: {', '.join(entities) if entities else 'None detected'}"
        )

    except BackendRouteError as e:
        logger.error("mcp_remember_route_error", error=str(e))
        return _format_error(str(e))
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
        layers = _normalize_layers(params.layers, ctx)
        workspace_id = _resolve_workspace_id(params.workspace_id, ctx)
        if "tenant" in layers and not workspace_id:
            return _format_error("workspace_id is required when querying workspace memory")

        payload: dict[str, Any] = {
            "query": params.query,
            "layers": layers,
            "max_results": params.max_results,
            "min_confidence": params.min_confidence,
        }
        if workspace_id:
            payload["workspace_id"] = workspace_id

        results = await _call_backend(ctx, "POST", "/memory/recall", json_body=payload)
        if not isinstance(results, list) or not results:
            return "No memories found matching your query."
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({
                "query": params.query,
                "count": len(results),
                "results": [
                    {
                        "id": str(r.get("id")),
                        "content": r.get("content", ""),
                        "score": round(_to_float(r.get("score"), 0.0), 3),
                        "confidence": round(_to_float(r.get("confidence"), 0.0), 2),
                        "layer": r.get("layer"),
                    }
                    for r in results
                ],
            }, indent=2, default=str)
        
        # Markdown format
        lines = [f"## Recall Results for: \"{params.query}\"\n"]
        lines.append(f"Found **{len(results)}** relevant memories:\n")
        
        for i, r in enumerate(results, 1):
            score = _to_float(r.get("score"), 0.0)
            content = str(r.get("content", ""))
            confidence = _to_float(r.get("confidence"), 0.0)
            lines.append(f"### {i}. [{score:.2f}] {content[:100]}{'...' if len(content) > 100 else ''}")
            lines.append(f"- Layer: `{r.get('layer', 'personal')}` | Confidence: {confidence:.0%}")
            lines.append("")
        
        return "\n".join(lines)
        
    except BackendRouteError as e:
        logger.error("mcp_recall_route_error", error=str(e))
        return _format_error(str(e))
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
        layers = _normalize_layers(params.layers, ctx)
        workspace_id = _resolve_workspace_id(params.workspace_id, ctx)
        if "tenant" in layers and not workspace_id:
            return _format_error("workspace_id is required when querying workspace memory")

        query_params: list[tuple[str, str]] = [("q", params.query), ("limit", str(params.limit))]
        for layer in layers:
            query_params.append(("layers", layer))
        if params.offset > 0:
            query_params.append(("offset", str(params.offset)))
        if workspace_id:
            query_params.append(("workspace_id", workspace_id))

        query_string = "&".join(f"{k}={quote(v)}" for k, v in query_params)
        results = await _call_backend(ctx, "GET", f"/memory/search?{query_string}")
        if not isinstance(results, list) or not results:
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
                        "id": str(r.get("id")),
                        "content": r.get("content", ""),
                        "score": round(_to_float(r.get("score"), 0.0), 3),
                        "layer": r.get("layer"),
                    }
                    for r in results
                ],
            }, indent=2, default=str)
        
        # Markdown
        lines = [f"## Search Results\n"]
        lines.append(f"Query: \"{params.query}\" | Type: {params.search_type.value}\n")
        
        for i, r in enumerate(results, 1):
            score = _to_float(r.get("score"), 0.0)
            content = str(r.get("content", ""))
            lines.append(f"{i}. **[{score:.2f}]** {content[:150]}...")
        
        if len(results) == params.limit:
            lines.append(f"\n*More results available. Use offset={params.offset + params.limit}*")
        
        return "\n".join(lines)
        
    except BackendRouteError as e:
        logger.error("mcp_search_route_error", error=str(e))
        return _format_error(str(e))
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
        _ = _normalize_memory_layer(params.layer.value)
        result = await _call_backend(ctx, "DELETE", f"/memory/{quote(params.memory_id)}")

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(
                {
                    "memory_id": params.memory_id,
                    "deleted": True,
                    "result": result,
                },
                indent=2,
                default=str,
            )

        message = str(result.get("message", "")).strip() if isinstance(result, dict) else ""
        if not message:
            message = f"Memory `{params.memory_id}` deleted successfully."
        return f"✅ {message}"

    except BackendRouteError as e:
        logger.error("mcp_forget_route_error", error=str(e))
        return _format_error(str(e))
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
        layer = _normalize_memory_layer(params.layer.value)
        workspace_id = _resolve_workspace_id(params.workspace_id, ctx)
        if layer == "tenant" and not workspace_id:
            return _format_error("workspace_id is required for workspace memory")

        query_params = [
            ("layer", layer),
            ("limit", str(params.limit)),
            ("offset", str(params.offset)),
        ]
        if workspace_id:
            query_params.append(("workspace_id", workspace_id))
        query_string = "&".join(f"{k}={quote(v)}" for k, v in query_params)

        rows = await _call_backend(ctx, "GET", f"/memory/list?{query_string}")
        if not isinstance(rows, list) or not rows:
            return f"No memories found in {params.layer.value} layer."
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({
                "layer": params.layer.value,
                "count": len(rows),
                "offset": params.offset,
                "has_more": len(rows) == params.limit,
                "memories": [
                    {
                        "id": str(r.get("id")),
                        "content": str(r.get("content", ""))[:200],
                        "confidence": _to_float(r.get("confidence"), 0.0),
                        "created_at": str(r.get("created_at")),
                    }
                    for r in rows
                ],
            }, indent=2)
        
        # Markdown
        lines = [f"## {params.layer.value.title()} Memories\n"]
        for r in rows:
            content = str(r.get("content", ""))
            lines.append(f"- **{str(r.get('id'))[:8]}...** {content[:100]}...")
        
        if len(rows) == params.limit:
            lines.append(f"\n*Use offset={params.offset + params.limit} for more*")
        
        return "\n".join(lines)
        
    except BackendRouteError as e:
        logger.error("mcp_list_route_error", error=str(e))
        return _format_error(str(e))
    except Exception as e:
        logger.error("mcp_list_error", error=str(e))
        return _format_error(str(e))


@mcp.tool(
    name="neurograph_get_memory",
    annotations={
        "title": "Get Memory",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def neurograph_get_memory(params: GetMemoryInput) -> str:
    """Fetch a single memory by ID."""
    ctx = await _get_session_context()

    if not ctx.get("user_id"):
        return _format_error("Not authenticated")

    try:
        memory = await _call_backend(ctx, "GET", f"/memory/{quote(params.memory_id)}")
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(memory, indent=2, default=str)

        lines = [
            "## Memory",
            "",
            f"- **ID**: `{memory.get('id', params.memory_id)}`",
            f"- **Layer**: {memory.get('layer', 'unknown')}",
            f"- **Confidence**: {_to_float(memory.get('confidence'), 0.0):.2f}",
            f"- **Created**: {memory.get('created_at', 'unknown')}",
            f"- **Updated**: {memory.get('updated_at', 'unknown')}",
            "",
            str(memory.get("content", "")),
        ]
        return "\n".join(lines)

    except BackendRouteError as e:
        logger.error("mcp_get_memory_route_error", error=str(e))
        return _format_error(str(e))
    except Exception as e:
        logger.error("mcp_get_memory_error", error=str(e))
        return _format_error(str(e))


@mcp.tool(
    name="neurograph_memory_detail",
    annotations={
        "title": "Memory Detail",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def neurograph_memory_detail(params: MemoryDetailInput) -> str:
    """Fetch detailed memory payload by ID."""
    ctx = await _get_session_context()

    if not ctx.get("user_id"):
        return _format_error("Not authenticated")

    try:
        detail = await _call_backend(ctx, "GET", f"/memory/{quote(params.memory_id)}/detail")
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(detail, indent=2, default=str)

        lines = [
            "## Memory Detail",
            "",
            f"- **ID**: `{detail.get('id', params.memory_id)}`",
            f"- **Layer**: {detail.get('layer', 'unknown')}",
            f"- **Confidence**: {_to_float(detail.get('confidence'), 0.0):.2f}",
            f"- **Locked**: {bool(detail.get('is_locked', False))}",
            f"- **Embedding Dimension**: {int(detail.get('embedding_dim', 0) or 0)}",
            f"- **Created**: {detail.get('created_at', 'unknown')}",
            "",
            str(detail.get("content", "")),
        ]
        return "\n".join(lines)

    except BackendRouteError as e:
        logger.error("mcp_memory_detail_route_error", error=str(e))
        return _format_error(str(e))
    except Exception as e:
        logger.error("mcp_memory_detail_error", error=str(e))
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
        layer = _normalize_memory_layer(params.layer.value)
        workspace_id = _resolve_workspace_id(params.workspace_id, ctx)
        payload: dict[str, Any] = {
            "name": params.name,
            "entity_type": params.entity_type,
            "properties": params.properties or {},
            "layer": layer,
        }
        if layer == "tenant" and workspace_id:
            payload["workspace_id"] = workspace_id
            payload["tenant_id"] = workspace_id

        created = await _call_backend(ctx, "POST", "/graph/entities", json_body=payload)
        entity_id = str(created.get("id", "ent_placeholder"))
        return (
            f"✅ **Entity Created**\n\n"
            f"- **ID**: `{entity_id}`\n"
            f"- **Name**: {created.get('name', params.name)}\n"
            f"- **Type**: {created.get('type', params.entity_type)}\n"
            f"- **Layer**: {created.get('layer', layer)}"
        )
        
    except BackendRouteError as e:
        logger.error("mcp_add_entity_route_error", error=str(e))
        return _format_error(str(e))
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
        rel_type = params.relationship_type.upper().replace(" ", "_")
        payload: dict[str, Any] = {
            "source_id": params.source_entity,
            "target_id": params.target_entity,
            "relationship_type": rel_type,
            "properties": params.properties or {},
            "reason": (params.properties or {}).get("reason"),
            "confidence": params.confidence,
        }
        created = await _call_backend(ctx, "POST", "/graph/relationships", json_body=payload)
        source = created.get("source_id", params.source_entity)
        target = created.get("target_id", params.target_entity)
        created_type = created.get("type", rel_type)
        created_confidence = created.get("confidence", params.confidence)
        if isinstance(created_confidence, (int, float)):
            confidence_text = f"{created_confidence:.0%}"
        else:
            confidence_text = str(created_confidence)

        return (
            f"✅ **Relationship Created**\n\n"
            f"`{source}` → **{created_type}** → `{target}`\n"
            f"Confidence: {confidence_text}"
        )
        
    except BackendRouteError as e:
        logger.error("mcp_add_relationship_route_error", error=str(e))
        return _format_error(str(e))
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
        max_hops = max(1, params.max_hops)
        start = params.start_entity
        queue: list[tuple[str, int, list[str]]] = [(start, 0, [start])]
        visited: set[str] = {start}
        traversed_paths: list[dict[str, Any]] = []
        traversed_edges: list[dict[str, Any]] = []
        max_expansions = 60
        expansions = 0

        while queue and expansions < max_expansions:
            current, depth, path_nodes = queue.pop(0)
            if depth >= max_hops:
                continue

            relationships = await _call_backend(
                ctx,
                "GET",
                f"/graph/relationships/{quote(current)}?direction=both",
            )
            if not isinstance(relationships, list):
                continue

            for rel in relationships:
                source_id = str(rel.get("source_id", ""))
                target_id = str(rel.get("target_id", ""))
                rel_type = str(rel.get("type", "RELATED_TO"))
                confidence = _to_float(rel.get("confidence"), 1.0)

                if source_id == current and target_id:
                    next_node = target_id
                elif target_id == current and source_id:
                    next_node = source_id
                else:
                    next_node = target_id or source_id

                if not next_node:
                    continue

                traversed_edges.append(
                    {
                        "source": source_id,
                        "target": target_id,
                        "type": rel_type,
                        "confidence": confidence,
                    }
                )

                if next_node in path_nodes:
                    continue

                next_path = path_nodes + [next_node]
                traversed_paths.append(
                    {
                        "nodes": next_path,
                        "hops": len(next_path) - 1,
                        "last_relationship": rel_type,
                    }
                )

                if next_node not in visited:
                    visited.add(next_node)
                    queue.append((next_node, depth + 1, next_path))
                    expansions += 1

        if not traversed_paths:
            return f"No connections found for entity '{params.start_entity}'"
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({
                "start_entity": params.start_entity,
                "max_hops": max_hops,
                "paths_found": len(traversed_paths),
                "paths": traversed_paths,
                "edges": traversed_edges,
            }, indent=2)
        
        # Markdown format
        lines = [f"## Graph Traversal from '{params.start_entity}'\n"]
        
        seen_paths = set()
        for path in traversed_paths:
            nodes = [str(n) for n in path.get("nodes", [])]
            path_str = " -> ".join(f"**{node}**" for node in nodes)
            if path_str not in seen_paths:
                lines.append(f"- {path_str}")
                seen_paths.add(path_str)
        
        return "\n".join(lines)
        
    except BackendRouteError as e:
        logger.error("mcp_traverse_route_error", error=str(e))
        return _format_error(str(e))
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
        node = await _call_backend(ctx, "GET", f"/graph/entities/{quote(params.node_id)}")
        relationships = await _call_backend(
            ctx,
            "GET",
            f"/graph/relationships/{quote(params.node_id)}?direction=both",
        )
        connections = relationships if isinstance(relationships, list) else []
        
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
                source = str(conn.get("source_id", ""))
                target = str(conn.get("target_id", ""))
                relation = str(conn.get("type", "RELATED_TO"))
                confidence = _to_float(conn.get("confidence"), 0.8)
                reason = conn.get("reason", "")
                node_id_text = str(params.node_id)
                direction = "→" if source == node_id_text else "←"
                connected_to = target if source == node_id_text else source
                
                lines.append(
                    f"- {direction} **{relation}** {direction} "
                    f"{connected_to} "
                    f"[{confidence:.0%}]"
                )
                if reason:
                    lines.append(f"  - Reason: {reason}")
        else:
            lines.append("*No connections found*")
        
        return "\n".join(lines)
        
    except BackendRouteError as e:
        logger.error("mcp_explain_route_error", error=str(e))
        return _format_error(str(e))
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
        requested_layer = params.layer.strip().lower() if params.layer else ""
        if requested_layer == "":
            if params.workspace_id or ctx.get("mode") == "workspace":
                requested_layer = "workspace"
            else:
                requested_layer = "personal"
        if requested_layer not in {"personal", "workspace", "global"}:
            return _format_error("layer must be one of personal, workspace, global")

        workspace_id = _resolve_workspace_id(params.workspace_id, ctx)
        if requested_layer == "workspace" and not workspace_id:
            return _format_error("workspace_id required for workspace layer")

        payload: dict[str, Any] = {
            "content": params.message,
            "layer": requested_layer,
            "include_global": params.include_global,
            "agents_enabled": bool(params.use_memory),
        }
        if workspace_id:
            payload["workspace_id"] = workspace_id
        if params.conversation_id:
            payload["conversation_id"] = params.conversation_id
        if params.provider:
            payload["provider"] = params.provider
        if params.model:
            payload["model"] = params.model

        response = await _call_backend(ctx, "POST", "/chat/message", json_body=payload)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(response, indent=2, default=str)

        content = str(response.get("content", "")).strip()
        if not content:
            content = "No response content returned."

        lines = ["## Response", "", content]
        confidence = response.get("confidence")
        provider_used = response.get("provider_used")
        model_used = response.get("model_used")
        conversation_id = response.get("conversation_id")

        meta: list[str] = []
        if conversation_id:
            meta.append(f"Conversation: `{conversation_id}`")
        if provider_used and model_used:
            meta.append(f"Model: `{provider_used}/{model_used}`")
        if isinstance(confidence, (int, float)):
            meta.append(f"Confidence: {confidence:.0%}")
        if meta:
            lines.extend(["", "### Metadata", *[f"- {item}" for item in meta]])

        sources = response.get("sources")
        if isinstance(sources, list) and sources:
            lines.extend(["", "### Sources Used"])
            for source in sources[:5]:
                if not isinstance(source, dict):
                    continue
                score = source.get("score")
                content_preview = str(source.get("content", "")).strip()
                if isinstance(score, (int, float)):
                    lines.append(f"- [{score:.2f}] {content_preview[:140]}")
                else:
                    lines.append(f"- {content_preview[:140]}")

        return "\n".join(lines)

    except BackendRouteError as e:
        logger.error("mcp_chat_route_error", error=str(e))
        return _format_error(str(e))
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
        workspace_id = _resolve_workspace_id(params.workspace_id, ctx)
        query = f"?workspace_id={quote(workspace_id)}" if workspace_id else ""
        status_payload = await _call_backend(ctx, "GET", f"/memory/status{query}")
        count_payload = await _call_backend(ctx, "GET", f"/memory/count{query}")

        stats = {
            "personal_memories": count_payload.get("personal", 0),
            "workspace_memories": count_payload.get("tenant", 0),
            "global_memories": count_payload.get("global", 0),
            "total_memories": count_payload.get("total", 0),
            "entities": status_payload.get("entity_count", 0),
            "relationships": status_payload.get("relationship_count", 0),
        }

        if params.response_format == ResponseFormat.JSON:
            return json.dumps({
                "user_id": str(ctx.get("user_id")),
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
        
        lines.append(f"- Workspace Memories: **{stats.get('workspace_memories', 0)}**")
        lines.append(f"- Global Memories: **{stats.get('global_memories', 0)}**")
        lines.append(f"- Total Memories: **{stats.get('total_memories', 0)}**")
        
        lines.extend([
            f"- Graph Entities: **{stats.get('entities', 0)}**",
            f"- Relationships: **{stats.get('relationships', 0)}**",
            "\n✅ System Status: **Healthy**",
        ])
        
        return "\n".join(lines)
        
    except BackendRouteError as e:
        logger.error("mcp_status_route_error", error=str(e))
        return _format_error(str(e))
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
        workspace = await _call_backend(
            ctx,
            "GET",
            f"/workspaces/{quote(params.workspace_id)}",
        )
        workspace_name = workspace.get("name", params.workspace_id)

        _session_state["tenant_id"] = UUID(params.workspace_id)
        _session_state["mode"] = "workspace"
        
        return f"✅ Switched to workspace: **{workspace_name}**\n`{params.workspace_id}`"

    except BackendRouteError as e:
        logger.error("mcp_switch_workspace_route_error", error=str(e))
        return _format_error(str(e))
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
