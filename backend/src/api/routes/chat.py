"""Chat routes with orchestration."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID, uuid4
import time

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from src.api.dependencies.auth import get_current_user_id
from src.core.logging import get_logger
from src.db.postgres import get_postgres_driver

router = APIRouter()
logger = get_logger(__name__)


class ChatMessage(BaseModel):
    """Chat message request."""
    content: str = Field(min_length=1, max_length=10000)
    conversation_id: UUID | None = None
    workspace_id: UUID | None = None
    layer: str = Field(default="personal", pattern="^(personal|workspace|global)$")
    include_global: bool = False
    agents_enabled: bool = True
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


class ProcessingStep(BaseModel):
    """Processing step for live updates."""
    step: int
    action: str
    status: str  # pending, running, completed, failed
    result: str | None = None
    reasoning: str | None = None
    duration_ms: int | None = None


async def save_processing_step(
    conversation_id: UUID,
    message_id: UUID | None,
    step: ProcessingStep,
) -> None:
    """Save a processing step to the database."""
    postgres = get_postgres_driver()
    try:
        async with postgres.connection() as conn:
            await conn.execute(
                """
                INSERT INTO chat.processing_steps 
                (conversation_id, message_id, step_number, action, status, result, reasoning, duration_ms, started_at, completed_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                conversation_id,
                message_id,
                step.step,
                step.action,
                step.status,
                step.result,
                step.reasoning,
                step.duration_ms,
                datetime.now(timezone.utc) if step.status == "running" else None,
                datetime.now(timezone.utc) if step.status in ("completed", "failed") else None,
            )
    except Exception as e:
        logger.warning("failed_to_save_step", error=str(e))


