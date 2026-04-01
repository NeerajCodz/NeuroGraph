"""Base normalizer for webhook events."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ExtractedEntity(BaseModel):
    """Entity extracted from webhook event."""
    
    name: str = Field(..., description="Entity name")
    type: str = Field(..., description="Entity type (person, channel, project, etc)")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")


class NormalizedEvent(BaseModel):
    """Standardized event format across all integrations."""
    
    event_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique event identifier")
    event_type: str = Field(..., description="Event type (message, issue, commit, email, etc)")
    source: str = Field(..., description="Integration source (slack, github, gmail, etc)")
    content: str = Field(..., description="Extracted text content")
    layer: str = Field(..., description="Memory layer (personal, tenant, global)")
    
    # User/Tenant context
    user_id: Optional[str] = Field(None, description="User ID from NeuroGraph")
    user_external_id: Optional[str] = Field(None, description="External user ID (slack user, github login, email)")
    tenant_id: Optional[str] = Field(None, description="Tenant/Organization ID")
    
    # Extracted entities
    entities: List[ExtractedEntity] = Field(default_factory=list, description="Entities extracted from content")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Source-specific metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    processed_at: Optional[datetime] = None
    processing_time_ms: Optional[int] = None


class BaseNormalizer(ABC):
    """Base class for event normalizers.
    
    Each integration (Slack, GitHub, Gmail, etc) implements a normalizer
    that converts platform-specific events into standardized NormalizedEvent format.
    """
    
    def __init__(self, integration_name: str):
        """Initialize normalizer.
        
        Args:
            integration_name: Name of the integration (slack, github, etc)
        """
        self.integration_name = integration_name
    
    @abstractmethod
    async def normalize(self, event_data: Dict[str, Any]) -> NormalizedEvent:
        """Normalize event data to standard format.
        
        Args:
            event_data: Raw webhook event data
            
        Returns:
            NormalizedEvent with standardized format
            
        Raises:
            ValueError: If event type is not supported
        """
        pass
    
    def extract_user(self, event_data: Dict[str, Any]) -> Optional[str]:
        """Extract user identifier from event.
        
        Args:
            event_data: Raw webhook event data
            
        Returns:
            User identifier or None
        """
        return None
    
    def extract_content(self, event_data: Dict[str, Any]) -> str:
        """Extract text content from event.
        
        Args:
            event_data: Raw webhook event data
            
        Returns:
            Extracted text content
        """
        return ""
    
    def extract_entities(self, event_data: Dict[str, Any]) -> List[ExtractedEntity]:
        """Extract entities from event.
        
        Args:
            event_data: Raw webhook event data
            
        Returns:
            List of extracted entities
        """
        return []
    
    async def resolve_user_id(self, external_id: str) -> Optional[str]:
        """Resolve external user ID to NeuroGraph user ID.
        
        This should query the database to find the NeuroGraph user
        associated with the external user ID (Slack user, GitHub login, email).
        
        Args:
            external_id: External user identifier
            
        Returns:
            NeuroGraph user ID or None if not found
        """
        # TODO: Implement user resolution via database lookup
        # For now, return None to use anonymous/system user
        return None
