"""API routes module initialization."""

from src.api.routes.auth import router as auth_router
from src.api.routes.chat import router as chat_router
from src.api.routes.graph import router as graph_router
from src.api.routes.memory import router as memory_router

__all__ = ["auth_router", "chat_router", "graph_router", "memory_router"]
