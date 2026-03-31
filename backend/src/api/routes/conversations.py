"""Conversation routes for chat threads."""

from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.api.dependencies.auth import get_current_user_id
from src.core.logging import get_logger
from src.db.postgres import get_postgres_driver

router = APIRouter()
logger = get_logger(__name__)


class ConversationCreate(BaseModel):
    """Create conversation request."""
    workspace_id: UUID | None = None
    title: str | None = None


class ConversationUpdate(BaseModel):
    """Update conversation request."""
    title: str | None = None
    is_pinned: bool | None = None
    is_archived: bool | None = None


class MessageResponse(BaseModel):
    """Message response model."""
    id: UUID
    role: str
    content: str
    provider: str | None
    model: str | None
    confidence: float | None
    reasoning_path: list | None
    sources: list | None
    created_at: datetime


class ConversationResponse(BaseModel):
    """Conversation response model."""
    id: UUID
    workspace_id: UUID | None
    user_id: UUID
    title: str | None
    summary: str | None
    message_count: int
    is_pinned: bool
    is_archived: bool
    last_message_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ConversationWithMessages(ConversationResponse):
    """Conversation with messages."""
    messages: list[MessageResponse] = []


class ProcessingStepResponse(BaseModel):
    """Processing step response."""
    id: UUID
    step_number: int
    action: str
    status: str
    result: str | None
    reasoning: str | None
    duration_ms: int | None
    created_at: datetime


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    data: ConversationCreate,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> ConversationResponse:
    """Create a new conversation."""
    logger.info("conversation_create", user_id=str(user_id))
    
    postgres = get_postgres_driver()
    conversation_id = uuid4()
    
    async with postgres.connection() as conn:
        # If workspace specified, verify access
        if data.workspace_id:
            access = await conn.fetchrow(
                """
                SELECT 1 FROM chat.workspaces w
                LEFT JOIN chat.workspace_members wm ON w.id = wm.workspace_id
                WHERE w.id = $1 AND (w.owner_id = $2 OR wm.user_id = $2)
                """,
                data.workspace_id,
                user_id,
            )
            if not access:
                raise HTTPException(status_code=403, detail="No access to workspace")
        
        await conn.execute(
            """
            INSERT INTO chat.conversations (id, workspace_id, user_id, title)
            VALUES ($1, $2, $3, $4)
            """,
            conversation_id,
            data.workspace_id,
            user_id,
            data.title or "New Conversation",
        )
    
    return ConversationResponse(
        id=conversation_id,
        workspace_id=data.workspace_id,
        user_id=user_id,
        title=data.title or "New Conversation",
        summary=None,
        message_count=0,
        is_pinned=False,
        is_archived=False,
        last_message_at=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    workspace_id: UUID | None = Query(default=None),
    include_archived: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ConversationResponse]:
    """List conversations for current user."""
    postgres = get_postgres_driver()
    
    async with postgres.connection() as conn:
        if workspace_id:
            rows = await conn.fetch(
                """
                SELECT c.* FROM chat.conversations c
                JOIN chat.workspaces w ON c.workspace_id = w.id
                LEFT JOIN chat.workspace_members wm ON w.id = wm.workspace_id
                WHERE c.workspace_id = $1 
                  AND (w.owner_id = $2 OR wm.user_id = $2)
                  AND ($3 OR c.is_archived = FALSE)
                ORDER BY c.is_pinned DESC, COALESCE(c.last_message_at, c.created_at) DESC
                LIMIT $4 OFFSET $5
                """,
                workspace_id,
                user_id,
                include_archived,
                limit,
                offset,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT c.* FROM chat.conversations c
                WHERE c.user_id = $1 
                  AND c.workspace_id IS NULL
                  AND ($2 OR c.is_archived = FALSE)
                ORDER BY c.is_pinned DESC, COALESCE(c.last_message_at, c.created_at) DESC
                LIMIT $3 OFFSET $4
                """,
                user_id,
                include_archived,
                limit,
                offset,
            )
    
    return [
        ConversationResponse(
            id=row["id"],
            workspace_id=row["workspace_id"],
            user_id=row["user_id"],
            title=row["title"],
            summary=row["summary"],
            message_count=row["message_count"],
            is_pinned=row["is_pinned"],
            is_archived=row["is_archived"],
            last_message_at=row["last_message_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]


@router.get("/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    include_messages: bool = Query(default=True),
    message_limit: int = Query(default=100, ge=1, le=500),
) -> ConversationWithMessages:
    """Get a conversation with optional messages."""
    postgres = get_postgres_driver()
    
    async with postgres.connection() as conn:
        # Get conversation with access check
        row = await conn.fetchrow(
            """
            SELECT c.* FROM chat.conversations c
            LEFT JOIN chat.workspaces w ON c.workspace_id = w.id
            LEFT JOIN chat.workspace_members wm ON w.id = wm.workspace_id
            WHERE c.id = $1 
              AND (c.user_id = $2 OR w.owner_id = $2 OR wm.user_id = $2)
            """,
            conversation_id,
            user_id,
        )
        
        if not row:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = []
        if include_messages:
            message_rows = await conn.fetch(
                """
                SELECT * FROM chat.messages
                WHERE conversation_id = $1
                ORDER BY created_at ASC
                LIMIT $2
                """,
                conversation_id,
                message_limit,
            )
            
            messages = [
                MessageResponse(
                    id=m["id"],
                    role=m["role"],
                    content=m["content"],
                    provider=m["provider"],
                    model=m["model"],
                    confidence=m["confidence"],
                    reasoning_path=m["reasoning_path"],
                    sources=m["sources"],
                    created_at=m["created_at"],
                )
                for m in message_rows
            ]
    
    return ConversationWithMessages(
        id=row["id"],
        workspace_id=row["workspace_id"],
        user_id=row["user_id"],
        title=row["title"],
        summary=row["summary"],
        message_count=row["message_count"],
        is_pinned=row["is_pinned"],
        is_archived=row["is_archived"],
        last_message_at=row["last_message_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        messages=messages,
    )


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    update: ConversationUpdate,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> ConversationResponse:
    """Update a conversation."""
    postgres = get_postgres_driver()
    
    updates = []
    params = []
    param_idx = 1
    
    if update.title is not None:
        updates.append(f"title = ${param_idx}")
        params.append(update.title)
        param_idx += 1
    if update.is_pinned is not None:
        updates.append(f"is_pinned = ${param_idx}")
        params.append(update.is_pinned)
        param_idx += 1
    if update.is_archived is not None:
        updates.append(f"is_archived = ${param_idx}")
        params.append(update.is_archived)
        param_idx += 1
    
    if not updates:
        return await get_conversation(conversation_id, user_id, include_messages=False)
    
    params.extend([conversation_id, user_id])
    
    async with postgres.connection() as conn:
        await conn.execute(
            f"""
            UPDATE chat.conversations
            SET {', '.join(updates)}, updated_at = NOW()
            WHERE id = ${param_idx} AND user_id = ${param_idx + 1}
            """,
            *params,
        )
    
    result = await get_conversation(conversation_id, user_id, include_messages=False)
    return ConversationResponse(**result.model_dump(exclude={"messages"}))


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> dict:
    """Delete a conversation and all its messages."""
    postgres = get_postgres_driver()
    
    async with postgres.connection() as conn:
        # Verify ownership
        row = await conn.fetchrow(
            "SELECT user_id FROM chat.conversations WHERE id = $1",
            conversation_id,
        )
        
        if not row or row["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Cannot delete this conversation")
        
        # Delete (cascades to messages and processing_steps)
        await conn.execute(
            "DELETE FROM chat.conversations WHERE id = $1",
            conversation_id,
        )
    
    return {"message": "Conversation deleted", "id": str(conversation_id)}


@router.get("/{conversation_id}/steps", response_model=list[ProcessingStepResponse])
async def get_processing_steps(
    conversation_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    message_id: UUID | None = Query(default=None),
) -> list[ProcessingStepResponse]:
    """Get processing steps for a conversation or specific message."""
    postgres = get_postgres_driver()
    
    async with postgres.connection() as conn:
        # Verify access
        access = await conn.fetchrow(
            """
            SELECT 1 FROM chat.conversations c
            LEFT JOIN chat.workspaces w ON c.workspace_id = w.id
            LEFT JOIN chat.workspace_members wm ON w.id = wm.workspace_id
            WHERE c.id = $1 AND (c.user_id = $2 OR w.owner_id = $2 OR wm.user_id = $2)
            """,
            conversation_id,
            user_id,
        )
        
        if not access:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if message_id:
            rows = await conn.fetch(
                """
                SELECT * FROM chat.processing_steps
                WHERE message_id = $1
                ORDER BY step_number ASC
                """,
                message_id,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT * FROM chat.processing_steps
                WHERE conversation_id = $1
                ORDER BY created_at DESC, step_number ASC
                LIMIT 100
                """,
                conversation_id,
            )
    
    return [
        ProcessingStepResponse(
            id=row["id"],
            step_number=row["step_number"],
            action=row["action"],
            status=row["status"],
            result=row["result"],
            reasoning=row["reasoning"],
            duration_ms=row["duration_ms"],
            created_at=row["created_at"],
        )
        for row in rows
    ]
