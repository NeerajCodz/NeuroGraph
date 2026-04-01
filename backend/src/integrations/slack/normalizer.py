"""Slack event normalizer."""

from typing import Any, Dict, List, Optional

from src.core.logging import get_logger
from src.integrations.base.normalizer import (
    BaseNormalizer,
    ExtractedEntity,
    NormalizedEvent,
)

logger = get_logger(__name__)


class SlackNormalizer(BaseNormalizer):
    """Normalize Slack webhook events to standard format."""
    
    def __init__(self):
        super().__init__("slack")
    
    async def normalize(self, event_data: Dict[str, Any]) -> NormalizedEvent:
        """Normalize Slack event to standard format.
        
        Supported Slack events:
        - message (in channels, groups, DMs)
        - reaction_added
        - file_shared
        - channel_created
        
        Args:
            event_data: Raw Slack webhook payload
            
        Returns:
            Normalized event
            
        Raises:
            ValueError: If event type is not supported
        """
        event = event_data.get("event", {})
        event_type = event.get("type")
        
        if event_type == "message":
            # Filter out bot messages and message changes
            if event.get("subtype") in ["bot_message", "message_changed", "message_deleted"]:
                raise ValueError(f"Skipping Slack subtype: {event.get('subtype')}")
            return await self._normalize_message(event, event_data)
        elif event_type == "reaction_added":
            return await self._normalize_reaction(event, event_data)
        elif event_type == "file_shared":
            return await self._normalize_file(event, event_data)
        else:
            raise ValueError(f"Unsupported Slack event type: {event_type}")
    
    async def _normalize_message(
        self,
        event: Dict[str, Any],
        full_payload: Dict[str, Any]
    ) -> NormalizedEvent:
        """Normalize a Slack message event.
        
        Args:
            event: The event object from payload
            full_payload: Full Slack webhook payload
            
        Returns:
            Normalized message event
        """
        text = event.get("text", "")
        user = event.get("user", "")
        channel = event.get("channel", "")
        ts = event.get("ts", "")
        thread_ts = event.get("thread_ts")
        
        # Extract entities from message
        entities = self._extract_entities_from_text(text, channel, user)
        
        # Resolve user ID
        external_user_id = user
        user_id = await self.resolve_user_id(external_user_id)
        
        # Determine team ID for tenant context
        team_id = full_payload.get("team_id", "")
        
        return NormalizedEvent(
            event_type="message",
            source=self.integration_name,
            content=text,
            layer="tenant",  # Slack messages are team/workspace level
            user_external_id=external_user_id,
            user_id=user_id,
            tenant_id=team_id,  # Use team_id as tenant_id
            entities=entities,
            metadata={
                "channel": channel,
                "user": user,
                "timestamp": ts,
                "thread_ts": thread_ts,
                "team_id": team_id,
                "is_thread_reply": bool(thread_ts and thread_ts != ts),
            },
        )
    
    async def _normalize_reaction(
        self,
        event: Dict[str, Any],
        full_payload: Dict[str, Any]
    ) -> NormalizedEvent:
        """Normalize a Slack reaction event.
        
        Args:
            event: The event object from payload
            full_payload: Full Slack webhook payload
            
        Returns:
            Normalized reaction event
        """
        reaction = event.get("reaction", "")
        user = event.get("user", "")
        item = event.get("item", {})
        channel = item.get("channel", "")
        ts = item.get("ts", "")
        
        content = f"Reacted with :{reaction}: to message"
        
        entities = [
            ExtractedEntity(
                name=user,
                type="person",
                properties={"slack_id": user},
            ),
            ExtractedEntity(
                name=channel,
                type="channel",
                properties={"platform": "slack"},
            ),
        ]
        
        external_user_id = user
        user_id = await self.resolve_user_id(external_user_id)
        team_id = full_payload.get("team_id", "")
        
        return NormalizedEvent(
            event_type="reaction",
            source=self.integration_name,
            content=content,
            layer="tenant",
            user_external_id=external_user_id,
            user_id=user_id,
            tenant_id=team_id,
            entities=entities,
            metadata={
                "reaction": reaction,
                "channel": channel,
                "user": user,
                "message_ts": ts,
                "team_id": team_id,
            },
        )
    
    async def _normalize_file(
        self,
        event: Dict[str, Any],
        full_payload: Dict[str, Any]
    ) -> NormalizedEvent:
        """Normalize a Slack file shared event.
        
        Args:
            event: The event object from payload
            full_payload: Full Slack webhook payload
            
        Returns:
            Normalized file event
        """
        file_id = event.get("file_id", "")
        user_id_slack = event.get("user_id", "")
        
        content = f"Shared a file: {file_id}"
        
        entities = [
            ExtractedEntity(
                name=user_id_slack,
                type="person",
                properties={"slack_id": user_id_slack},
            ),
        ]
        
        user_id = await self.resolve_user_id(user_id_slack)
        team_id = full_payload.get("team_id", "")
        
        return NormalizedEvent(
            event_type="file_shared",
            source=self.integration_name,
            content=content,
            layer="tenant",
            user_external_id=user_id_slack,
            user_id=user_id,
            tenant_id=team_id,
            entities=entities,
            metadata={
                "file_id": file_id,
                "user": user_id_slack,
                "team_id": team_id,
            },
        )
    
    def _extract_entities_from_text(
        self,
        text: str,
        channel: str,
        user: str,
    ) -> List[ExtractedEntity]:
        """Extract entities from Slack message text.
        
        Extracts:
        - User mentions (@user)
        - Channel mentions (#channel)
        - The sender
        - The channel
        
        Args:
            text: Message text
            channel: Channel ID
            user: User ID
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        # Add sender as entity
        entities.append(
            ExtractedEntity(
                name=user,
                type="person",
                properties={"slack_id": user},
            )
        )
        
        # Add channel as entity
        entities.append(
            ExtractedEntity(
                name=channel,
                type="channel",
                properties={"platform": "slack"},
            )
        )
        
        # Extract user mentions (<@U123ABC>)
        import re
        user_mentions = re.findall(r'<@([A-Z0-9]+)>', text)
        for mentioned_user in user_mentions:
            entities.append(
                ExtractedEntity(
                    name=mentioned_user,
                    type="person",
                    properties={"slack_id": mentioned_user, "mentioned": True},
                )
            )
        
        # Extract channel mentions (<#C123ABC|channel-name>)
        channel_mentions = re.findall(r'<#([A-Z0-9]+)(?:\|([^>]+))?>', text)
        for channel_id, channel_name in channel_mentions:
            entities.append(
                ExtractedEntity(
                    name=channel_name or channel_id,
                    type="channel",
                    properties={
                        "platform": "slack",
                        "channel_id": channel_id,
                        "mentioned": True,
                    },
                )
            )
        
        return entities
