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
    # Model selection - optional, uses defaults if not specified
    provider: str | None = Field(default=None, description="LLM provider: gemini, nvidia, groq")
    model: str | None = Field(default=None, description="Model ID to use")


class ChatResponse(BaseModel):
    """Chat response model."""
    id: UUID
    conversation_id: UUID
    content: str
    reasoning_path: list[dict] | None = None
    sources: list[dict] | None = None
    confidence: float
    created_at: datetime
    model_used: str | None = None
    provider_used: str | None = None


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
    
    This endpoint:
    1. Searches memory for relevant context
    2. Builds structured context for the LLM
    3. Generates response using selected LLM provider/model
    4. Returns response with reasoning path
    
    Model selection:
    - provider: gemini | nvidia | groq (default: from config)
    - model: specific model ID (default: provider's default)
    """
    from datetime import timezone
    from src.rag.hybrid_search import HybridSearch
    from src.rag.context_assembly import ContextAssembler
    from src.models.unified_llm import get_unified_llm
    from src.core.config import get_settings
    
    settings = get_settings()
    
    # Determine provider and model
    provider = message.provider or settings.default_llm_provider
    model = message.model or settings.default_llm_model
    
    logger.info(
        "chat_message_received",
        user_id=str(user_id),
        layer=message.layer,
        content_length=len(message.content),
        provider=provider,
        model=model,
    )
    
    conversation_id = message.conversation_id or uuid4()
    reasoning_path = []
    sources = []
    
    try:
        # Step 1: Search memory for relevant context
        hybrid_search = HybridSearch()
        layers = [message.layer]
        if message.include_global:
            layers.append("global")
        
        memory_results = await hybrid_search.search(
            query=message.content,
            user_id=user_id,
            tenant_id=message.tenant_id,
            layers=layers,
            limit=10,
            min_confidence=0.3,
        )
        
        reasoning_path.append({
            "step": 1,
            "action": "memory_search",
            "result": f"Found {len(memory_results)} relevant memories",
            "details": {
                "layers": layers,
                "top_scores": [r.final_score for r in memory_results[:3]],
            },
        })
        
        # Step 2: Build context from memory results
        context_assembler = ContextAssembler()
        context = context_assembler.assemble(
            scored_nodes=memory_results,
        )
        
        reasoning_path.append({
            "step": 2,
            "action": "context_build",
            "result": f"Built context with {len(memory_results)} nodes",
        })
        
        # Step 3: Generate response with unified LLM
        llm = get_unified_llm()
        
        if memory_results:
            response_text = await llm.generate_with_context(
                query=message.content,
                context=context,
                provider=provider,
                model=model,
            )
            confidence = min(0.95, max(r.confidence for r in memory_results))
            
            # Collect sources
            sources = [
                {
                    "node_id": str(r.node_id),
                    "content": r.content[:100],
                    "score": r.final_score,
                    "layer": r.layer,
                }
                for r in memory_results[:5]
            ]
        else:
            # No memory context - generate without context
            response_text = await llm.generate(
                prompt=f"Please help with this question: {message.content}",
                system_instruction="You are NeuroGraph, a helpful AI assistant. Answer concisely.",
                provider=provider,
                model=model,
            )
            confidence = 0.5
        
        reasoning_path.append({
            "step": 3,
            "action": "generate_response",
            "result": f"Generated response using {provider}/{model}",
            "provider": provider,
            "model": model,
        })
        
        return ChatResponse(
            id=uuid4(),
            conversation_id=conversation_id,
            content=response_text,
            reasoning_path=reasoning_path,
            sources=sources,
            confidence=confidence,
            created_at=datetime.now(timezone.utc),
            model_used=model,
            provider_used=provider,
        )
        
    except Exception as e:
        logger.error("chat_generation_failed", error=str(e), provider=provider, model=model)
        # Return error response
        return ChatResponse(
            id=uuid4(),
            conversation_id=conversation_id,
            content=f"I apologize, but I encountered an error: {str(e)[:100]}",
            reasoning_path=[{"step": 1, "action": "error", "result": str(e)[:100]}],
            sources=[],
            confidence=0.1,
            created_at=datetime.now(timezone.utc),
            model_used=model,
            provider_used=provider,
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
