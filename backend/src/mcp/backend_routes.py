"""Backend route client for MCP tools.

This module provides a single HTTP client abstraction used by MCP tools to call
the same FastAPI backend routes exposed under /api/v1.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class BackendRouteError(RuntimeError):
    """Raised when a backend route call fails."""


def resolve_backend_base_url(session_ctx: dict[str, Any]) -> str:
    """Resolve backend API base URL for MCP route calls."""
    explicit = session_ctx.get("backend_url")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.rstrip("/")

    env_base = os.environ.get("NEUROGRAPH_BACKEND_URL")
    if env_base:
        return env_base.rstrip("/")

    settings = get_settings()
    return f"http://{settings.host}:{settings.port}/api/v1"


class BackendRoutesClient:
    """Thin HTTP client for calling backend routes from MCP tools."""

    def __init__(self, session_ctx: dict[str, Any]) -> None:
        self._base_url = resolve_backend_base_url(session_ctx)
        self._access_token = session_ctx.get("access_token")
        self._api_key = session_ctx.get("api_key")

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        elif self._api_key:
            # Kept for compatibility, although core API routes are JWT-authenticated.
            headers["X-API-Key"] = str(self._api_key)
        return headers

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Any = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a backend API request and return parsed JSON payload."""
        clean_path = path if path.startswith("/") else f"/{path}"
        url = f"{self._base_url}{clean_path}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self._headers(),
                params=params,
                json=json_body,
            )

        if response.status_code >= 400:
            detail: str
            try:
                payload = response.json()
                detail = str(payload.get("detail", payload))
            except Exception:
                detail = response.text.strip() or "request failed"

            logger.warning(
                "mcp_backend_route_failed",
                method=method,
                path=clean_path,
                status=response.status_code,
                detail=detail[:400],
            )
            raise BackendRouteError(
                f"{method.upper()} {clean_path} failed ({response.status_code}): {detail}"
            )

        if not response.content:
            return {}

        try:
            return response.json()
        except Exception as exc:
            raise BackendRouteError(
                f"{method.upper()} {clean_path} returned non-JSON response"
            ) from exc
