"""MCP Server implementation for NeuroGraph."""

from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.core.config import get_settings
from src.core.logging import get_logger
from src.mcp.session import MCPSession
from src.mcp.tools import TOOLS

logger = get_logger(__name__)


class MCPServer:
    """MCP Server for direct memory access.
    
    Key characteristic: NO ORCHESTRATION
    - MCP tools bypass the Groq orchestrator
    - Direct access to Memory Manager
    - Minimal latency (<200ms target)
    - Stateless tool execution
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._server = Server("neurograph")
        self._session: MCPSession | None = None
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up MCP request handlers."""
        
        @self._server.list_tools()
        async def list_tools() -> list[Tool]:
            """Return available MCP tools."""
            return [
                Tool(
                    name="remember",
                    description="Store information in memory. Creates entities and relationships.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Information to remember",
                            },
                            "layer": {
                                "type": "string",
                                "enum": ["personal", "shared", "organization"],
                                "default": "personal",
                                "description": "Memory layer to store in",
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Additional context",
                            },
                        },
                        "required": ["content"],
                    },
                ),
                Tool(
                    name="recall",
                    description="Retrieve information from memory with scoring.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query",
                            },
                            "layers": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Layers to search",
                            },
                            "max_results": {
                                "type": "integer",
                                "default": 10,
                                "description": "Maximum results",
                            },
                            "min_confidence": {
                                "type": "number",
                                "default": 0.5,
                                "description": "Minimum confidence threshold",
                            },
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="search",
                    description="Perform hybrid search across graph and vector stores.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query",
                            },
                            "search_type": {
                                "type": "string",
                                "enum": ["vector", "graph", "hybrid"],
                                "default": "hybrid",
                            },
                            "filters": {
                                "type": "object",
                                "description": "Filter criteria",
                            },
                            "limit": {
                                "type": "integer",
                                "default": 20,
                            },
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="forget",
                    description="Delete information from memory.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "memory_id": {
                                "type": "string",
                                "description": "Memory ID to delete",
                            },
                            "layer": {
                                "type": "string",
                                "default": "personal",
                            },
                        },
                        "required": ["memory_id"],
                    },
                ),
                Tool(
                    name="add_entity",
                    description="Create a new entity in the knowledge graph.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "properties": {"type": "object"},
                            "layer": {"type": "string", "default": "personal"},
                        },
                        "required": ["name", "type"],
                    },
                ),
                Tool(
                    name="add_relationship",
                    description="Create a relationship between entities.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "source_id": {"type": "string"},
                            "target_id": {"type": "string"},
                            "relationship_type": {"type": "string"},
                            "properties": {"type": "object"},
                        },
                        "required": ["source_id", "target_id", "relationship_type"],
                    },
                ),
                Tool(
                    name="explain",
                    description="Explain how a node was derived or connected.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "node_id": {"type": "string"},
                        },
                        "required": ["node_id"],
                    },
                ),
                Tool(
                    name="switch_mode",
                    description="Switch the active memory mode.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "mode": {
                                "type": "string",
                                "enum": ["general", "organization"],
                            },
                            "tenant_id": {"type": "string"},
                        },
                        "required": ["mode"],
                    },
                ),
                Tool(
                    name="memory_status",
                    description="Get memory statistics.",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="resolve_conflict",
                    description="Resolve conflicting information.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "conflict_id": {"type": "string"},
                            "resolution": {
                                "type": "string",
                                "enum": ["keep_first", "keep_second", "merge", "discard_both"],
                            },
                        },
                        "required": ["conflict_id", "resolution"],
                    },
                ),
            ]

        @self._server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Execute an MCP tool."""
            logger.info("mcp_tool_call", tool=name, args_keys=list(arguments.keys()))
            
            if not self._session:
                return [TextContent(type="text", text="Error: No active session")]
            
            try:
                # Get tool handler
                if name in TOOLS:
                    result = await TOOLS[name](arguments, self._session)
                else:
                    result = {"error": f"Unknown tool: {name}"}
                
                import json
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                logger.error("mcp_tool_error", tool=name, error=str(e))
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def run_stdio(self) -> None:
        """Run MCP server with stdio transport."""
        self._session = MCPSession()
        await self._session.initialize()
        
        logger.info("mcp_server_starting", transport="stdio")
        
        async with stdio_server() as (read_stream, write_stream):
            await self._server.run(
                read_stream,
                write_stream,
                self._server.create_initialization_options(),
            )

    async def close(self) -> None:
        """Clean up server resources."""
        if self._session:
            await self._session.close()
            self._session = None


async def run_mcp_server() -> None:
    """Entry point for running the MCP server."""
    server = MCPServer()
    try:
        await server.run_stdio()
    finally:
        await server.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_mcp_server())
