"""API routes module initialization."""

from fastapi import APIRouter

from src.api.routes.auth import router as auth_router
from src.api.routes.chat import router as chat_router
from src.api.routes.graph import router as graph_router
from src.api.routes.memory import router as memory_router
from src.api.routes.models import router as models_router
from src.api.routes.workspaces import router as workspaces_router
from src.api.routes.conversations import router as conversations_router

# Create main API router
api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(memory_router, prefix="/memory", tags=["memory"])

api_router.include_router(graph_router, prefix="/graph", tags=["graph"])
api_router.include_router(models_router)
api_router.include_router(workspaces_router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(conversations_router, prefix="/conversations", tags=["conversations"])

__all__ = [
    "api_router",
    "auth_router",
    "chat_router",
    "graph_router",
    "memory_router",
    "models_router",
    "workspaces_router",
    "conversations_router",
]
