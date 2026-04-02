"""Workspace routes for chat context management."""

from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4
import secrets

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.api.dependencies.auth import get_current_user_id
from src.core.logging import get_logger
from src.db.postgres import get_postgres_driver

router = APIRouter()
logger = get_logger(__name__)


class WorkspaceCreate(BaseModel):
    """Create workspace request."""
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    is_public: bool = False
    memory_enabled: bool = True
    default_provider: str = "nvidia"
    default_model: str = "devstral-2-123b"


class WorkspaceUpdate(BaseModel):
    """Update workspace request."""
    name: str | None = None
    description: str | None = None
    is_public: bool | None = None
    memory_enabled: bool | None = None
    default_provider: str | None = None
    default_model: str | None = None


class WorkspaceResponse(BaseModel):
    """Workspace response model."""
    id: UUID
    name: str
    description: str | None
    owner_id: UUID
    share_token: str | None
    is_public: bool
    status: str
    memory_enabled: bool
    default_provider: str
    default_model: str
    member_count: int = 0
    conversation_count: int = 0
    created_at: datetime
    updated_at: datetime


class WorkspaceMemberResponse(BaseModel):
    """Workspace member response."""
    user_id: UUID
    email: str
    full_name: str | None
    role: str
    can_write: bool
    joined_at: datetime


