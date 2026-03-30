"""MCP tools module initialization."""

from src.mcp.tools.remember import remember_tool
from src.mcp.tools.recall import recall_tool
from src.mcp.tools.search import search_tool
from src.mcp.tools.forget import forget_tool

TOOLS = {
    "remember": remember_tool,
    "recall": recall_tool,
    "search": search_tool,
    "forget": forget_tool,
}

__all__ = ["TOOLS", "remember_tool", "recall_tool", "search_tool", "forget_tool"]
