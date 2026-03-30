"""MCP recall tool - retrieve information from memory."""

from typing import Any

from src.core.logging import get_logger
from src.mcp.session import MCPSession

logger = get_logger(__name__)


async def recall_tool(
    arguments: dict[str, Any],
    session: MCPSession,
) -> dict[str, Any]:
    """Retrieve information from memory.
    
    Performs hybrid search with scoring.
    Bypasses orchestration for direct memory access.
    
    Args:
        arguments: {query, layers?, max_results?, min_confidence?}
        session: MCP session
        
    Returns:
        {results[], total_found}
    """
    query = arguments.get("query")
    if not query:
        return {"error": "query is required"}
    
    layers = arguments.get("layers", session.get_layers())
    max_results = arguments.get("max_results", 10)
    min_confidence = arguments.get("min_confidence", 0.5)
    
    logger.info(
        "mcp_recall",
        session_id=session.session_id,
        query_length=len(query),
        layers=layers,
    )
    
    try:
        scored_nodes = await session.memory_manager.recall(
            query=query,
            user_id=session.user_id,
            layers=layers,
            tenant_id=session.tenant_id,
            include_global="global" in layers,
            limit=max_results,
            min_confidence=min_confidence,
        )
        
        results = [
            {
                "content": node.content,
                "confidence": node.confidence,
                "layer": node.layer,
                "score": node.final_score,
            }
            for node in scored_nodes
        ]
        
        return {
            "results": results,
            "total_found": len(results),
        }
        
    except Exception as e:
        logger.error("mcp_recall_error", error=str(e))
        return {"error": str(e)}