@router.post("", response_model=WorkspaceResponse)
async def create_workspace(
    workspace: WorkspaceCreate,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> WorkspaceResponse:
    """Create a new workspace."""
    logger.info("workspace_create", user_id=str(user_id), name=workspace.name)
    
    postgres = get_postgres_driver()
    workspace_id = uuid4()
    share_token = secrets.token_hex(32)
    
    async with postgres.connection() as conn:
        await conn.execute(
            """
            INSERT INTO chat.workspaces 
            (id, name, description, owner_id, share_token, is_public, memory_enabled, default_provider, default_model)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            workspace_id,
            workspace.name,
            workspace.description,
            user_id,
            share_token,
            workspace.is_public,
            workspace.memory_enabled,
            workspace.default_provider,
            workspace.default_model,
        )
        
        # Add owner as member
        await conn.execute(
            """
            INSERT INTO chat.workspace_members (workspace_id, user_id, role, can_write)
            VALUES ($1, $2, 'owner', TRUE)
            """,
            workspace_id,
            user_id,
        )
    
    return WorkspaceResponse(
        id=workspace_id,
        name=workspace.name,
        description=workspace.description,
        owner_id=user_id,
        share_token=share_token,
        is_public=workspace.is_public,
        status="active",
        memory_enabled=workspace.memory_enabled,
        default_provider=workspace.default_provider,
        default_model=workspace.default_model,
        member_count=1,
        conversation_count=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    include_shared: bool = Query(default=True),
) -> list[WorkspaceResponse]:
    """List workspaces for current user."""
    postgres = get_postgres_driver()
    
    async with postgres.connection() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT w.*, 
                   (SELECT COUNT(*) FROM chat.workspace_members WHERE workspace_id = w.id) as member_count,
                   (SELECT COUNT(*) FROM chat.conversations WHERE workspace_id = w.id) as conversation_count
            FROM chat.workspaces w
            LEFT JOIN chat.workspace_members wm ON w.id = wm.workspace_id
            WHERE (w.owner_id = $1 OR (wm.user_id = $1 AND $2))
              AND w.status = 'active'
            ORDER BY w.updated_at DESC
            """,
            user_id,
            include_shared,
        )
    
    return [
        WorkspaceResponse(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            owner_id=row["owner_id"],
            share_token=row["share_token"] if row["owner_id"] == user_id else None,
            is_public=row["is_public"],
            status=row["status"],
            memory_enabled=row["memory_enabled"],
            default_provider=row["default_provider"],
            default_model=row["default_model"],
            member_count=row["member_count"],
            conversation_count=row["conversation_count"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> WorkspaceResponse:
    """Get a workspace by ID."""
    postgres = get_postgres_driver()
    
    async with postgres.connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT w.*, 
                   (SELECT COUNT(*) FROM chat.workspace_members WHERE workspace_id = w.id) as member_count,
                   (SELECT COUNT(*) FROM chat.conversations WHERE workspace_id = w.id) as conversation_count
            FROM chat.workspaces w
            LEFT JOIN chat.workspace_members wm ON w.id = wm.workspace_id
            WHERE w.id = $1 
              AND (w.owner_id = $2 OR wm.user_id = $2 OR w.is_public = TRUE)
              AND w.status = 'active'
            """,
            workspace_id,
            user_id,
        )
    
    if not row:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    return WorkspaceResponse(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        owner_id=row["owner_id"],
        share_token=row["share_token"] if row["owner_id"] == user_id else None,
        is_public=row["is_public"],
        status=row["status"],
        memory_enabled=row["memory_enabled"],
        default_provider=row["default_provider"],
        default_model=row["default_model"],
        member_count=row["member_count"],
        conversation_count=row["conversation_count"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: UUID,
    update: WorkspaceUpdate,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> WorkspaceResponse:
    """Update a workspace."""
    postgres = get_postgres_driver()
    
    # Build update query dynamically
    updates = []
    params = []
    param_idx = 1
    
    if update.name is not None:
        updates.append(f"name = ${param_idx}")
        params.append(update.name)
        param_idx += 1
    if update.description is not None:
        updates.append(f"description = ${param_idx}")
        params.append(update.description)
        param_idx += 1
    if update.is_public is not None:
        updates.append(f"is_public = ${param_idx}")
        params.append(update.is_public)
        param_idx += 1
    if update.memory_enabled is not None:
        updates.append(f"memory_enabled = ${param_idx}")
        params.append(update.memory_enabled)
        param_idx += 1
    if update.default_provider is not None:
        updates.append(f"default_provider = ${param_idx}")
        params.append(update.default_provider)
        param_idx += 1
    if update.default_model is not None:
        updates.append(f"default_model = ${param_idx}")
        params.append(update.default_model)
        param_idx += 1
    
    if not updates:
        return await get_workspace(workspace_id, user_id)
    
    params.append(workspace_id)
    params.append(user_id)
    
    async with postgres.connection() as conn:
        await conn.execute(
            f"""
            UPDATE chat.workspaces
            SET {', '.join(updates)}, updated_at = NOW()
            WHERE id = ${param_idx} AND owner_id = ${param_idx + 1}
            """,
            *params,
        )
    
    return await get_workspace(workspace_id, user_id)


@router.delete("/{workspace_id}")
async def delete_workspace(
    workspace_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> dict:
    """Delete (archive) a workspace."""
    postgres = get_postgres_driver()
    
    async with postgres.connection() as conn:
        result = await conn.execute(
            """
            UPDATE chat.workspaces
            SET status = 'deleted', updated_at = NOW()
            WHERE id = $1 AND owner_id = $2
            """,
            workspace_id,
            user_id,
        )
    
    return {"message": "Workspace deleted", "id": str(workspace_id)}


@router.post("/{workspace_id}/join")
async def join_workspace_by_token(
    workspace_id: UUID,
    share_token: str,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> dict:
    """Join a workspace using a share token."""
    postgres = get_postgres_driver()
    
    async with postgres.connection() as conn:
        # Verify token
        workspace = await conn.fetchrow(
            """
            SELECT id, name FROM chat.workspaces
            WHERE id = $1 AND share_token = $2 AND status = 'active'
            """,
            workspace_id,
            share_token,
        )
        
        if not workspace:
            raise HTTPException(status_code=404, detail="Invalid workspace or token")
        
        # Check if already a member
        existing = await conn.fetchrow(
            """
            SELECT 1 FROM chat.workspace_members
            WHERE workspace_id = $1 AND user_id = $2
            """,
            workspace_id,
            user_id,
        )
        
        if existing:
            return {"message": "Already a member", "workspace_id": str(workspace_id)}
        
        # Add as member
        await conn.execute(
            """
            INSERT INTO chat.workspace_members (workspace_id, user_id, role, can_write)
            VALUES ($1, $2, 'member', TRUE)
            """,
            workspace_id,
            user_id,
        )
    
    return {
        "message": f"Joined workspace '{workspace['name']}'",
        "workspace_id": str(workspace_id),
    }


@router.get("/{workspace_id}/members", response_model=list[WorkspaceMemberResponse])
async def list_workspace_members(
    workspace_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> list[WorkspaceMemberResponse]:
    """List members of a workspace."""
    postgres = get_postgres_driver()
    
    async with postgres.connection() as conn:
        # Check access
        access = await conn.fetchrow(
            """
            SELECT 1 FROM chat.workspaces w
            LEFT JOIN chat.workspace_members wm ON w.id = wm.workspace_id
            WHERE w.id = $1 AND (w.owner_id = $2 OR wm.user_id = $2)
            """,
            workspace_id,
            user_id,
        )
        
        if not access:
            raise HTTPException(status_code=403, detail="Access denied")
        
        rows = await conn.fetch(
            """
            SELECT wm.*, u.email, u.full_name
            FROM chat.workspace_members wm
            JOIN auth.users u ON wm.user_id = u.id
            WHERE wm.workspace_id = $1
            ORDER BY wm.role DESC, wm.joined_at
            """,
            workspace_id,
        )
    
    return [
        WorkspaceMemberResponse(
            user_id=row["user_id"],
            email=row["email"],
            full_name=row["full_name"],
            role=row["role"],
            can_write=row["can_write"],
            joined_at=row["joined_at"],
        )
        for row in rows
    ]


@router.post("/{workspace_id}/regenerate-token")
async def regenerate_share_token(
    workspace_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> dict:
    """Regenerate the share token for a workspace."""
    postgres = get_postgres_driver()
    new_token = secrets.token_hex(32)
    
    async with postgres.connection() as conn:
        result = await conn.execute(
            """
            UPDATE chat.workspaces
            SET share_token = $1, updated_at = NOW()
            WHERE id = $2 AND owner_id = $3
            """,
            new_token,
            workspace_id,
            user_id,
        )
    
    return {"share_token": new_token}
