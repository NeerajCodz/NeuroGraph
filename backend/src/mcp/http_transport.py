"""
MCP HTTP Transport with SSE for NeuroGraph.

Provides HTTP endpoint for MCP server with authentication.
Can be mounted on the main FastAPI app or run standalone.
"""

import json
from typing import Any, AsyncGenerator, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.api.dependencies.auth import get_current_user
from src.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/mcp", tags=["MCP"])


class MCPRequest(BaseModel):
    """MCP JSON-RPC request."""
    jsonrpc: str = "2.0"
    id: Optional[str | int] = None
    method: str
    params: dict[str, Any] = {}


class MCPResponse(BaseModel):
    """MCP JSON-RPC response."""
    jsonrpc: str = "2.0"
    id: Optional[str | int] = None
    result: Optional[Any] = None
    error: Optional[dict[str, Any]] = None


def _extract_bearer_token(request: Request) -> str | None:
    """Extract bearer token from Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    parts = auth_header.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    return token or None


def _set_session_state_from_request(
    session_state: dict[str, Any],
    current_user: dict[str, Any],
    request: Request,
) -> None:
    """Sync MCP session state with the authenticated HTTP request context."""
    user_id_raw = current_user.get("id")
    if isinstance(user_id_raw, UUID):
        user_id = user_id_raw
    else:
        user_id = UUID(str(user_id_raw))

    session_state["user_id"] = user_id
    session_state["initialized"] = True

    access_token = _extract_bearer_token(request)
    if access_token:
        session_state["access_token"] = access_token
        session_state["api_key"] = None


# Import MCP tools - lazy import to avoid circular dependencies
def get_mcp_tools():
    """Get all MCP tools from neurograph_mcp module."""
    from src.mcp.neurograph_mcp import (
        neurograph_authenticate, AuthenticateInput,
        neurograph_remember, RememberInput,
        neurograph_recall, RecallInput,
        neurograph_search, SearchInput,
        neurograph_forget, ForgetInput,
        neurograph_list_memories, ListMemoriesInput,
        neurograph_add_entity, AddEntityInput,
        neurograph_add_relationship, AddRelationshipInput,
        neurograph_traverse_graph, TraverseGraphInput,
        neurograph_explain, ExplainNodeInput,
        neurograph_chat, ChatInput,
        neurograph_status, MemoryStatusInput,
        neurograph_switch_workspace, SwitchWorkspaceInput,
        _session_state,
    )
    
    return {
        "neurograph_authenticate": (neurograph_authenticate, AuthenticateInput),
        "neurograph_remember": (neurograph_remember, RememberInput),
        "neurograph_recall": (neurograph_recall, RecallInput),
        "neurograph_search": (neurograph_search, SearchInput),
        "neurograph_forget": (neurograph_forget, ForgetInput),
        "neurograph_list_memories": (neurograph_list_memories, ListMemoriesInput),
        "neurograph_add_entity": (neurograph_add_entity, AddEntityInput),
        "neurograph_add_relationship": (neurograph_add_relationship, AddRelationshipInput),
        "neurograph_traverse_graph": (neurograph_traverse_graph, TraverseGraphInput),
        "neurograph_explain": (neurograph_explain, ExplainNodeInput),
        "neurograph_chat": (neurograph_chat, ChatInput),
        "neurograph_status": (neurograph_status, MemoryStatusInput),
        "neurograph_switch_workspace": (neurograph_switch_workspace, SwitchWorkspaceInput),
    }, _session_state


def get_tool_schemas():
    """Get tool schemas for MCP tools/list response."""
    return [
        {
            "name": "neurograph_authenticate",
            "description": "Authenticate with NeuroGraph using API key or access token.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "api_key": {"type": "string", "description": "NeuroGraph API key"},
                    "access_token": {"type": "string", "description": "JWT access token"},
                },
            },
        },
        {
            "name": "neurograph_remember",
            "description": "Store information in NeuroGraph memory with automatic entity extraction.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Information to store"},
                    "layer": {"type": "string", "enum": ["personal", "workspace", "tenant"]},
                    "workspace_id": {"type": "string"},
                    "metadata": {"type": "object"},
                    "response_format": {"type": "string", "enum": ["markdown", "json"]},
                },
                "required": ["content"],
            },
        },
        {
            "name": "neurograph_recall",
            "description": "Retrieve information from memory using semantic search.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "layers": {"type": "array", "items": {"type": "string"}},
                    "workspace_id": {"type": "string"},
                    "max_results": {"type": "integer", "default": 10},
                    "min_confidence": {"type": "number", "default": 0.3},
                    "response_format": {"type": "string", "enum": ["markdown", "json"]},
                },
                "required": ["query"],
            },
        },
        {
            "name": "neurograph_search",
            "description": "Perform hybrid search across memory systems.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "search_type": {"type": "string", "enum": ["vector", "graph", "hybrid"]},
                    "layers": {"type": "array", "items": {"type": "string"}},
                    "workspace_id": {"type": "string"},
                    "limit": {"type": "integer", "default": 20},
                    "offset": {"type": "integer", "default": 0},
                    "include_graph_paths": {"type": "boolean", "default": True},
                    "response_format": {"type": "string", "enum": ["markdown", "json"]},
                },
                "required": ["query"],
            },
        },
        {
            "name": "neurograph_forget",
            "description": "Delete a memory from NeuroGraph.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "memory_id": {"type": "string"},
                    "layer": {"type": "string", "enum": ["personal", "workspace", "tenant"]},
                    "workspace_id": {"type": "string"},
                },
                "required": ["memory_id"],
            },
        },
        {
            "name": "neurograph_list_memories",
            "description": "List memories in a specific layer with pagination.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "layer": {"type": "string", "enum": ["personal", "workspace", "tenant"]},
                    "workspace_id": {"type": "string"},
                    "limit": {"type": "integer", "default": 20},
                    "offset": {"type": "integer", "default": 0},
                    "response_format": {"type": "string", "enum": ["markdown", "json"]},
                },
            },
        },
        {
            "name": "neurograph_add_entity",
            "description": "Create a new entity in the knowledge graph.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "entity_type": {"type": "string"},
                    "properties": {"type": "object"},
                    "layer": {"type": "string", "enum": ["personal", "workspace", "tenant"]},
                    "workspace_id": {"type": "string"},
                },
                "required": ["name", "entity_type"],
            },
        },
        {
            "name": "neurograph_add_relationship",
            "description": "Create a relationship between two entities.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "source_entity": {"type": "string"},
                    "target_entity": {"type": "string"},
                    "relationship_type": {"type": "string"},
                    "properties": {"type": "object"},
                    "confidence": {"type": "number", "default": 0.8},
                },
                "required": ["source_entity", "target_entity", "relationship_type"],
            },
        },
        {
            "name": "neurograph_traverse_graph",
            "description": "Traverse the knowledge graph from a starting entity.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "start_entity": {"type": "string"},
                    "max_hops": {"type": "integer", "default": 3},
                    "relationship_types": {"type": "array", "items": {"type": "string"}},
                    "response_format": {"type": "string", "enum": ["markdown", "json"]},
                },
                "required": ["start_entity"],
            },
        },
        {
            "name": "neurograph_explain",
            "description": "Explain how a node is connected in the knowledge graph.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "node_id": {"type": "string"},
                    "include_paths": {"type": "boolean", "default": True},
                    "response_format": {"type": "string", "enum": ["markdown", "json"]},
                },
                "required": ["node_id"],
            },
        },
        {
            "name": "neurograph_chat",
            "description": "Send a message to NeuroGraph AI with memory context.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "use_memory": {"type": "boolean", "default": True},
                    "workspace_id": {"type": "string"},
                    "conversation_id": {"type": "string"},
                    "layer": {"type": "string", "enum": ["personal", "workspace", "global"]},
                    "include_global": {"type": "boolean", "default": False},
                    "provider": {"type": "string"},
                    "model": {"type": "string"},
                    "response_format": {"type": "string", "enum": ["markdown", "json"]},
                },
                "required": ["message"],
            },
        },
        {
            "name": "neurograph_status",
            "description": "Get NeuroGraph memory system status and statistics.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string"},
                    "response_format": {"type": "string", "enum": ["markdown", "json"]},
                },
            },
        },
        {
            "name": "neurograph_switch_workspace",
            "description": "Switch to a different workspace context.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string"},
                },
                "required": ["workspace_id"],
            },
        },
    ]


@router.post("/invoke")
async def invoke_tool(
    request: MCPRequest,
    http_request: Request,
    current_user: dict = Depends(get_current_user),
) -> MCPResponse:
    """Invoke an MCP tool via HTTP.
    
    Accepts JSON-RPC formatted requests and returns JSON-RPC responses.
    Requires JWT authentication.
    """
    tools, session_state = get_mcp_tools()
    
    _set_session_state_from_request(session_state, current_user, http_request)
    
    if request.method == "tools/list":
        # Return list of available tools
        return MCPResponse(
            id=request.id,
            result={"tools": get_tool_schemas()},
        )
    
    if request.method == "tools/call":
        tool_name = request.params.get("name")
        arguments = request.params.get("arguments", {})
        
        if tool_name not in tools:
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32601,
                    "message": f"Unknown tool: {tool_name}",
                },
            )
        
        try:
            tool_fn, input_model = tools[tool_name]
            params = input_model(**arguments)
            result = await tool_fn(params)
            
            return MCPResponse(
                id=request.id,
                result={"content": [{"type": "text", "text": result}]},
            )
            
        except Exception as e:
            logger.error("mcp_tool_error", tool=tool_name, error=str(e))
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32603,
                    "message": str(e),
                },
            )
    
    return MCPResponse(
        id=request.id,
        error={
            "code": -32601,
            "message": f"Unknown method: {request.method}",
        },
    )


@router.get("/tools")
async def list_tools(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """List available MCP tools.
    
    Returns tool schemas for client introspection.
    """
    _, session_state = get_mcp_tools()
    _set_session_state_from_request(session_state, current_user, request)
    return {"tools": get_tool_schemas()}


@router.post("/sse")
async def mcp_sse_stream(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> StreamingResponse:
    """MCP Server-Sent Events endpoint.
    
    Implements MCP streamable HTTP transport with SSE.
    """
    tools, session_state = get_mcp_tools()
    
    _set_session_state_from_request(session_state, current_user, request)
    
    async def event_stream() -> AsyncGenerator[str, None]:
        # Send connected event
        yield f"event: connected\ndata: {json.dumps({'status': 'connected'})}\n\n"
        
        # Read request body
        body = await request.body()
        if body:
            try:
                mcp_request = MCPRequest.model_validate_json(body)
                
                if mcp_request.method == "tools/list":
                    response = MCPResponse(
                        id=mcp_request.id,
                        result={"tools": get_tool_schemas()},
                    )
                    yield f"event: message\ndata: {response.model_dump_json()}\n\n"
                    
                elif mcp_request.method == "tools/call":
                    tool_name = mcp_request.params.get("name")
                    arguments = mcp_request.params.get("arguments", {})
                    
                    if tool_name in tools:
                        try:
                            tool_fn, input_model = tools[tool_name]
                            params = input_model(**arguments)
                            result = await tool_fn(params)
                            
                            response = MCPResponse(
                                id=mcp_request.id,
                                result={"content": [{"type": "text", "text": result}]},
                            )
                        except Exception as e:
                            response = MCPResponse(
                                id=mcp_request.id,
                                error={"code": -32603, "message": str(e)},
                            )
                    else:
                        response = MCPResponse(
                            id=mcp_request.id,
                            error={"code": -32601, "message": f"Unknown tool: {tool_name}"},
                        )
                    
                    yield f"event: message\ndata: {response.model_dump_json()}\n\n"
                    
            except Exception as e:
                error_response = MCPResponse(
                    error={"code": -32700, "message": f"Parse error: {str(e)}"},
                )
                yield f"event: error\ndata: {error_response.model_dump_json()}\n\n"
        
        # Send done event
        yield f"event: done\ndata: {json.dumps({'status': 'complete'})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# API Key authentication for MCP clients
@router.post("/invoke/api-key")
async def invoke_tool_with_api_key(
    request: MCPRequest,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> MCPResponse:
    """Invoke an MCP tool using API key authentication.
    
    For MCP clients that don't support OAuth/JWT flow.
    Pass API key via X-API-Key header.
    """
    from src.mcp.neurograph_mcp import _authenticate_api_key
    
    if not x_api_key:
        return MCPResponse(
            id=request.id,
            error={"code": -32600, "message": "X-API-Key header required"},
        )
    
    try:
        # Authenticate with API key
        await _authenticate_api_key(x_api_key)
    except Exception as e:
        return MCPResponse(
            id=request.id,
            error={"code": -32600, "message": f"Authentication failed: {str(e)}"},
        )
    
    # Process request
    tools, session_state = get_mcp_tools()
    
    if request.method == "tools/list":
        return MCPResponse(
            id=request.id,
            result={"tools": get_tool_schemas()},
        )
    
    if request.method == "tools/call":
        tool_name = request.params.get("name")
        arguments = request.params.get("arguments", {})
        
        if tool_name not in tools:
            return MCPResponse(
                id=request.id,
                error={"code": -32601, "message": f"Unknown tool: {tool_name}"},
            )
        
        try:
            tool_fn, input_model = tools[tool_name]
            params = input_model(**arguments)
            result = await tool_fn(params)
            
            return MCPResponse(
                id=request.id,
                result={"content": [{"type": "text", "text": result}]},
            )
            
        except Exception as e:
            return MCPResponse(
                id=request.id,
                error={"code": -32603, "message": str(e)},
            )
    
    return MCPResponse(
        id=request.id,
        error={"code": -32601, "message": f"Unknown method: {request.method}"},
    )