@router.post("/message", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> ChatResponse:
    """Send a chat message and get AI response.
    
    This endpoint:
    1. Creates/gets conversation
    2. Saves user message
    3. Searches memory for relevant context (if agents enabled)
    4. Builds structured context for the LLM
    5. Generates response using selected LLM provider/model
    6. Saves assistant message
    7. Returns response with reasoning path
    """
    from src.rag.hybrid_search import HybridSearch
    from src.rag.context_assembly import ContextAssembler
    from src.models.unified_llm import get_unified_llm
    from src.core.config import get_settings
    import json
    
    settings = get_settings()
    postgres = get_postgres_driver()
    
    provider = message.provider or settings.default_llm_provider
    model = message.model or settings.default_llm_model
    
    logger.info(
        "chat_message_received",
        user_id=str(user_id),
        layer=message.layer,
        content_length=len(message.content),
        provider=provider,
        model=model,
        agents_enabled=message.agents_enabled,
    )
    
    reasoning_path = []
    sources = []
    
    # Step 0: Create or get conversation
    step_start = time.time()
    conversation_id = message.conversation_id
    
    if not conversation_id:
        conversation_id = uuid4()
        async with postgres.connection() as conn:
            await conn.execute(
                """
                INSERT INTO chat.conversations (id, workspace_id, user_id, title)
                VALUES ($1, $2, $3, $4)
                """,
                conversation_id,
                message.workspace_id,
                user_id,
                message.content[:50] + ("..." if len(message.content) > 50 else ""),
            )
    
    # Save user message
    user_message_id = uuid4()
    async with postgres.connection() as conn:
        await conn.execute(
            """
            INSERT INTO chat.messages (id, conversation_id, role, content)
            VALUES ($1, $2, 'user', $3)
            """,
            user_message_id,
            conversation_id,
            message.content,
        )
    
    reasoning_path.append({
        "step": 1,
        "action": "conversation_init",
        "status": "completed",
        "result": f"Conversation {'created' if not message.conversation_id else 'loaded'}",
        "duration_ms": int((time.time() - step_start) * 1000),
    })
    
    try:
        # Step 1: Search memory for relevant context (if agents enabled)
        memory_results = []
        if message.agents_enabled:
            step_start = time.time()
            await save_processing_step(conversation_id, None, ProcessingStep(
                step=2, action="memory_search", status="running"
            ))
            
            hybrid_search = HybridSearch()
            layers = [message.layer if message.layer != "workspace" else "tenant"]
            if message.include_global:
                layers.append("global")
            
            memory_results = await hybrid_search.search(
                query=message.content,
                user_id=user_id,
                tenant_id=message.workspace_id,
                layers=layers,
                limit=10,
                min_confidence=0.3,
            )
            
            step_duration = int((time.time() - step_start) * 1000)
            reasoning_path.append({
                "step": 2,
                "action": "memory_search",
                "status": "completed",
                "result": f"Found {len(memory_results)} relevant memories",
                "reasoning": f"Searched {', '.join(layers)} layers with threshold 0.3",
                "duration_ms": step_duration,
            })
            
            await save_processing_step(conversation_id, None, ProcessingStep(
                step=2, action="memory_search", status="completed",
                result=f"Found {len(memory_results)} memories", duration_ms=step_duration
            ))
        
        # Step 2: Build context from memory results
        context = ""
        if memory_results:
            step_start = time.time()
            context_assembler = ContextAssembler()
            context = context_assembler.assemble(scored_nodes=memory_results)
            
            step_duration = int((time.time() - step_start) * 1000)
            reasoning_path.append({
                "step": 3,
                "action": "context_build",
                "status": "completed",
                "result": f"Built context with {len(memory_results)} nodes",
                "duration_ms": step_duration,
            })
            
            sources = [
                {
                    "node_id": str(r.node_id),
                    "content": r.content[:150] + "..." if len(r.content) > 150 else r.content,
                    "score": round(r.final_score, 3),
                    "layer": r.layer,
                }
                for r in memory_results[:5]
            ]
        
        # Step 3: Generate response
        step_start = time.time()
        await save_processing_step(conversation_id, None, ProcessingStep(
            step=4, action="generating_response", status="running"
        ))
        
        llm = get_unified_llm()
        
        if context:
            response_text = await llm.generate_with_context(
                query=message.content,
                context=context,
                provider=provider,
                model=model,
            )
            confidence = min(0.95, max(r.confidence for r in memory_results)) if memory_results else 0.7
        else:
            response_text = await llm.generate(
                prompt=f"Please help with this question: {message.content}",
                system_instruction="You are NeuroGraph, a helpful AI assistant with access to a knowledge graph. Answer concisely and helpfully.",
                provider=provider,
                model=model,
            )
            confidence = 0.5
        
        step_duration = int((time.time() - step_start) * 1000)
        reasoning_path.append({
            "step": 4,
            "action": "generate_response",
            "status": "completed",
            "result": f"Generated using {provider}/{model}",
            "reasoning": f"{'Used memory context' if context else 'No memory context available'}",
            "duration_ms": step_duration,
        })
        
        await save_processing_step(conversation_id, None, ProcessingStep(
            step=4, action="generating_response", status="completed",
            result=f"Generated with {model}", duration_ms=step_duration
        ))
        
        # Save assistant message
        assistant_message_id = uuid4()
        async with postgres.connection() as conn:
            await conn.execute(
                """
                INSERT INTO chat.messages 
                (id, conversation_id, role, content, provider, model, confidence, reasoning_path, sources)
                VALUES ($1, $2, 'assistant', $3, $4, $5, $6, $7, $8)
                """,
                assistant_message_id,
                conversation_id,
                response_text,
                provider,
                model,
                confidence,
                json.dumps(reasoning_path),
                json.dumps(sources),
            )
        
        return ChatResponse(
            id=assistant_message_id,
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
        
        error_message_id = uuid4()
        error_content = f"I apologize, but I encountered an error processing your request. Please try again."
        
        # Save error response
        async with postgres.connection() as conn:
            await conn.execute(
                """
                INSERT INTO chat.messages 
                (id, conversation_id, role, content, provider, model, confidence)
                VALUES ($1, $2, 'assistant', $3, $4, $5, $6)
                """,
                error_message_id,
                conversation_id,
                error_content,
                provider,
                model,
                0.1,
            )
        
        return ChatResponse(
            id=error_message_id,
            conversation_id=conversation_id,
            content=error_content,
            reasoning_path=[{"step": 1, "action": "error", "status": "failed", "result": str(e)[:100]}],
            sources=[],
            confidence=0.1,
            created_at=datetime.now(timezone.utc),
            model_used=model,
            provider_used=provider,
        )


@router.get("/conversations", response_model=list[dict])
async def list_conversations(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    workspace_id: UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """List user's conversations."""
    postgres = get_postgres_driver()
    
    async with postgres.connection() as conn:
        if workspace_id:
            rows = await conn.fetch(
                """
                SELECT c.*, 
                       (SELECT content FROM chat.messages WHERE conversation_id = c.id ORDER BY created_at DESC LIMIT 1) as last_message
                FROM chat.conversations c
                WHERE c.workspace_id = $1 AND c.user_id = $2 AND NOT c.is_archived
                ORDER BY COALESCE(c.last_message_at, c.created_at) DESC
                LIMIT $3 OFFSET $4
                """,
                workspace_id, user_id, limit, offset
            )
        else:
            rows = await conn.fetch(
                """
                SELECT c.*, 
                       (SELECT content FROM chat.messages WHERE conversation_id = c.id ORDER BY created_at DESC LIMIT 1) as last_message
                FROM chat.conversations c
                WHERE c.user_id = $1 AND c.workspace_id IS NULL AND NOT c.is_archived
                ORDER BY COALESCE(c.last_message_at, c.created_at) DESC
                LIMIT $2 OFFSET $3
                """,
                user_id, limit, offset
            )
    
    return [
        {
            "id": str(row["id"]),
            "workspace_id": str(row["workspace_id"]) if row["workspace_id"] else None,
            "title": row["title"],
            "message_count": row["message_count"],
            "last_message": row["last_message"][:100] if row["last_message"] else None,
            "last_message_at": row["last_message_at"].isoformat() if row["last_message_at"] else None,
            "is_pinned": row["is_pinned"],
            "created_at": row["created_at"].isoformat(),
        }
        for row in rows
    ]


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> dict:
    """Get conversation with messages."""
    postgres = get_postgres_driver()
    
    async with postgres.connection() as conn:
        conv = await conn.fetchrow(
            "SELECT * FROM chat.conversations WHERE id = $1 AND user_id = $2",
            conversation_id, user_id
        )
        
        if not conv:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = await conn.fetch(
            "SELECT * FROM chat.messages WHERE conversation_id = $1 ORDER BY created_at ASC",
            conversation_id
        )
    
    return {
        "id": str(conv["id"]),
        "title": conv["title"],
        "message_count": conv["message_count"],
        "created_at": conv["created_at"].isoformat(),
        "messages": [
            {
                "id": str(m["id"]),
                "role": m["role"],
                "content": m["content"],
                "provider": m["provider"],
                "model": m["model"],
                "confidence": m["confidence"],
                "reasoning_path": m["reasoning_path"],
                "sources": m["sources"],
                "created_at": m["created_at"].isoformat(),
            }
            for m in messages
        ],
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> dict:
    """Delete a conversation."""
    postgres = get_postgres_driver()
    
    async with postgres.connection() as conn:
        await conn.execute(
            "DELETE FROM chat.conversations WHERE id = $1 AND user_id = $2",
            conversation_id, user_id
        )
    
    return {"message": f"Conversation deleted", "id": str(conversation_id)}


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
