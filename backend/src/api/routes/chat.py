"""Chat routes with orchestration."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID, uuid4
import time

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
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
    agents_enabled: bool | None = None
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
    custom_key_override = custom_provider_keys.get(provider.lower())
    
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

        provider_lower = provider.lower()
        if provider_lower == "gemini":
            response_text = await llm._get_gemini().generate(
                prompt=user_prompt,
                system_instruction=system_prompt,
                model=model,
                api_key=custom_key_override,
            )
        elif provider_lower == "groq":
            response_text = await llm._get_groq().generate(
                prompt=user_prompt,
                system_instruction=system_prompt,
                model=model,
                api_key=custom_key_override,
            )
        elif provider_lower == "nvidia":
            response_text = await llm._get_nvidia().generate(
                prompt=user_prompt,
                system_instruction=system_prompt,
                model=model,
                api_key=custom_key_override,
            )
        else:
            response_text = await llm.generate(
                prompt=user_prompt,
                system_instruction=system_prompt,
                provider=provider,
                model=model,
            )
        
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


# =============================================================================
# SSE Streaming Chat Endpoint - Real-time Pipeline Execution
# =============================================================================

from fastapi import Request
from fastapi.responses import StreamingResponse
import json
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
        details: list[dict] | None = None
    ):
        self.step = step
        self.action = action
        self.status = status
        self.description = description
        self.reasoning = reasoning
        self.result = result
        self.duration_ms = duration_ms
        self.details = details or []

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
            custom_key_override = custom_provider_keys.get(provider.lower())

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
                # STEP 2: Graph Traversal (Neo4j)
                # =========================================================================
                if memory_results:
                    step_start = time.time()
                    
                    step2 = StreamingStepResult(
                        step=2,
                        action="Accessing graph memory",
                        status="running",
                        description="Traversing knowledge graph for connected concepts",
                        reasoning="Following relationships between memory nodes",
                        details=[{"type": "info", "content": "Querying Neo4j graph database"}]
                    )
                    yield f"data: {json.dumps({'type': 'step', 'data': step2.to_dict()})}\n\n"
                    
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
                    
                    step2_complete = StreamingStepResult(
                        step=2,
                        action="Accessing graph memory",
                        status="completed",
                        description="Graph traversal complete",
                        reasoning="Expanded context via relationship paths",
                        result=f"Found {len(graph_paths)} graph connections",
                        duration_ms=step_duration,
                        details=graph_details
                    )
                    step_results.append(step2_complete.to_dict())
                    yield f"data: {json.dumps({'type': 'step', 'data': step2_complete.to_dict()})}\n\n"
                else:
                    # No memory results, skip graph
                    step2_skip = StreamingStepResult(
                        step=2,
                        action="Accessing graph memory",
                        status="skipped",
                        description="Skipped - no seed nodes from vector search",
                        reasoning="Graph traversal requires seed nodes from memory search",
                        details=[{"type": "info", "content": "No memories found to expand via graph"}]
                    )
                    step_results.append(step2_skip.to_dict())
                    yield f"data: {json.dumps({'type': 'step', 'data': step2_skip.to_dict()})}\n\n"

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
                    action="Accessing graph memory",
                    status="skipped",
                    description="Graph search disabled by settings",
                    reasoning="Agents disabled - no graph traversal performed",
                    details=[]
                )
                step_results.append(step2_skip.to_dict())
                yield f"data: {json.dumps({'type': 'step', 'data': step2_skip.to_dict()})}\n\n"

            # =========================================================================
            # STEP 3: Web Search (conditional)
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
            
            step3 = StreamingStepResult(
                step=3,
                action="Surfing web",
                status="running" if should_search_web else "skipped",
                description="Searching for additional context online" if should_search_web else "Sufficient context from memory",
                reasoning=f"{'Insufficient memory context, fetching external data' if should_search_web else f'Memory confidence {avg_confidence:.0%} is sufficient'}",
                details=[{"type": "info", "content": "Evaluating need for web search..."}]
            )
            yield f"data: {json.dumps({'type': 'step', 'data': step3.to_dict()})}\n\n"
            
            if should_search_web:
                # In production, this would call Tavily/SerpAPI
                # For now, indicate that web search would be performed
                web_search_details = [
                    {"type": "info", "content": "Search engine: DuckDuckGo"},
                    {"type": "search", "content": f'Query: "{message.content[:50]}..."'},
                    {"type": "info", "content": "Web search integration not configured"},
                ]
                step_duration = int((time.time() - step_start) * 1000)
                
                step3_complete = StreamingStepResult(
                    step=3,
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
                step3_complete = StreamingStepResult(
                    step=3,
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
            
            step_results.append(step3_complete.to_dict())
            yield f"data: {json.dumps({'type': 'step', 'data': step3_complete.to_dict()})}\n\n"

            # =========================================================================
            # STEP 4: Generate Response (LLM)
            # =========================================================================
            step_start = time.time()
            
            step4 = StreamingStepResult(
                step=4,
                action="Generating response",
                status="running",
                description="Synthesizing answer from all gathered context",
                reasoning="LLM processing with retrieved context and reasoning",
                details=[
                    {"type": "info", "content": f"Provider: {provider}"},
                    {"type": "info", "content": f"Model: {model}"},
                ]
            )
            yield f"data: {json.dumps({'type': 'step', 'data': step4.to_dict()})}\n\n"

            # Build context
            context = ""
            reasoning_context = ""
            if memory_results:
                context_assembler = ContextAssembler()
                context = context_assembler.assemble(scored_nodes=memory_results)
                
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
            provider_lower = provider.lower()
            
            try:
                if provider_lower == "gemini":
                    response_text = await llm._get_gemini().generate(
                        prompt=user_prompt, system_instruction=system_prompt,
                        model=model, api_key=custom_key_override,
                    )
                elif provider_lower == "groq":
                    response_text = await llm._get_groq().generate(
                        prompt=user_prompt, system_instruction=system_prompt,
                        model=model, api_key=custom_key_override,
                    )
                elif provider_lower == "nvidia":
                    response_text = await llm._get_nvidia().generate(
                        prompt=user_prompt, system_instruction=system_prompt,
                        model=model, api_key=custom_key_override,
                    )
                else:
                    response_text = await llm.generate(
                        prompt=user_prompt, system_instruction=system_prompt,
                        provider=provider, model=model,
                    )
            except Exception as llm_err:
                logger.error("llm_generation_error", error=str(llm_err))
                response_text = f"I apologize, but I encountered an error generating a response: {str(llm_err)[:100]}"
                confidence = 0.1

            step_duration = int((time.time() - step_start) * 1000)
            
            step4_complete = StreamingStepResult(
                step=4,
                action="Generating response",
                status="completed",
                description="Response generated successfully",
                reasoning=f"{'Used memory context with ' + str(len(memory_results)) + ' nodes' if context else 'No memory context available'}",
                result=f"Generated using {provider}/{model}",
                duration_ms=step_duration,
                details=[
                    {"type": "info", "content": f"Provider: {provider}"},
                    {"type": "info", "content": f"Model: {model}"},
                    {"type": "info", "content": f"Context tokens: ~{len(context) // 4}"},
                    {"type": "result", "content": f"Response generated ({len(response_text)} chars)"}
                ]
            )
            step_results.append(step4_complete.to_dict())
            yield f"data: {json.dumps({'type': 'step', 'data': step4_complete.to_dict()})}\n\n"

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
                    provider, model, confidence,
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
                    "model_used": model,
                    "provider_used": provider,
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
