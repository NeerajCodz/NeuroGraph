"""Models for integration connections."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class IntegrationConnectionBase(BaseModel):
    """Base model for integration connection."""
    
    integration_type: str = Field(..., description="Integration type (slack, gmail, notion, etc)")
    scope: str = Field("personal", description="Scope: personal or workspace")
    name: Optional[str] = Field(None, description="User-defined name for this connection")
    config: Dict[str, Any] = Field(default_factory=dict, description="Integration-specific configuration")
    enabled: bool = Field(True, description="Whether this connection is enabled")


class IntegrationConnectionCreate(IntegrationConnectionBase):
    """Create integration connection."""
    
    tenant_id: Optional[UUID] = Field(None, description="Tenant ID for workspace scope")
    external_id: Optional[str] = Field(None, description="External workspace/team ID")
    external_name: Optional[str] = Field(None, description="External workspace/team name")


class IntegrationConnectionUpdate(BaseModel):
    """Update integration connection."""
    
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


class IntegrationConnection(IntegrationConnectionBase):
    """Integration connection response model."""
    
    id: UUID
    user_id: Optional[UUID]
    tenant_id: Optional[UUID]
    external_id: Optional[str]
    external_name: Optional[str]
    status: str
    last_sync_at: Optional[datetime]
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # Don't expose tokens in API responses
    # access_token and refresh_token are excluded
    
    class Config:
        from_attributes = True


class IntegrationConnectionList(BaseModel):
    """List of integration connections."""
    
    connections: list[IntegrationConnection]
    total: int


class OAuth2InitiateRequest(BaseModel):
    """Request to initiate OAuth2 flow."""
    
    integration_type: str = Field(..., description="Integration type")
    scope: str = Field("personal", description="personal or workspace")
    tenant_id: Optional[UUID] = Field(None, description="Tenant ID for workspace scope")
    redirect_uri: str = Field(..., description="Redirect URI after OAuth")


class OAuth2InitiateResponse(BaseModel):
    """Response with OAuth authorization URL."""
    
    authorization_url: str = Field(..., description="URL to redirect user to")
    state: str = Field(..., description="State parameter for CSRF protection")


class OAuth2CallbackRequest(BaseModel):
    """OAuth2 callback parameters."""
    
    code: str = Field(..., description="Authorization code")
    state: str = Field(..., description="State parameter")


class IntegrationStats(BaseModel):
    """Integration statistics."""
    
    integration_type: str
    total_connections: int
    active_connections: int
    personal_connections: int
    workspace_connections: int
    last_sync: Optional[datetime]


class IntegrationHealth(BaseModel):
    """Integration health check."""
    
    connection_id: UUID
    status: str  # healthy, warning, error
    message: Optional[str]
    last_checked: datetime
