"""MCP remember tool - store information in memory."""

from typing import Any

from src.core.logging import get_logger
from src.mcp.session import MCPSession

logger = get_logger(__name__)


async def remember_tool(
    arguments: dict[str, Any],
    session: MCPSession,
) -> dict[str, Any]:
    """Store information in memory.
    
    Creates entities and relationships from the content.
    Bypasses orchestration for direct memory access.
    
    Args:
        arguments: {content, layer?, metadata?}
        session: MCP session
        
    Returns:
        {memory_id, entities_extracted, confidence, layer}
    """
    content = arguments.get("content")
    if not content:
        return {"error": "content is required"}
    
    layer = arguments.get("layer", "personal")
    metadata = arguments.get("metadata", {})
    
    # Map "shared" to "tenant" and "organization" to "global"
    layer_mapping = {
        "shared": "tenant",
        "organization": "global",
    }
    layer = layer_mapping.get(layer, layer)
    
    logger.info(
        "mcp_remember",
        session_id=session.session_id,
        layer=layer,
        content_length=len(content),
    )
    
    try:
        result = await session.memory_manager.remember(
            content=content,
            user_id=session.user_id,
            layer=layer,
            tenant_id=session.tenant_id,
            metadata=metadata,
        )
        
        return {
            "memory_id": result.get("id"),
            "entities_extracted": [e.get("name") for e in result.get("entities", [])],
            "confidence": result.get("confidence", 1.0),
            "layer": result.get("layer", layer),
        }
        
    except Exception as e:
        logger.error("mcp_remember_error", error=str(e))
        return {"error": str(e)}
