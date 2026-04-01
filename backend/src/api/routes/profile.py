"""Profile and user settings routes."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.api.dependencies import get_current_user_id
from src.auth.passwords import hash_password, verify_password
from src.core.logging import get_logger
from src.db.postgres import get_postgres_driver
from src.models.unified_llm import get_unified_llm

logger = get_logger(__name__)
router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileUpdateRequest(BaseModel):
    """Profile update payload."""

    full_name: str = Field(min_length=1, max_length=255)


class PasswordUpdateRequest(BaseModel):
    """Password update payload."""

    current_password: str = Field(min_length=1, max_length=255)
    new_password: str = Field(min_length=8, max_length=255)
    confirm_password: str = Field(min_length=8, max_length=255)


class AiKeyInput(BaseModel):
    """Custom provider API key input."""

    provider: str = Field(pattern="^(gemini|groq|nvidia)$")
    api_key: str = Field(min_length=1, max_length=512)


class ProfileSettingsUpdateRequest(BaseModel):
    """Profile settings update payload."""

    default_provider: str | None = None
    default_model: str | None = None
    default_memory_layer: str | None = Field(default=None, pattern="^(personal|workspace|global)$")
    theme: str | None = Field(default=None, pattern="^(dark|light|system)$")
    compact_mode: bool | None = None
    show_confidence: bool | None = None
    show_reasoning: bool | None = None
    agents_enabled: bool | None = None
    agent_orchestrator_enabled: bool | None = None
    agent_memory_enabled: bool | None = None
    agent_web_enabled: bool | None = None
    agent_parallel_enabled: bool | None = None
    agent_safe_mode: bool | None = None
    agent_auto_retry: bool | None = None
    auto_memory_update: bool | None = None
    analytics_enabled: bool | None = None
    sidebar_collapsed: bool | None = None
    custom_keys: list[AiKeyInput] | None = None


class ProfileSettingsResponse(BaseModel):
    """Profile settings response payload."""

    user: dict[str, Any]
    settings: dict[str, Any]


def _json_get_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    return default


def _json_get_str(value: Any, default: str) -> str:
    if isinstance(value, str) and value:
        return value
    return default


def _mask_key(key: str) -> str:
    if len(key) <= 8:
        return "*" * len(key)
    return f"{key[:4]}...{key[-4:]}"


async def _ensure_user_preferences(user_id: UUID) -> None:
    postgres = get_postgres_driver()
    async with postgres.connection() as conn:
        await conn.execute(
            """
            INSERT INTO chat.user_preferences (user_id)
            VALUES ($1)
            ON CONFLICT (user_id) DO NOTHING
            """,
            user_id,
        )


@router.get("/settings", response_model=ProfileSettingsResponse)
async def get_profile_settings(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> ProfileSettingsResponse:
    """Get profile settings + user preference bundle."""
    await _ensure_user_preferences(user_id)

    postgres = get_postgres_driver()
    async with postgres.connection() as conn:
        user_row = await conn.fetchrow(
            """
            SELECT id, email, full_name, is_active, created_at
            FROM auth.users
            WHERE id = $1
            """,
            user_id,
        )
        if not user_row:
            raise HTTPException(status_code=404, detail="User not found")

        pref_row = await conn.fetchrow(
            """
            SELECT default_provider, default_model, default_memory_layer, agents_enabled, theme, settings
            FROM chat.user_preferences
            WHERE user_id = $1
            """,
            user_id,
        )

    settings_json = pref_row["settings"] if isinstance(pref_row["settings"], dict) else {}
    custom_keys = settings_json.get("custom_provider_keys", {})
    if not isinstance(custom_keys, dict):
        custom_keys = {}

    custom_key_status: dict[str, dict[str, str | bool]] = {}
    for provider in ("gemini", "groq", "nvidia"):
        provider_key = custom_keys.get(provider)
        if isinstance(provider_key, str) and provider_key:
            custom_key_status[provider] = {
                "configured": True,
                "masked": _mask_key(provider_key),
            }
        else:
            custom_key_status[provider] = {
                "configured": False,
                "masked": "",
            }

    llm = get_unified_llm()
    providers = llm.get_available_providers()
    provider_models = {p["id"]: p.get("models", []) for p in providers}

    return ProfileSettingsResponse(
        user={
            "id": str(user_row["id"]),
            "email": user_row["email"],
            "full_name": user_row["full_name"],
            "is_active": user_row["is_active"],
            "created_at": user_row["created_at"].isoformat(),
        },
        settings={
            "default_provider": pref_row["default_provider"],
            "default_model": pref_row["default_model"],
            "default_memory_layer": pref_row["default_memory_layer"],
            "agents_enabled": pref_row["agents_enabled"],
            "theme": _json_get_str(settings_json.get("theme"), pref_row["theme"] or "dark"),
            "compact_mode": _json_get_bool(settings_json.get("compact_mode"), False),
            "show_confidence": _json_get_bool(settings_json.get("show_confidence"), True),
            "show_reasoning": _json_get_bool(settings_json.get("show_reasoning"), True),
            "agent_orchestrator_enabled": _json_get_bool(settings_json.get("agent_orchestrator_enabled"), True),
            "agent_memory_enabled": _json_get_bool(settings_json.get("agent_memory_enabled"), True),
            "agent_web_enabled": _json_get_bool(settings_json.get("agent_web_enabled"), True),
            "agent_parallel_enabled": _json_get_bool(settings_json.get("agent_parallel_enabled"), True),
            "agent_safe_mode": _json_get_bool(settings_json.get("agent_safe_mode"), True),
            "agent_auto_retry": _json_get_bool(settings_json.get("agent_auto_retry"), True),
            "auto_memory_update": _json_get_bool(settings_json.get("auto_memory_update"), True),
            "analytics_enabled": _json_get_bool(settings_json.get("analytics_enabled"), True),
            "sidebar_collapsed": _json_get_bool(settings_json.get("sidebar_collapsed"), False),
            "custom_provider_keys": custom_key_status,
            "available_providers": providers,
            "available_models": provider_models,
        },
    )


@router.patch("/user")
async def update_profile_user(
    payload: ProfileUpdateRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> dict[str, Any]:
    """Update current user's profile fields."""
    postgres = get_postgres_driver()
    async with postgres.connection() as conn:
        updated = await conn.fetchrow(
            """
            UPDATE auth.users
            SET full_name = $1, updated_at = NOW()
            WHERE id = $2
            RETURNING id, email, full_name, is_active, created_at
            """,
            payload.full_name.strip(),
            user_id,
        )
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": str(updated["id"]),
        "email": updated["email"],
        "full_name": updated["full_name"],
        "is_active": updated["is_active"],
        "created_at": updated["created_at"].isoformat(),
    }


