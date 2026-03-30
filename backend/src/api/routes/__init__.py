"""API routes module initialization."""

from fastapi import APIRouter

from src.api.routes.auth import router as auth_router
from src.api.routes.chat import router as chat_router
from src.api.routes.graph import router as graph_router
from src.api.routes.memory import router as memory_router

# Create main API router
api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(memory_router, prefix="/memory", tags=["memory"])
api_router.include_router(graph_router, prefix="/graph", tags=["graph"])

__all__ = ["api_router", "auth_router", "chat_router", "graph_router", "memory_router"]
