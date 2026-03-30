"""MCP search tool - hybrid search across graph and vector stores."""

from typing import Any

from src.core.logging import get_logger
from src.mcp.session import MCPSession

logger = get_logger(__name__)


async def search_tool(
    arguments: dict[str, Any],
    session: MCPSession,
) -> dict[str, Any]:
    """Perform hybrid search across memory stores.
    
    Supports vector, graph, or hybrid search modes.
    Bypasses orchestration for direct memory access.
    
    Args:
        arguments: {query, search_type?, filters?, limit?}
        session: MCP session
        
    Returns:
        {results[], total_found}
    """
    query = arguments.get("query")
    if not query:
        return {"error": "query is required"}
    
    search_type = arguments.get("search_type", "hybrid")
    filters = arguments.get("filters", {})
    limit = arguments.get("limit", 20)
    
    logger.info(
        "mcp_search",
        session_id=session.session_id,
        query_length=len(query),
        search_type=search_type,
    )
    
    try:
        results = await session.memory_manager.search(
            query=query,
            user_id=session.user_id,
            search_type=search_type,
            layers=session.get_layers(),
            tenant_id=session.tenant_id,
            filters=filters,
            limit=limit,
        )
        
        formatted = [
            {
                "entity_id": node.node_id,
                "name": node.name,
                "type": node.layer,
                "score": node.final_score,
                "snippet": node.content[:200] if node.content else "",
            }
            for node in results
        ]
        
        return {
            "results": formatted,
            "total_found": len(formatted),
        }
        
    except Exception as e:
        logger.error("mcp_search_error", error=str(e))
        return {"error": str(e)}
