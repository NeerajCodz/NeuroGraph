"""MCP forget tool - delete information from memory."""

from typing import Any

from src.core.logging import get_logger
from src.mcp.session import MCPSession

logger = get_logger(__name__)


async def forget_tool(
    arguments: dict[str, Any],
    session: MCPSession,
) -> dict[str, Any]:
    """Delete information from memory.
    
    Removes the specified memory from the system.
    Bypasses orchestration for direct memory access.
    
    Args:
        arguments: {memory_id, layer?}
        session: MCP session
        
    Returns:
        {success, message}
    """
    memory_id = arguments.get("memory_id")
    if not memory_id:
        return {"error": "memory_id is required"}
    
    layer = arguments.get("layer", "personal")
    
    logger.info(
        "mcp_forget",
        session_id=session.session_id,
        memory_id=memory_id,
        layer=layer,
    )
    
    try:
        success = await session.memory_manager.forget(
            memory_id=memory_id,
            user_id=session.user_id,
            layer=layer,
            tenant_id=session.tenant_id,
        )
        
        if success:
            return {
                "success": True,
                "message": f"Memory {memory_id} deleted",
            }
        else:
            return {
                "success": False,
                "message": f"Memory {memory_id} not found or access denied",
            }
        
    except Exception as e:
        logger.error("mcp_forget_error", error=str(e))
        return {"error": str(e)}
