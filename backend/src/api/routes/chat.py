"""Chat routes with orchestration."""

from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from src.api.dependencies.auth import get_current_user_id
from src.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


class ChatMessage(BaseModel):
    """Chat message request."""
    content: str = Field(min_length=1, max_length=10000)
    conversation_id: UUID | None = None
    layer: str = Field(default="personal", pattern="^(personal|tenant|global)$")
    tenant_id: UUID | None = None
    include_global: bool = False


class ChatResponse(BaseModel):
    """Chat response model."""
    id: UUID
    conversation_id: UUID
    content: str
    reasoning_path: list[dict] | None = None
    sources: list[dict] | None = None
    confidence: float
    created_at: datetime


class ConversationHistory(BaseModel):
    """Conversation history item."""
    id: UUID
    role: str
    content: str
    created_at: datetime


@router.post("/message", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> ChatResponse:
    """Send a chat message and get AI response.
    
    This endpoint uses the Groq orchestrator to classify intent,
    spawn appropriate agents, and generate a response using Gemini.
    """
    logger.info(
        "chat_message_received",
        user_id=str(user_id),
        layer=message.layer,
        content_length=len(message.content),
    )
    
    conversation_id = message.conversation_id or uuid4()
    
    # TODO: Implement full orchestration flow:
    # 1. Classify intent with Groq
    # 2. Spawn agents based on intent
    # 3. Execute agents (memory read, graph traversal, etc.)
    # 4. Build context from agent results
    # 5. Generate response with Gemini
    # 6. Update memory with new information
    
    # Placeholder response
    return ChatResponse(
        id=uuid4(),
        conversation_id=conversation_id,
        content="This is a placeholder response. Full orchestration coming soon.",
        reasoning_path=[
            {
                "step": 1,
                "action": "intent_classification",
                "result": "read",
            }
        ],
        sources=[],
        confidence=0.8,
        created_at=datetime.utcnow(),
    )


@router.get("/conversations", response_model=list[dict])
async def list_conversations(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    """List user's conversations."""
    # TODO: Fetch from database
    return []


@router.get("/conversations/{conversation_id}", response_model=list[ConversationHistory])
async def get_conversation(
    conversation_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> list[ConversationHistory]:
    """Get conversation history."""
    # TODO: Fetch from database with access check
    return []


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> dict[str, str]:
    """Delete a conversation."""
    # TODO: Implement deletion
    return {"message": f"Conversation {conversation_id} deleted"}


@router.websocket("/ws/{conversation_id}")
async def websocket_chat(
    websocket: WebSocket,
    conversation_id: UUID,
) -> None:
    """WebSocket endpoint for streaming chat."""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # TODO: Implement streaming response
            await websocket.send_json({
                "type": "message",
                "content": "Streaming response placeholder",
                "done": True,
            })
    except WebSocketDisconnect:
        logger.info("websocket_disconnected", conversation_id=str(conversation_id))