@router.patch("/password")
async def update_profile_password(
    payload: PasswordUpdateRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> dict[str, str]:
    """Update current user's password."""
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="New password and confirmation do not match")

    postgres = get_postgres_driver()
    async with postgres.connection() as conn:
        row = await conn.fetchrow(
            "SELECT hashed_password FROM auth.users WHERE id = $1",
            user_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        if not verify_password(payload.current_password, row["hashed_password"]):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        new_hash = hash_password(payload.new_password)
        await conn.execute(
            "UPDATE auth.users SET hashed_password = $1, updated_at = NOW() WHERE id = $2",
            new_hash,
            user_id,
        )

    return {"message": "Password updated successfully"}


@router.patch("/settings")
async def update_profile_settings(
    payload: ProfileSettingsUpdateRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> dict[str, str]:
    """Persist profile settings and preferences."""
    await _ensure_user_preferences(user_id)
    postgres = get_postgres_driver()

    async with postgres.connection() as conn:
        pref_row = await conn.fetchrow(
            """
            SELECT settings
            FROM chat.user_preferences
            WHERE user_id = $1
            """,
            user_id,
        )
        current_settings = pref_row["settings"] if pref_row and isinstance(pref_row["settings"], dict) else {}
        current_settings = dict(current_settings)

        if payload.theme is not None:
            current_settings["theme"] = payload.theme
        if payload.compact_mode is not None:
            current_settings["compact_mode"] = payload.compact_mode
        if payload.show_confidence is not None:
            current_settings["show_confidence"] = payload.show_confidence
        if payload.show_reasoning is not None:
            current_settings["show_reasoning"] = payload.show_reasoning
        if payload.agent_orchestrator_enabled is not None:
            current_settings["agent_orchestrator_enabled"] = payload.agent_orchestrator_enabled
        if payload.agent_memory_enabled is not None:
            current_settings["agent_memory_enabled"] = payload.agent_memory_enabled
        if payload.agent_web_enabled is not None:
            current_settings["agent_web_enabled"] = payload.agent_web_enabled
        if payload.agent_parallel_enabled is not None:
            current_settings["agent_parallel_enabled"] = payload.agent_parallel_enabled
        if payload.agent_safe_mode is not None:
            current_settings["agent_safe_mode"] = payload.agent_safe_mode
        if payload.agent_auto_retry is not None:
            current_settings["agent_auto_retry"] = payload.agent_auto_retry
        if payload.auto_memory_update is not None:
            current_settings["auto_memory_update"] = payload.auto_memory_update
        if payload.analytics_enabled is not None:
            current_settings["analytics_enabled"] = payload.analytics_enabled
        if payload.sidebar_collapsed is not None:
            current_settings["sidebar_collapsed"] = payload.sidebar_collapsed

        if payload.custom_keys is not None:
            custom_provider_keys: dict[str, str] = {}
            for item in payload.custom_keys:
                custom_provider_keys[item.provider] = item.api_key
            current_settings["custom_provider_keys"] = custom_provider_keys

        default_memory_layer = payload.default_memory_layer
        if default_memory_layer == "workspace":
            default_memory_layer = "tenant"

        await conn.execute(
            """
            UPDATE chat.user_preferences
            SET default_provider = COALESCE($1, default_provider),
                default_model = COALESCE($2, default_model),
                default_memory_layer = COALESCE($3, default_memory_layer),
                agents_enabled = COALESCE($4, agents_enabled),
                theme = COALESCE($5, theme),
                settings = $6::jsonb,
                updated_at = NOW()
            WHERE user_id = $7
            """,
            payload.default_provider,
            payload.default_model,
            default_memory_layer,
            payload.agents_enabled,
            payload.theme,
            current_settings,
            user_id,
        )

    return {"message": "Settings updated"}


@router.get("/export")
async def export_profile_data(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> dict[str, Any]:
    """Export user profile/chat/memory/settings as JSON payload."""
    await _ensure_user_preferences(user_id)
    postgres = get_postgres_driver()

    async with postgres.connection() as conn:
        user_row = await conn.fetchrow(
            """
            SELECT id, email, full_name, is_active, created_at, updated_at
            FROM auth.users
            WHERE id = $1
            """,
            user_id,
        )
        if not user_row:
            raise HTTPException(status_code=404, detail="User not found")

        pref_row = await conn.fetchrow(
            """
            SELECT default_provider, default_model, default_memory_layer, agents_enabled, theme, settings, updated_at
            FROM chat.user_preferences
            WHERE user_id = $1
            """,
            user_id,
        )

        conversations = await conn.fetch(
            """
            SELECT id, workspace_id, title, message_count, is_pinned, is_archived, created_at, updated_at
            FROM chat.conversations
            WHERE user_id = $1
            ORDER BY updated_at DESC
            LIMIT 200
            """,
            user_id,
        )
        conversation_ids = [row["id"] for row in conversations]
        messages = await conn.fetch(
            """
            SELECT id, conversation_id, role, content, provider, model, confidence, created_at
            FROM chat.messages
            WHERE conversation_id = ANY($1::uuid[])
            ORDER BY created_at ASC
            LIMIT 2000
            """,
            conversation_ids if conversation_ids else [],
        )

        memories = await conn.fetch(
            """
            SELECT id, node_id, layer, content, confidence, created_at, updated_at, metadata
            FROM memory.embeddings
            WHERE user_id = $1 OR tenant_id IN (
                SELECT workspace_id FROM chat.workspace_members WHERE user_id = $1
            )
            ORDER BY updated_at DESC
            LIMIT 2000
            """,
            user_id,
        )

    return {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "user": {
            "id": str(user_row["id"]),
            "email": user_row["email"],
            "full_name": user_row["full_name"],
            "is_active": user_row["is_active"],
            "created_at": user_row["created_at"].isoformat(),
            "updated_at": user_row["updated_at"].isoformat() if user_row["updated_at"] else None,
        },
        "preferences": {
            "default_provider": pref_row["default_provider"],
            "default_model": pref_row["default_model"],
            "default_memory_layer": pref_row["default_memory_layer"],
            "agents_enabled": pref_row["agents_enabled"],
            "theme": pref_row["theme"],
            "settings": pref_row["settings"] if isinstance(pref_row["settings"], dict) else {},
            "updated_at": pref_row["updated_at"].isoformat() if pref_row["updated_at"] else None,
        },
        "conversations": [
            {
                "id": str(row["id"]),
                "workspace_id": str(row["workspace_id"]) if row["workspace_id"] else None,
                "title": row["title"],
                "message_count": row["message_count"],
                "is_pinned": row["is_pinned"],
                "is_archived": row["is_archived"],
                "created_at": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat(),
            }
            for row in conversations
        ],
        "messages": [
            {
                "id": str(row["id"]),
                "conversation_id": str(row["conversation_id"]),
                "role": row["role"],
                "content": row["content"],
                "provider": row["provider"],
                "model": row["model"],
                "confidence": row["confidence"],
                "created_at": row["created_at"].isoformat(),
            }
            for row in messages
        ],
        "memories": [
            {
                "id": str(row["id"]),
                "node_id": row["node_id"],
                "layer": row["layer"],
                "content": row["content"],
                "confidence": row["confidence"],
                "metadata": row["metadata"] if isinstance(row["metadata"], dict) else {},
                "created_at": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            }
            for row in memories
        ],
    }
