"""API routes for integration management."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies.auth import get_current_user
from src.integrations.manager import IntegrationManager
from src.models.integrations import (
    IntegrationConnection,
    IntegrationConnectionCreate,
    IntegrationConnectionList,
    IntegrationConnectionUpdate,
    OAuth2InitiateRequest,
    OAuth2InitiateResponse,
)

integration_router = APIRouter(prefix="/integrations", tags=["integrations"])


@integration_router.get("/connections", response_model=IntegrationConnectionList)
async def list_connections(
    current_user: dict = Depends(get_current_user),
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    integration_type: Optional[str] = Query(None, description="Filter by type (slack, gmail, notion)"),
    scope: Optional[str] = Query(None, description="Filter by scope (personal, workspace)"),
    enabled_only: bool = Query(False, description="Only show enabled connections"),
):
    """List all integration connections for the current user.
    
    Returns connections across:
    - Personal integrations (user's Gmail, personal Slack, etc)
    - Workspace integrations (tenant's Slack workspace, Notion workspace, etc)
    """
    manager = IntegrationManager()
    
    connections = await manager.list_connections(
        user_id=current_user["id"],
        tenant_id=tenant_id,
        integration_type=integration_type,
        scope=scope,
        enabled_only=enabled_only,
    )
    
    return IntegrationConnectionList(
        connections=connections,
        total=len(connections),
    )


@integration_router.get("/connections/{connection_id}", response_model=IntegrationConnection)
async def get_connection(
    connection_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Get a specific integration connection."""
    manager = IntegrationManager()
    
    connection = await manager.get_connection(
        connection_id=connection_id,
        user_id=current_user["id"],
    )
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    return connection


@integration_router.post("/connections", response_model=IntegrationConnection, status_code=201)
async def create_connection(
    connection: IntegrationConnectionCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new integration connection.
    
    Note: This is typically called after OAuth flow completes.
    For initiating OAuth, use POST /integrations/oauth/initiate
    """
    manager = IntegrationManager()
    
    # Validate scope
    if connection.scope == "workspace" and not connection.tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id required for workspace scope")
    
    if connection.scope == "personal" and connection.tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id not allowed for personal scope")
    
    created = await manager.create_connection(
        user_id=current_user["id"],
        connection=connection,
    )
    
    return created


@integration_router.patch("/connections/{connection_id}", response_model=IntegrationConnection)
async def update_connection(
    connection_id: UUID,
    update: IntegrationConnectionUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update an integration connection."""
    manager = IntegrationManager()
    
    updated = await manager.update_connection(
        connection_id=connection_id,
        user_id=current_user["id"],
        update=update,
    )
    
    if not updated:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    return updated


@integration_router.delete("/connections/{connection_id}", status_code=204)
async def delete_connection(
    connection_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Delete an integration connection.
    
    This will:
    - Revoke OAuth tokens
    - Stop receiving webhooks
    - Remove the connection from the database
    """
    manager = IntegrationManager()
    
    deleted = await manager.delete_connection(
        connection_id=connection_id,
        user_id=current_user["id"],
    )
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    return None


@integration_router.post("/oauth/initiate", response_model=OAuth2InitiateResponse)
async def initiate_oauth(
    request: OAuth2InitiateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Initiate OAuth2 flow for an integration.
    
    Returns an authorization URL to redirect the user to.
    After user authorizes, they'll be redirected to the redirect_uri with a code.
    """
    # TODO: Implement OAuth initiation for each integration type
    # This will:
    # 1. Generate state parameter for CSRF protection
    # 2. Build authorization URL with correct scopes
    # 3. Store state in session/database
    # 4. Return URL to frontend
    
    raise HTTPException(status_code=501, detail="OAuth initiation not yet implemented")


@integration_router.post("/oauth/callback")
async def oauth_callback(
    code: str = Query(..., description="Authorization code"),
    state: str = Query(..., description="State parameter"),
    current_user: dict = Depends(get_current_user),
):
    """Handle OAuth2 callback.
    
    This endpoint is called by the OAuth provider after user authorizes.
    It exchanges the code for tokens and creates the integration connection.
    """
    # TODO: Implement OAuth callback handling
    # This will:
    # 1. Verify state parameter
    # 2. Exchange code for access/refresh tokens
    # 3. Fetch user/workspace info from integration API
    # 4. Create integration connection with tokens
    # 5. Return success response
    
    raise HTTPException(status_code=501, detail="OAuth callback not yet implemented")


@integration_router.get("/types")
async def list_integration_types():
    """List available integration types with their metadata."""
    return {
        "integrations": [
            {
                "type": "slack",
                "name": "Slack",
                "description": "Connect Slack workspaces to capture messages, reactions, and files",
                "scopes": ["personal", "workspace"],
                "supports_multiple": True,
                "oauth_required": True,
            },
            {
                "type": "gmail",
                "name": "Gmail",
                "description": "Connect Gmail to capture and analyze emails",
                "scopes": ["personal"],
                "supports_multiple": True,
                "oauth_required": True,
            },
            {
                "type": "notion",
                "name": "Notion",
                "description": "Connect Notion workspaces to capture pages, databases, and blocks",
                "scopes": ["personal", "workspace"],
                "supports_multiple": True,
                "oauth_required": True,
            },
            {
                "type": "github",
                "name": "GitHub",
                "description": "Connect GitHub repositories to capture issues, PRs, and commits",
                "scopes": ["personal", "workspace"],
                "supports_multiple": True,
                "oauth_required": True,
            },
        ]
    }
