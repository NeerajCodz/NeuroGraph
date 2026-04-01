"""Notion event normalizer."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.logging import get_logger
from src.integrations.base.normalizer import (
    BaseNormalizer,
    ExtractedEntity,
    NormalizedEvent,
)

logger = get_logger(__name__)


class NotionNormalizer(BaseNormalizer):
    """Normalize Notion webhook events to standard format."""
    
    def __init__(self, notion_client=None):
        super().__init__("notion")
        self.notion_client = notion_client
    
    async def normalize(self, event_data: Dict[str, Any]) -> NormalizedEvent:
        """Normalize Notion webhook event to standard format.
        
        Notion webhooks support events for:
        - page (created, updated, deleted)
        - database (created, updated, deleted)
        - block (created, updated, deleted)
        
        Args:
            event_data: Raw Notion webhook payload
            
        Returns:
            Normalized event
            
        Raises:
            ValueError: If event type is not supported
        """
        event_type = event_data.get("type")
        
        if event_type == "page":
            return await self._normalize_page(event_data)
        elif event_type == "database":
            return await self._normalize_database(event_data)
        elif event_type == "block":
            return await self._normalize_block(event_data)
        else:
            raise ValueError(f"Unsupported Notion event type: {event_type}")
    
    async def _normalize_page(
        self,
        event_data: Dict[str, Any],
    ) -> NormalizedEvent:
        """Normalize a Notion page event.
        
        Args:
            event_data: Raw Notion webhook payload
            
        Returns:
            Normalized page event
        """
        action = event_data.get("action", "unknown")
        page = event_data.get("page", {})
        
        page_id = page.get("id", "")
        workspace = event_data.get("workspace", {})
        workspace_id = workspace.get("id", "")
        
        # Fetch full page content if we have a client
        if self.notion_client:
            full_page = await self.notion_client.get_page(page_id)
            if full_page:
                page = full_page
        
        # Extract page title
        title = self._extract_title(page)
        
        # Extract content (simplified)
        content = f"Notion Page: {title}\n\nAction: {action}"
        
        # Extract entities
        entities = self._extract_entities(page, title)
        
        # Parse timestamp
        timestamp_str = event_data.get("timestamp", "")
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except Exception:
            timestamp = None
        
        return NormalizedEvent(
            event_type=f"page_{action}",
            source=self.integration_name,
            content=content,
            layer="tenant",  # Notion is workspace-level
            tenant_id=workspace_id,
            entities=entities,
            metadata={
                "page_id": page_id,
                "workspace_id": workspace_id,
                "action": action,
                "url": page.get("url", ""),
            },
            timestamp=timestamp,
        )
    
    async def _normalize_database(
        self,
        event_data: Dict[str, Any],
    ) -> NormalizedEvent:
        """Normalize a Notion database event.
        
        Args:
            event_data: Raw Notion webhook payload
            
        Returns:
            Normalized database event
        """
        action = event_data.get("action", "unknown")
        database = event_data.get("database", {})
        
        database_id = database.get("id", "")
        workspace = event_data.get("workspace", {})
        workspace_id = workspace.get("id", "")
        
        # Extract database title
        title = self._extract_title(database)
        
        content = f"Notion Database: {title}\n\nAction: {action}"
        
        entities = [
            ExtractedEntity(
                name=title,
                type="database",
                properties={
                    "platform": "notion",
                    "database_id": database_id,
                },
            )
        ]
        
        timestamp_str = event_data.get("timestamp", "")
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except Exception:
            timestamp = None
        
        return NormalizedEvent(
            event_type=f"database_{action}",
            source=self.integration_name,
            content=content,
            layer="tenant",
            tenant_id=workspace_id,
            entities=entities,
            metadata={
                "database_id": database_id,
                "workspace_id": workspace_id,
                "action": action,
                "url": database.get("url", ""),
            },
            timestamp=timestamp,
        )
    
    async def _normalize_block(
        self,
        event_data: Dict[str, Any],
    ) -> NormalizedEvent:
        """Normalize a Notion block event.
        
        Args:
            event_data: Raw Notion webhook payload
            
        Returns:
            Normalized block event
        """
        action = event_data.get("action", "unknown")
        block = event_data.get("block", {})
        
        block_id = block.get("id", "")
        block_type = block.get("type", "unknown")
        workspace = event_data.get("workspace", {})
        workspace_id = workspace.get("id", "")
        
        # Extract block text
        text = self._extract_block_text(block)
        
        content = f"Notion Block ({block_type}): {text}\n\nAction: {action}"
        
        entities = []
        
        timestamp_str = event_data.get("timestamp", "")
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except Exception:
            timestamp = None
        
        return NormalizedEvent(
            event_type=f"block_{action}",
            source=self.integration_name,
            content=content,
            layer="tenant",
            tenant_id=workspace_id,
            entities=entities,
            metadata={
                "block_id": block_id,
                "block_type": block_type,
                "workspace_id": workspace_id,
                "action": action,
            },
            timestamp=timestamp,
        )
    
    def _extract_title(self, obj: Dict[str, Any]) -> str:
        """Extract title from Notion page or database.
        
        Args:
            obj: Notion page or database object
            
        Returns:
            Title string
        """
        properties = obj.get("properties", {})
        
        # Look for title property
        for prop_name, prop_value in properties.items():
            if prop_value.get("type") == "title":
                title_parts = prop_value.get("title", [])
                if title_parts:
                    return "".join(part.get("plain_text", "") for part in title_parts)
        
        # Fallback to object title
        title_parts = obj.get("title", [])
        if isinstance(title_parts, list):
            return "".join(part.get("plain_text", "") for part in title_parts)
        elif isinstance(title_parts, str):
            return title_parts
        
        return "(Untitled)"
    
    def _extract_block_text(self, block: Dict[str, Any]) -> str:
        """Extract text from Notion block.
        
        Args:
            block: Notion block object
            
        Returns:
            Block text
        """
        block_type = block.get("type", "")
        block_data = block.get(block_type, {})
        
        # Get rich text
        rich_text = block_data.get("rich_text", [])
        if rich_text:
            return "".join(part.get("plain_text", "") for part in rich_text)
        
        # Get text if available
        text = block_data.get("text", "")
        if text:
            return text
        
        return ""
    
    def _extract_entities(
        self,
        page: Dict[str, Any],
        title: str,
    ) -> List[ExtractedEntity]:
        """Extract entities from Notion page.
        
        Args:
            page: Notion page object
            title: Page title
            
        Returns:
            List of extracted entities
        """
        entities = [
            ExtractedEntity(
                name=title,
                type="document",
                properties={
                    "platform": "notion",
                    "page_id": page.get("id", ""),
                },
            )
        ]
        
        # Extract mentions or other entities from properties
        # This is a simplified version - production should parse all properties
        
        return entities
