"""Chat routes with orchestration."""

from datetime import datetime, timezone
from typing import Annotated, Any
from uuid import UUID, uuid4
import json
import time

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel, Field

from src.api.dependencies.auth import get_current_user_id
from src.core.logging import get_logger
from src.db.postgres import get_postgres_driver

router = APIRouter()
logger = get_logger(__name__)


def _parse_json_list(value: object) -> list:
    """Parse JSON-list fields that may arrive as list, JSON string, or None."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []
    return []


def _provider_candidate_order(requested_provider: str) -> list[str]:
    """Build ordered provider candidates for failover attempts."""
    requested = requested_provider.lower().strip()
    ordered = [requested, "gemini", "groq", "nvidia"]
    deduped: list[str] = []
    seen: set[str] = set()
    for provider in ordered:
        if provider not in seen:
            seen.add(provider)
            deduped.append(provider)
    return deduped


def _default_model_for_provider(provider: str, settings: Any) -> str:
    """Resolve default model for a specific provider."""
    if provider == "gemini":
        return settings.gemini_model_flash
    if provider == "groq":
        return settings.groq_model
    if provider == "nvidia":
        return "devstral-2-123b"
    return settings.default_llm_model


def _is_provider_configured(
    provider: str,
    settings: Any,
    llm: Any,
    key_override: str | None,
) -> bool:
    """Check whether a provider is usable for this request."""
    if provider == "gemini":
        return bool(key_override) or bool(settings.gemini_api_key)
    if provider == "groq":
        return bool(key_override) or bool(settings.groq_api_key)
    if provider == "nvidia":
        if key_override:
            from src.models.nvidia import is_nvidia_sdk_available

            return is_nvidia_sdk_available()
        return llm._get_nvidia().is_available
    return False


async def _generate_with_failover(
    *,
    llm: Any,
    user_prompt: str,
    system_prompt: str,
    requested_provider: str,
    requested_model: str | None,
    settings: Any,
    custom_provider_keys: dict[str, str],
) -> tuple[str, str, str, list[dict[str, str]]]:
    """Generate response with provider failover."""
    attempts: list[dict[str, str]] = []

    for candidate in _provider_candidate_order(requested_provider):
        key_override = custom_provider_keys.get(candidate)
        if not _is_provider_configured(candidate, settings, llm, key_override):
            attempts.append({"provider": candidate, "error": "not configured"})
            continue

        model_for_call = (
            requested_model
            if candidate == requested_provider.lower() and requested_model
            else _default_model_for_provider(candidate, settings)
        )

        try:
            if candidate == "gemini":
                response_text = await llm._get_gemini().generate(
                    prompt=user_prompt,
                    system_instruction=system_prompt,
                    model=model_for_call,
                    api_key=key_override,
                )
            elif candidate == "groq":
                response_text = await llm._get_groq().generate(
                    prompt=user_prompt,
                    system_instruction=system_prompt,
                    model=model_for_call,
                    api_key=key_override,
                )
            elif candidate == "nvidia":
                response_text = await llm._get_nvidia().generate(
                    prompt=user_prompt,
                    system_instruction=system_prompt,
                    model=model_for_call,
                    api_key=key_override,
                )
            else:
                attempts.append({"provider": candidate, "error": "unsupported provider"})
                continue

            return response_text, candidate, model_for_call, attempts
        except Exception as provider_error:
            error_text = str(provider_error)
            logger.warning(
                "chat_provider_attempt_failed",
                provider=candidate,
                model=model_for_call,
                error=error_text[:200],
            )
            attempts.append({"provider": candidate, "error": error_text[:200]})

    attempted = ", ".join(
        f"{attempt['provider']}: {attempt['error']}" for attempt in attempts
    )
    raise RuntimeError(f"No available LLM provider could generate a response ({attempted})")


class ChatMessage(BaseModel):
    """Chat message request."""
    content: str = Field(min_length=1, max_length=10000)
    conversation_id: UUID | None = None
    workspace_id: UUID | None = None
    layer: str = Field(default="personal", pattern="^(personal|workspace|global)$")
    include_global: bool = False
    agents_enabled: bool | None = None
    provider: str | None = Field(default=None, description="LLM provider: gemini, nvidia, groq")
    model: str | None = Field(default=None, description="Model ID to use")
    reasoning_model: str | None = Field(default=None, description="Reasoning model to use (qwen3-32b, deepseek-r1, etc)")
    reasoning_enabled: bool | None = Field(default=None, description="Whether to use reasoning agent step")


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
    user_pref_settings: dict = {}
    custom_provider_keys: dict[str, str] = {}
    preferred_provider: str | None = None
    preferred_model: str | None = None
    preferred_agents_enabled: bool | None = None

    async with postgres.connection() as conn:
        await conn.execute(
            """
            INSERT INTO chat.user_preferences (user_id)
            VALUES ($1)
            ON CONFLICT (user_id) DO NOTHING
            """,
            user_id,
        )
        pref_row = await conn.fetchrow(
            """
            SELECT default_provider, default_model, agents_enabled, settings
            FROM chat.user_preferences
            WHERE user_id = $1
            """,
            user_id,
        )
    if pref_row:
        preferred_provider = pref_row["default_provider"]
        preferred_model = pref_row["default_model"]
        preferred_agents_enabled = pref_row["agents_enabled"]
        if isinstance(pref_row["settings"], dict):
            user_pref_settings = pref_row["settings"]
            custom_keys_raw = user_pref_settings.get("custom_provider_keys")
            if isinstance(custom_keys_raw, dict):
                custom_provider_keys = {
                    str(k): str(v)
                    for k, v in custom_keys_raw.items()
                    if isinstance(v, str) and v
                }

    provider = message.provider or preferred_provider or settings.default_llm_provider
    model = message.model or preferred_model or settings.default_llm_model
    effective_agents_enabled = (
        message.agents_enabled
        if message.agents_enabled is not None
        else (preferred_agents_enabled if preferred_agents_enabled is not None else True)
    )
    memory_agent_enabled = bool(user_pref_settings.get("agent_memory_enabled", True))
    
    logger.info(
        "chat_message_received",
        user_id=str(user_id),
        layer=message.layer,
        content_length=len(message.content),
        provider=provider,
        model=model,
        agents_enabled=effective_agents_enabled,
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
        async with postgres.connection() as conn:
            workspace_ids = await conn.fetch(
                """
                SELECT workspace_id FROM (
                    SELECT wm.workspace_id AS workspace_id
                    FROM chat.workspace_members wm
                    JOIN chat.workspaces w ON w.id = wm.workspace_id
                    WHERE wm.user_id = $1
                      AND w.status = 'active'
                    UNION
                    SELECT tm.tenant_id AS workspace_id
                    FROM auth.tenant_members tm
                    WHERE tm.user_id = $1
                ) ws
                """,
                user_id,
            )
            accessible_workspace_ids = [row["workspace_id"] for row in workspace_ids]

        if message.layer == "workspace":
            if not message.workspace_id:
                raise HTTPException(status_code=400, detail="workspace_id required for workspace layer")
            if message.workspace_id not in accessible_workspace_ids:
                raise HTTPException(status_code=403, detail="No access to workspace")

        # Step 1: Search memory for relevant context (if agents enabled)
        memory_results = []
        if effective_agents_enabled and memory_agent_enabled:
            step_start = time.time()
            await save_processing_step(conversation_id, None, ProcessingStep(
                step=2, action="memory_search", status="running"
            ))
            
            hybrid_search = HybridSearch()
            layers = [message.layer if message.layer != "workspace" else "tenant"]
            if message.include_global:
                layers.append("global")

            tenant_scope_ids = [message.workspace_id] if message.workspace_id else accessible_workspace_ids

            memory_results = await hybrid_search.search(
                query=message.content,
                user_id=user_id,
                tenant_id=message.workspace_id,
                tenant_ids=tenant_scope_ids,
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
        else:
            reasoning_path.append({
                "step": 2,
                "action": "memory_search",
                "status": "skipped",
                "result": "Memory search disabled by settings",
                "reasoning": "Agents or memory agent toggle is disabled",
                "duration_ms": 0,
            })
        
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
            user_prompt = (
                "Context:\n"
                f"{context}\n\n"
                "---\n\n"
                f"User question: {message.content}\n\n"
                "Answer with reasoning. Cite which memory nodes led to your conclusion."
            )
            system_prompt = (
                "You are NeuroGraph, an AI with structured memory. "
                "Use provided context to answer. If confidence is low, say so explicitly."
            )
            confidence = min(0.95, max(r.confidence for r in memory_results)) if memory_results else 0.7
        else:
            user_prompt = f"Please help with this question: {message.content}"
            system_prompt = (
                "You are NeuroGraph, a helpful AI assistant with access to a knowledge graph. "
                "Answer concisely and helpfully."
            )
            confidence = 0.5

        requested_provider = provider.lower()
        response_text, used_provider, used_model, provider_attempts = await _generate_with_failover(
            llm=llm,
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            requested_provider=requested_provider,
            requested_model=model,
            settings=settings,
            custom_provider_keys=custom_provider_keys,
        )
        failover_note = ""
        if used_provider != requested_provider:
            failover_note = f" (fallback from {requested_provider}/{model} to {used_provider}/{used_model})"
            logger.info(
                "chat_provider_failover_used",
                requested_provider=requested_provider,
                requested_model=model,
                used_provider=used_provider,
                used_model=used_model,
                attempts=provider_attempts,
            )
        
        step_duration = int((time.time() - step_start) * 1000)
        reasoning_path.append({
            "step": 4,
            "action": "generate_response",
            "status": "completed",
            "result": f"Generated using {used_provider}/{used_model}{failover_note}",
            "reasoning": f"{'Used memory context' if context else 'No memory context available'}",
            "duration_ms": step_duration,
        })
        
        await save_processing_step(conversation_id, None, ProcessingStep(
            step=4, action="generating_response", status="completed",
            result=f"Generated with {used_provider}/{used_model}", duration_ms=step_duration
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
                used_provider,
                used_model,
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
            model_used=used_model,
            provider_used=used_provider,
        )
        
    except HTTPException:
        raise
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
        step_rows = await conn.fetch(
            """
            SELECT message_id, step_number, action, status, result, reasoning, duration_ms
            FROM chat.processing_steps
            WHERE conversation_id = $1 AND message_id IS NOT NULL
            ORDER BY created_at ASC, step_number ASC
            """,
            conversation_id,
        )

    steps_by_message: dict[str, list[dict]] = {}
    for row in step_rows:
        message_id = str(row["message_id"])
        if message_id not in steps_by_message:
            steps_by_message[message_id] = []
        steps_by_message[message_id].append(
            {
                "step_number": row["step_number"],
                "action": row["action"] or "",
                "status": row["status"] or "completed",
                "description": "",
                "reasoning": row["reasoning"] or "",
                "result": row["result"],
                "duration_ms": row["duration_ms"] or 0,
                "details": [],
            }
        )

    normalized_messages = []
    for m in messages:
        message_id = str(m["id"])
        processing_steps = _parse_json_list(m["reasoning_path"])
        if not processing_steps and message_id in steps_by_message:
            processing_steps = steps_by_message[message_id]
        sources = _parse_json_list(m["sources"])
        normalized_messages.append(
            {
                "id": message_id,
                "role": m["role"],
                "content": m["content"],
                "provider": m["provider"],
                "model": m["model"],
                "confidence": m["confidence"],
                "reasoning_path": processing_steps,
                "processing_steps": processing_steps,  # Alias for frontend compatibility
                "sources": sources,
                "created_at": m["created_at"].isoformat(),
            }
        )

    return {
        "id": str(conv["id"]),
        "title": conv["title"],
        "message_count": conv["message_count"],
        "created_at": conv["created_at"].isoformat(),
        "messages": normalized_messages,
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


# =============================================================================
# SSE Streaming Chat Endpoint - Real-time Pipeline Execution
# =============================================================================

from fastapi import Request
from fastapi.responses import StreamingResponse
import asyncio


class StreamingStepResult:
    """Result from a pipeline step for streaming."""
    def __init__(
        self,
        step: int,
        action: str,
        status: str,
        description: str = "",
        reasoning: str = "",
        result: str | None = None,
        duration_ms: int = 0,
        details: list[dict] | None = None,
        reasoning_output: str | None = None,  # Full reasoning trace from reasoning model
    ):
        self.step = step
        self.action = action
        self.status = status
        self.description = description
        self.reasoning = reasoning
        self.result = result
        self.duration_ms = duration_ms
        self.details = details or []
        self.reasoning_output = reasoning_output

    def to_dict(self) -> dict:
        return {
            "step_number": self.step,
            "action": self.action,
            "status": self.status,
            "description": self.description,
            "reasoning": self.reasoning,
            "result": self.result,
            "duration_ms": self.duration_ms,
            "details": self.details,
            "reasoning_output": self.reasoning_output,
        }


@router.post("/stream")
async def stream_chat(
    message: ChatMessage,
    request: Request,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
):
    """
    Streaming chat endpoint using Server-Sent Events (SSE).
    
    Returns real-time updates as the pipeline executes:
    - Step 1: Vector search (RAG)
    - Step 2: Graph traversal (Neo4j)
    - Step 3: Web search (if needed)
    - Step 4: Response generation (LLM)
    
    Each step emits:
    - action: What is being done
    - status: running/completed/skipped
    - details: Real data (actual nodes, connections, etc.)
    - reasoning: Why this step was taken
    """
    from src.rag.hybrid_search import HybridSearch
    from src.rag.context_assembly import ContextAssembler
    from src.models.unified_llm import get_unified_llm
    from src.core.config import get_settings
    from src.db.neo4j import get_neo4j_driver
    
    settings = get_settings()
    postgres = get_postgres_driver()

    async def event_generator():
        nonlocal user_id
        step_results: list[dict] = []
        
        try:
            # Load user preferences
            user_pref_settings: dict = {}
            custom_provider_keys: dict[str, str] = {}
            preferred_provider: str | None = None
            preferred_model: str | None = None
            preferred_agents_enabled: bool | None = None

            async with postgres.connection() as conn:
                await conn.execute(
                    """INSERT INTO chat.user_preferences (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING""",
                    user_id,
                )
                pref_row = await conn.fetchrow(
                    """SELECT default_provider, default_model, agents_enabled, settings FROM chat.user_preferences WHERE user_id = $1""",
                    user_id,
                )
            if pref_row:
                preferred_provider = pref_row["default_provider"]
                preferred_model = pref_row["default_model"]
                preferred_agents_enabled = pref_row["agents_enabled"]
                if isinstance(pref_row["settings"], dict):
                    user_pref_settings = pref_row["settings"]
                    custom_keys_raw = user_pref_settings.get("custom_provider_keys")
                    if isinstance(custom_keys_raw, dict):
                        custom_provider_keys = {
                            str(k): str(v) for k, v in custom_keys_raw.items() if isinstance(v, str) and v
                        }

            provider = message.provider or preferred_provider or settings.default_llm_provider
            model = message.model or preferred_model or settings.default_llm_model
            effective_agents_enabled = (
                message.agents_enabled
                if message.agents_enabled is not None
                else (preferred_agents_enabled if preferred_agents_enabled is not None else True)
            )
            memory_agent_enabled = bool(user_pref_settings.get("agent_memory_enabled", True))
            # Use request reasoning_enabled if provided, else fall back to user preference
            show_reasoning = (
                message.reasoning_enabled 
                if message.reasoning_enabled is not None 
                else bool(user_pref_settings.get("show_reasoning", True))
            )
            # Use request reasoning_model if provided, else fall back to user preference or default
            reasoning_model = message.reasoning_model or str(user_pref_settings.get("reasoning_model", "qwen3-32b"))

            # Create/get conversation
            conversation_id = message.conversation_id
            if not conversation_id:
                conversation_id = uuid4()
                async with postgres.connection() as conn:
                    await conn.execute(
                        """INSERT INTO chat.conversations (id, workspace_id, user_id, title) VALUES ($1, $2, $3, $4)""",
                        conversation_id, message.workspace_id, user_id,
                        message.content[:50] + ("..." if len(message.content) > 50 else ""),
                    )

            # Save user message
            user_message_id = uuid4()
            async with postgres.connection() as conn:
                await conn.execute(
                    """INSERT INTO chat.messages (id, conversation_id, role, content) VALUES ($1, $2, 'user', $3)""",
                    user_message_id, conversation_id, message.content,
                )

            # Emit conversation init
            yield f"data: {json.dumps({'type': 'init', 'conversation_id': str(conversation_id)})}\n\n"

            # Get accessible workspaces
            async with postgres.connection() as conn:
                workspace_ids = await conn.fetch(
                    """
                    SELECT workspace_id FROM (
                        SELECT wm.workspace_id FROM chat.workspace_members wm
                        JOIN chat.workspaces w ON w.id = wm.workspace_id
                        WHERE wm.user_id = $1 AND w.status = 'active'
                        UNION
                        SELECT tm.tenant_id FROM auth.tenant_members tm WHERE tm.user_id = $1
                    ) ws
                    """,
                    user_id,
                )
                accessible_workspace_ids = [row["workspace_id"] for row in workspace_ids]

            # =========================================================================
            # STEP 1: Vector Search (RAG)
            # =========================================================================
            memory_results = []
            graph_paths = []
            
            if effective_agents_enabled and memory_agent_enabled:
                step_start = time.time()
                
                # Emit running status
                step1 = StreamingStepResult(
                    step=1,
                    action="Fetching relevant info from RAG",
                    status="running",
                    description="Searching vector database for semantically similar memories",
                    reasoning="Converting query to embeddings and performing similarity search",
                    details=[
                        {"type": "info", "content": "Embedding query using gemini-embedding-exp-03-07 (768 dim)"}
                    ]
                )
                yield f"data: {json.dumps({'type': 'step', 'data': step1.to_dict()})}\n\n"
                
                hybrid_search = HybridSearch()
                layers = [message.layer if message.layer != "workspace" else "tenant"]
                if message.include_global:
                    layers.append("global")

                tenant_scope_ids = [message.workspace_id] if message.workspace_id else accessible_workspace_ids

                # Perform actual vector search
                memory_results = await hybrid_search.search(
                    query=message.content,
                    user_id=user_id,
                    tenant_id=message.workspace_id,
                    tenant_ids=tenant_scope_ids,
                    layers=layers,
                    limit=10,
                    min_confidence=0.3,
                )

                step_duration = int((time.time() - step_start) * 1000)
                
                # Build real details from results
                details = [
                    {"type": "info", "content": f"Embedding query using gemini-embedding-exp-03-07 (768 dim)"},
                    {"type": "search", "content": f"Searching {', '.join(layers)} memory layers..."},
                    {"type": "result", "content": f"Found {len(memory_results)} relevant memories (similarity > 0.30)"},
                ]
                
                # Add actual memory nodes found
                for i, mem in enumerate(memory_results[:5]):
                    content_preview = (mem.content[:60] + "...") if len(mem.content) > 60 else mem.content
                    score = getattr(mem, 'final_score', getattr(mem, 'similarity', 0.0))
                    if isinstance(score, (int, float)):
                        details.append({
                            "type": "node",
                            "content": f"[{score:.2f}] {content_preview}",
                            "metadata": {"id": str(mem.node_id), "layer": mem.layer}
                        })

                step1_complete = StreamingStepResult(
                    step=1,
                    action="Fetching relevant info from RAG",
                    status="completed",
                    description="Vector similarity search complete",
                    reasoning=f"Searched {', '.join(layers)} layers with confidence threshold 0.3",
                    result=f"Found {len(memory_results)} relevant memories",
                    duration_ms=step_duration,
                    details=details
                )
                step_results.append(step1_complete.to_dict())
                yield f"data: {json.dumps({'type': 'step', 'data': step1_complete.to_dict()})}\n\n"

                # =========================================================================
                # STEP 2: Connected Memories (Canvas Edges)
                # =========================================================================
                connected_memories: list[dict] = []
                connected_memory_contents: list[str] = []
                
                if memory_results:
                    step_start = time.time()
                    
                    step2 = StreamingStepResult(
                        step=2,
                        action="Checking connected memories",
                        status="running",
                        description="Finding user-defined memory connections",
                        reasoning="Analyzing canvas edges with embedded reasons",
                        details=[{"type": "info", "content": "Querying memory.canvas_edges for connections"}]
                    )
                    yield f"data: {json.dumps({'type': 'step', 'data': step2.to_dict()})}\n\n"
                    
                    connection_details: list[dict] = []
                    
                    try:
                        # Get memory IDs from results
                        memory_ids = [m.node_id for m in memory_results[:10]]
                        
                        async with postgres.connection() as conn:
                            # Query canvas_edges for connections between found memories
                            # and also connections FROM found memories to other memories
                            edges_query = """
                            WITH source_memories AS (
                                SELECT UNNEST($1::uuid[]) AS mem_id
                            )
                            SELECT 
                                ce.id AS edge_id,
                                ce.source_memory_id,
                                ce.target_memory_id,
                                ce.reason,
                                ce.confidence AS edge_confidence,
                                ce.weight,
                                ce.connection_count,
                                source_mem.content AS source_content,
                                source_mem.embedding AS source_embedding,
                                target_mem.content AS target_content,
                                target_mem.embedding AS target_embedding,
                                target_mem.layer AS target_layer
                            FROM memory.canvas_edges ce
                            JOIN memory.embeddings source_mem ON ce.source_memory_id = source_mem.id
                            JOIN memory.embeddings target_mem ON ce.target_memory_id = target_mem.id
                            WHERE ce.source_memory_id = ANY($1::uuid[])
                               OR ce.target_memory_id = ANY($1::uuid[])
                            ORDER BY ce.weight DESC, ce.connection_count DESC
                            LIMIT 15
                            """
                            
                            edge_records = await conn.fetch(edges_query, memory_ids)
                            
                            connection_details.append({
                                "type": "info", 
                                "content": f"Found {len(edge_records)} memory connections"
                            })
                            
                            # Process each edge and compute enhanced confidence
                            from src.rag.similarity import cosine_similarity
                            import numpy as np
                            
                            for edge in edge_records:
                                source_content = edge["source_content"][:60]
                                target_content = edge["target_content"][:60]
                                reason = edge["reason"] or ""
                                edge_conf = edge["edge_confidence"] or 0.8
                                weight = edge["weight"] or 1.0
                                conn_count = edge["connection_count"] or 1
                                
                                # Compute embedding similarity between source and target
                                embedding_sim = 0.5  # Default
                                try:
                                    source_emb = edge["source_embedding"]
                                    target_emb = edge["target_embedding"]
                                    if source_emb and target_emb:
                                        source_arr = np.array(source_emb)
                                        target_arr = np.array(target_emb)
                                        embedding_sim = float(cosine_similarity(source_arr, target_arr))
                                        embedding_sim = max(0.0, min(1.0, (embedding_sim + 1) / 2))  # Normalize -1,1 to 0,1
                                except Exception:
                                    pass
                                
                                # Compute combined confidence:
                                # - embedding_similarity: 0-1 (how similar the memories are)
                                # - edge_confidence: 0-1 (user-provided confidence)
                                # - weight: 1-2 (boosted by re-connections)
                                # - connection_count: 1+ (how many times connected)
                                # Formula: avg(emb_sim, edge_conf) * min(weight, 1.5) * (1 + log(conn_count)/10)
                                import math
                                base_conf = (embedding_sim * 0.4 + edge_conf * 0.6)  # Weighted avg
                                weight_boost = min(weight, 1.5) / 1.0  # Normalize weight boost
                                count_boost = 1.0 + (math.log(conn_count + 1) / 10.0)  # Log boost for count
                                combined_confidence = min(1.0, base_conf * weight_boost * count_boost)
                                
                                connection_str = f"{source_content}... → {target_content}..."
                                if reason:
                                    connection_str += f" (reason: {reason[:30]})"
                                
                                connection_details.append({
                                    "type": "connection",
                                    "content": connection_str,
                                    "metadata": {
                                        "edge_id": str(edge["edge_id"]),
                                        "confidence": round(combined_confidence, 2),
                                        "embedding_similarity": round(embedding_sim, 2),
                                        "weight": weight,
                                    }
                                })
                                
                                # Track connected memory for context
                                # Find the "other" memory (not in our original results)
                                target_id = edge["target_memory_id"]
                                source_id = edge["source_memory_id"]
                                other_id = target_id if source_id in memory_ids else source_id
                                other_content = edge["target_content"] if source_id in memory_ids else edge["source_content"]
                                
                                connected_memories.append({
                                    "memory_id": str(other_id),
                                    "content": other_content,
                                    "reason": reason,
                                    "confidence": combined_confidence,
                                    "layer": edge["target_layer"],
                                    "connection_type": "canvas_edge",
                                })
                                connected_memory_contents.append(other_content)
                            
                            # Add summary node
                            if connected_memories:
                                avg_conf = sum(m["confidence"] for m in connected_memories) / len(connected_memories)
                                connection_details.append({
                                    "type": "result",
                                    "content": f"Connected {len(connected_memories)} memories (avg confidence: {avg_conf:.0%})"
                                })
                            else:
                                connection_details.append({
                                    "type": "info",
                                    "content": "No user-defined memory connections found"
                                })
                        
                    except Exception as conn_err:
                        logger.warning("connected_memories_error", error=str(conn_err))
                        connection_details.append({
                            "type": "error",
                            "content": f"Connection lookup failed: {str(conn_err)[:50]}"
                        })
                    
                    step_duration = int((time.time() - step_start) * 1000)
                    
                    step2_status = "completed" if connected_memories else "completed"
                    step2_complete = StreamingStepResult(
                        step=2,
                        action="Checking connected memories",
                        status=step2_status,
                        description="Memory connection analysis complete",
                        reasoning=f"Analyzed canvas edges with confidence scoring",
                        result=f"Found {len(connected_memories)} connected memories",
                        duration_ms=step_duration,
                        details=connection_details
                    )
                    step_results.append(step2_complete.to_dict())
                    yield f"data: {json.dumps({'type': 'step', 'data': step2_complete.to_dict()})}\n\n"
                    
                else:
                    # No memory results, skip connected memories
                    step2_skip = StreamingStepResult(
                        step=2,
                        action="Checking connected memories",
                        status="skipped",
                        description="Skipped - no memories to check connections for",
                        reasoning="Connected memories requires base memories from RAG",
                        details=[{"type": "info", "content": "No memories to analyze connections"}]
                    )
                    step_results.append(step2_skip.to_dict())
                    yield f"data: {json.dumps({'type': 'step', 'data': step2_skip.to_dict()})}\n\n"

                # =========================================================================
                # STEP 3: Graph Traversal (Neo4j)
                # =========================================================================
                if memory_results:
                    step_start = time.time()
                    
                    step3 = StreamingStepResult(
                        step=3,
                        action="Accessing graph memory",
                        status="running",
                        description="Traversing knowledge graph for connected concepts",
                        reasoning="Following relationships between memory nodes",
                        details=[{"type": "info", "content": "Querying Neo4j graph database"}]
                    )
                    yield f"data: {json.dumps({'type': 'step', 'data': step3.to_dict()})}\n\n"
                    
                    # Get seed nodes for graph traversal
                    seed_nodes = [str(m.node_id) for m in memory_results[:5]]
                    
                    # Query Neo4j for graph connections
                    neo4j = get_neo4j_driver()
                    graph_details: list[dict] = []
                    
                    try:
                        async with neo4j.session() as session:
                            # Find connected nodes with relationships
                            cypher_query = """
                            MATCH (start:Entity)-[r]-(connected:Entity)
                            WHERE start.id IN $seed_ids
                            RETURN start.id AS source_id, start.name AS source_name,
                                   type(r) AS relationship, r.reason AS reason,
                                   connected.id AS target_id, connected.name AS target_name,
                                   r.confidence AS confidence
                            LIMIT 20
                            """
                            result = await session.run(cypher_query, seed_ids=seed_nodes)
                            records = await result.data()
                            
                            graph_details.append({"type": "info", "content": f"Querying Neo4j with {len(seed_nodes)} seed nodes"})
                            
                            # Build connection details
                            connections_found = 0
                            for record in records:
                                source = record.get("source_name", record.get("source_id", "?"))
                                target = record.get("target_name", record.get("target_id", "?"))
                                rel = record.get("relationship", "CONNECTED_TO")
                                reason = record.get("reason", "")
                                conf = record.get("confidence", 0.8)
                                
                                connection_str = f"{source} → {rel} → {target}"
                                if reason:
                                    connection_str += f" ({reason})"
                                
                                graph_details.append({
                                    "type": "connection",
                                    "content": connection_str,
                                    "metadata": {"confidence": conf}
                                })
                                connections_found += 1
                                graph_paths.append({
                                    "source": source,
                                    "relationship": rel,
                                    "target": target,
                                    "reason": reason
                                })
                            
                            # Get centrality for top nodes
                            centrality_query = """
                            MATCH (e:Entity)-[r]-(n)
                            WHERE e.id IN $seed_ids
                            RETURN e.name AS node, e.id AS node_id, count(r) AS edge_count
                            ORDER BY edge_count DESC
                            LIMIT 5
                            """
                            centrality_result = await session.run(centrality_query, seed_ids=seed_nodes)
                            centrality_records = await centrality_result.data()
                            
                            for cr in centrality_records:
                                graph_details.append({
                                    "type": "node",
                                    "content": f"Node: {cr.get('node', '?')} (edges: {cr.get('edge_count', 0)})",
                                    "metadata": {"centrality": cr.get("edge_count", 0)}
                                })
                            
                            graph_details.append({
                                "type": "result",
                                "content": f"Retrieved {connections_found} graph connections"
                            })

                    except Exception as graph_err:
                        logger.warning("graph_traversal_warning", error=str(graph_err))
                        graph_details.append({
                            "type": "info",
                            "content": "Graph traversal skipped - no graph data available"
                        })

                    step_duration = int((time.time() - step_start) * 1000)
                    
                    step3_complete = StreamingStepResult(
                        step=3,
                        action="Accessing graph memory",
                        status="completed",
                        description="Graph traversal complete",
                        reasoning="Expanded context via relationship paths",
                        result=f"Found {len(graph_paths)} graph connections",
                        duration_ms=step_duration,
                        details=graph_details
                    )
                    step_results.append(step3_complete.to_dict())
                    yield f"data: {json.dumps({'type': 'step', 'data': step3_complete.to_dict()})}\n\n"
                else:
                    # No memory results, skip graph
                    step3_skip = StreamingStepResult(
                        step=3,
                        action="Accessing graph memory",
                        status="skipped",
                        description="Skipped - no seed nodes from vector search",
                        reasoning="Graph traversal requires seed nodes from memory search",
                        details=[{"type": "info", "content": "No memories found to expand via graph"}]
                    )
                    step_results.append(step3_skip.to_dict())
                    yield f"data: {json.dumps({'type': 'step', 'data': step3_skip.to_dict()})}\n\n"

            else:
                # Agents disabled
                step1_skip = StreamingStepResult(
                    step=1,
                    action="Fetching relevant info from RAG",
                    status="skipped",
                    description="Memory search disabled by settings",
                    reasoning="Agents or memory agent toggle is disabled in preferences",
                    details=[{"type": "info", "content": "Memory search is disabled"}]
                )
                step_results.append(step1_skip.to_dict())
                yield f"data: {json.dumps({'type': 'step', 'data': step1_skip.to_dict()})}\n\n"

                step2_skip = StreamingStepResult(
                    step=2,
                    action="Checking connected memories",
                    status="skipped",
                    description="Connected memories check disabled by settings",
                    reasoning="Agents disabled - no connection check performed",
                    details=[]
                )
                step_results.append(step2_skip.to_dict())
                yield f"data: {json.dumps({'type': 'step', 'data': step2_skip.to_dict()})}\n\n"

                step3_skip = StreamingStepResult(
                    step=3,
                    action="Accessing graph memory",
                    status="skipped",
                    description="Graph search disabled by settings",
                    reasoning="Agents disabled - no graph traversal performed",
                    details=[]
                )
                step_results.append(step3_skip.to_dict())
                yield f"data: {json.dumps({'type': 'step', 'data': step3_skip.to_dict()})}\n\n"

            # =========================================================================
            # STEP 4: Web Search (conditional)
            # =========================================================================
            step_start = time.time()
            web_search_details: list[dict] = []
            
            # Determine if we should search the web
            # (low confidence or no memory results)
            avg_confidence = 0.0
            if memory_results:
                confidences = [getattr(m, 'confidence', 0.7) for m in memory_results[:5]]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            should_search_web = len(memory_results) < 2 or avg_confidence < 0.5
            
            step4 = StreamingStepResult(
                step=4,
                action="Surfing web",
                status="running" if should_search_web else "skipped",
                description="Searching for additional context online" if should_search_web else "Sufficient context from memory",
                reasoning=f"{'Insufficient memory context, fetching external data' if should_search_web else f'Memory confidence {avg_confidence:.0%} is sufficient'}",
                details=[{"type": "info", "content": "Evaluating need for web search..."}]
            )
            yield f"data: {json.dumps({'type': 'step', 'data': step4.to_dict()})}\n\n"
            
            if should_search_web:
                # In production, this would call Tavily/SerpAPI
                # For now, indicate that web search would be performed
                web_search_details = [
                    {"type": "info", "content": "Search engine: DuckDuckGo"},
                    {"type": "search", "content": f'Query: "{message.content[:50]}..."'},
                    {"type": "info", "content": "Web search integration not configured"},
                ]
                step_duration = int((time.time() - step_start) * 1000)
                
                step4_complete = StreamingStepResult(
                    step=4,
                    action="Surfing web",
                    status="skipped",
                    description="Web search not configured",
                    reasoning="External search API not available - using memory only",
                    result="Proceeding with memory context",
                    duration_ms=step_duration,
                    details=web_search_details
                )
            else:
                step_duration = int((time.time() - step_start) * 1000)
                step4_complete = StreamingStepResult(
                    step=4,
                    action="Surfing web",
                    status="skipped",
                    description="Sufficient context from memory",
                    reasoning=f"Memory confidence ({avg_confidence:.0%}) exceeds threshold - no web search needed",
                    result="Using memory context only",
                    duration_ms=step_duration,
                    details=[
                        {"type": "info", "content": f"Average memory confidence: {avg_confidence:.0%}"},
                        {"type": "result", "content": "Skipping web search - sufficient context from memory"}
                    ]
                )
            
            step_results.append(step4_complete.to_dict())
            yield f"data: {json.dumps({'type': 'step', 'data': step4_complete.to_dict()})}\n\n"

            # =========================================================================
            # STEP 5: Reasoning Agent (if enabled)
            # =========================================================================
            reasoning_result = None
            synthesized_context = ""
            reasoning_trace = ""
            
            # Include connected memory contents in reasoning
            all_memory_contents = []
            for m in memory_results[:10]:
                all_memory_contents.append(m.content)
            all_memory_contents.extend(connected_memory_contents[:5])  # Add connected memories
            
            if show_reasoning and memory_results:
                from src.models.nvidia import get_nvidia_client
                
                step_start = time.time()
                
                step5_reasoning = StreamingStepResult(
                    step=5,
                    action="Reasoning over context",
                    status="running",
                    description="Analyzing memory nodes and graph paths",
                    reasoning="Using reasoning agent to synthesize context with explicit reasoning traces",
                    details=[
                        {"type": "info", "content": "Model: Nemotron Reasoning Agent"},
                        {"type": "info", "content": f"Processing {len(memory_results)} memory nodes + {len(connected_memories)} connected"},
                        {"type": "info", "content": f"Processing {len(graph_paths)} graph paths"},
                    ]
                )
                yield f"data: {json.dumps({'type': 'step', 'data': step5_reasoning.to_dict()})}\n\n"
                
                try:
                    nvidia_client = get_nvidia_client()
                    
                    # Convert memory results to dict format for reasoning agent
                    # Include both direct memories and connected memories
                    memory_nodes_dict = [
                        {
                            "content": m.content,
                            "score": getattr(m, 'final_score', getattr(m, 'similarity', 0.7)),
                            "layer": m.layer,
                            "node_id": str(m.node_id),
                        }
                        for m in memory_results[:10]
                    ]
                    
                    # Add connected memories with their confidence
                    for cm in connected_memories[:5]:
                        memory_nodes_dict.append({
                            "content": cm["content"],
                            "score": cm["confidence"],
                            "layer": cm["layer"],
                            "node_id": cm["memory_id"],
                            "connection_reason": cm.get("reason", ""),
                        })
                    
                    reasoning_result = await nvidia_client.reason_over_nodes(
                        query=message.content,
                        memory_nodes=memory_nodes_dict,
                        graph_paths=graph_paths,
                        api_key=custom_provider_keys.get("nvidia"),
                        enable_thinking=True,
                        reasoning_model=reasoning_model,
                    )
                    
                    synthesized_context = reasoning_result.get("synthesized_context", "")
                    reasoning_trace = reasoning_result.get("reasoning", "")
                    cited_nodes = reasoning_result.get("cited_nodes", [])
                    reasoning_confidence = reasoning_result.get("confidence", 0.7)
                    
                    step_duration = int((time.time() - step_start) * 1000)
                    
                    reasoning_details = [
                        {"type": "info", "content": f"Model: {reasoning_result.get('model_used', reasoning_model)}"},
                        {"type": "info", "content": f"Reasoning confidence: {reasoning_confidence:.0%}"},
                    ]
                    
                    # Add reasoning trace steps
                    if reasoning_trace:
                        for i, line in enumerate(reasoning_trace.split("\n")[:5]):
                            if line.strip():
                                reasoning_details.append({
                                    "type": "connection",
                                    "content": line.strip(),
                                })
                    
                    # Add cited nodes
                    for node in cited_nodes[:3]:
                        reasoning_details.append({
                            "type": "node",
                            "content": f"[{node.get('score', 0):.2f}] {node.get('content', '')[:60]}...",
                        })
                    
                    reasoning_details.append({
                        "type": "result",
                        "content": f"Synthesized context: {len(synthesized_context)} chars"
                    })
                    
                    step5_complete = StreamingStepResult(
                        step=5,
                        action="Reasoning over context",
                        status="completed",
                        description="Context reasoning complete",
                        reasoning=f"Traced {len(graph_paths)} paths, cited {len(cited_nodes)} nodes",
                        result=f"Reasoning confidence: {reasoning_confidence:.0%}",
                        duration_ms=step_duration,
                        details=reasoning_details,
                        reasoning_output=reasoning_trace or synthesized_context,  # Persist model output for refresh display
                    )
                    # Also persist model output in details so historical rows can display it
                    if step5_complete.reasoning_output:
                        step5_complete.details.append(
                            {
                                "type": "result",
                                "content": f"Reasoning output: {step5_complete.reasoning_output[:200]}",
                            }
                        )
                    step_results.append(step5_complete.to_dict())
                    yield f"data: {json.dumps({'type': 'step', 'data': step5_complete.to_dict()})}\n\n"
                    
                except Exception as reasoning_err:
                    logger.warning("reasoning_agent_error", error=str(reasoning_err))
                    step_duration = int((time.time() - step_start) * 1000)
                    
                    step5_failed = StreamingStepResult(
                        step=5,
                        action="Reasoning over context",
                        status="skipped",
                        description="Reasoning agent unavailable",
                        reasoning=f"Falling back to direct context: {str(reasoning_err)[:50]}",
                        duration_ms=step_duration,
                        details=[{"type": "info", "content": "Using direct memory context"}]
                    )
                    step_results.append(step5_failed.to_dict())
                    yield f"data: {json.dumps({'type': 'step', 'data': step5_failed.to_dict()})}\n\n"
            else:
                # Skip reasoning step
                step5_skip = StreamingStepResult(
                    step=5,
                    action="Reasoning over context",
                    status="skipped",
                    description="Reasoning disabled or no memory context",
                    reasoning="Using direct context assembly" if memory_results else "No memories to reason over",
                    details=[{"type": "info", "content": "Proceeding to response generation"}]
                )
                step_results.append(step5_skip.to_dict())
                yield f"data: {json.dumps({'type': 'step', 'data': step5_skip.to_dict()})}\n\n"

            # =========================================================================
            # STEP 6: Generate Response (LLM)
            # =========================================================================
            step_start = time.time()
            
            step6 = StreamingStepResult(
                step=6,
                action="Generating response",
                status="running",
                description="Synthesizing answer from all gathered context",
                reasoning="LLM processing with retrieved context and reasoning",
                details=[
                    {"type": "info", "content": f"Provider: {provider}"},
                    {"type": "info", "content": f"Model: {model}"},
                ]
            )
            yield f"data: {json.dumps({'type': 'step', 'data': step6.to_dict()})}\n\n"

            # Build context - use synthesized context if reasoning was performed
            context = ""
            reasoning_context = ""
            if synthesized_context:
                # Use the reasoning agent's synthesized context
                context = synthesized_context
                if reasoning_trace:
                    reasoning_context = f"\n\nReasoning Trace:\n{reasoning_trace}"
            elif memory_results or connected_memories:
                context_assembler = ContextAssembler()
                context = context_assembler.assemble(scored_nodes=memory_results)
                
                # Add connected memory context
                if connected_memories:
                    context += "\n\nConnected Memories:\n"
                    for cm in connected_memories[:5]:
                        context += f"- {cm['content'][:100]}"
                        if cm.get('reason'):
                            context += f" (connected because: {cm['reason']})"
                        context += f" [confidence: {cm['confidence']:.0%}]\n"
                
                # Build reasoning path string
                if graph_paths:
                    reasoning_context = "\n\nReasoning Path:\n"
                    for path in graph_paths[:5]:
                        path_str = f"  {path['source']} → {path['relationship']} → {path['target']}"
                        if path.get('reason'):
                            path_str += f" ({path['reason']})"
                        reasoning_context += path_str + "\n"

            # Prepare prompts
            if context:
                user_prompt = (
                    "Context:\n" + context + reasoning_context + 
                    "\n\n---\n\n"
                    f"User question: {message.content}\n\n"
                    "Answer with reasoning. Cite which memory nodes led to your conclusion using [score] format."
                )
                system_prompt = (
                    "You are NeuroGraph, an AI with structured memory. "
                    "Use provided context to answer. If confidence is low, say so explicitly. "
                    "When citing memories, use the [score] notation to show confidence."
                )
                confidence = min(0.95, max(getattr(m, 'confidence', 0.7) for m in memory_results)) if memory_results else 0.7
            else:
                user_prompt = f"Please help with this question: {message.content}"
                system_prompt = (
                    "You are NeuroGraph, a helpful AI assistant. "
                    "Answer concisely and helpfully."
                )
                confidence = 0.5

            # Call LLM
            llm = get_unified_llm()
            requested_provider = provider.lower()
            
            try:
                response_text, used_provider, used_model, provider_attempts = await _generate_with_failover(
                    llm=llm,
                    user_prompt=user_prompt,
                    system_prompt=system_prompt,
                    requested_provider=requested_provider,
                    requested_model=model,
                    settings=settings,
                    custom_provider_keys=custom_provider_keys,
                )
                failover_note = ""
                if used_provider != requested_provider:
                    failover_note = (
                        f"Fallback from {requested_provider}/{model} to {used_provider}/{used_model}"
                    )
                    logger.info(
                        "stream_chat_provider_failover_used",
                        requested_provider=requested_provider,
                        requested_model=model,
                        used_provider=used_provider,
                        used_model=used_model,
                        attempts=provider_attempts,
                    )
            except Exception as llm_err:
                logger.error("llm_generation_error", error=str(llm_err))
                response_text = f"I apologize, but I encountered an error generating a response: {str(llm_err)[:100]}"
                confidence = 0.1
                used_provider = requested_provider
                used_model = model
                failover_note = ""

            step_duration = int((time.time() - step_start) * 1000)
            
            step6_complete = StreamingStepResult(
                step=6,
                action="Generating response",
                status="completed",
                description="Response generated successfully",
                reasoning=f"{'Used memory context with ' + str(len(memory_results)) + ' nodes + ' + str(len(connected_memories)) + ' connected' if context else 'No memory context available'}",
                result=f"Generated using {used_provider}/{used_model}",
                duration_ms=step_duration,
                details=[
                    {"type": "info", "content": f"Provider: {used_provider}"},
                    {"type": "info", "content": f"Model: {used_model}"},
                    {"type": "info", "content": f"Context tokens: ~{len(context) // 4}"},
                    {"type": "result", "content": f"Response generated ({len(response_text)} chars)"}
                ]
            )
            if failover_note:
                step6_complete.details.append({"type": "info", "content": failover_note})
            step_results.append(step6_complete.to_dict())
            yield f"data: {json.dumps({'type': 'step', 'data': step6_complete.to_dict()})}\n\n"

            # Save assistant message
            assistant_message_id = uuid4()
            sources = [
                {
                    "node_id": str(r.node_id),
                    "content": r.content[:150] + "..." if len(r.content) > 150 else r.content,
                    "score": round(getattr(r, 'final_score', getattr(r, 'similarity', 0.0)), 3),
                    "layer": r.layer,
                }
                for r in memory_results[:5]
            ]
            
            async with postgres.connection() as conn:
                await conn.execute(
                    """
                    INSERT INTO chat.messages 
                    (id, conversation_id, role, content, provider, model, confidence, reasoning_path, sources)
                    VALUES ($1, $2, 'assistant', $3, $4, $5, $6, $7, $8)
                    """,
                    assistant_message_id, conversation_id, response_text,
                    used_provider, used_model, confidence,
                    json.dumps(step_results), json.dumps(sources),
                )

            # Emit final response
            final_response = {
                "type": "response",
                "data": {
                    "id": str(assistant_message_id),
                    "conversation_id": str(conversation_id),
                    "content": response_text,
                    "confidence": confidence,
                    "model_used": used_model,
                    "provider_used": used_provider,
                    "sources": sources,
                    "processing_steps": step_results,
                    "graph_paths": graph_paths[:5],
                }
            }
            yield f"data: {json.dumps(final_response)}\n\n"
            
            # End stream
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.error("stream_chat_error", error=str(e))
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
