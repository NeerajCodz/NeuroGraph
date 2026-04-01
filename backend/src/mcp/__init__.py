"""MCP module initialization.

NeuroGraph MCP Server - Model Context Protocol server for direct memory access.

This module provides:
- FastMCP server with all memory and graph tools
- HTTP/SSE transport for remote access
- stdio transport for local integrations (Claude Desktop, Cursor)

Usage:
    # stdio mode (for Claude Desktop)
    python -m src.mcp.neurograph_mcp
    
    # HTTP mode (for remote access)
    python -m src.mcp.neurograph_mcp --http 0.0.0.0 8001
"""

from src.mcp.server import MCPServer
from src.mcp.session import MCPSession
from src.mcp.neurograph_mcp import mcp as fastmcp_server

__all__ = ["MCPServer", "MCPSession", "fastmcp_server"]
