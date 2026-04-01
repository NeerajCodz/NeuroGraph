"""Slack API client for fetching additional data."""

from typing import Any, Dict, Optional

import httpx

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class SlackClient:
    """Client for interacting with Slack API.
    
    Used to fetch additional data not provided in webhook events,
    such as user profiles, channel information, message history, etc.
    """
    
    BASE_URL = "https://slack.com/api"
    
    def __init__(self, bot_token: Optional[str] = None):
        """Initialize Slack client.
        
        Args:
            bot_token: Slack bot token (xoxb-...). If None, reads from settings.
        """
        settings = get_settings()
        self.bot_token = bot_token or (
            settings.slack_bot_token.get_secret_value()
            if settings.slack_bot_token
            else None
        )
        
        if not self.bot_token:
            logger.warning("slack_bot_token_not_configured")
    
    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information from Slack.
        
        Args:
            user_id: Slack user ID
            
        Returns:
            User info dict or None if error
        """
        if not self.bot_token:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/users.info",
                    headers={"Authorization": f"Bearer {self.bot_token}"},
                    params={"user": user_id},
                )
                data = response.json()
                
                if data.get("ok"):
                    return data.get("user")
                else:
                    logger.warning(
                        "slack_api_error",
                        method="users.info",
                        error=data.get("error"),
                    )
                    return None
        except Exception as e:
            logger.error("slack_api_request_failed", error=str(e))
            return None
    
    async def get_channel_info(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Get channel information from Slack.
        
        Args:
            channel_id: Slack channel ID
            
        Returns:
            Channel info dict or None if error
        """
        if not self.bot_token:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/conversations.info",
                    headers={"Authorization": f"Bearer {self.bot_token}"},
                    params={"channel": channel_id},
                )
                data = response.json()
                
                if data.get("ok"):
                    return data.get("channel")
                else:
                    logger.warning(
                        "slack_api_error",
                        method="conversations.info",
                        error=data.get("error"),
                    )
                    return None
        except Exception as e:
            logger.error("slack_api_request_failed", error=str(e))
            return None
    
    async def get_message(
        self,
        channel_id: str,
        timestamp: str,
    ) -> Optional[Dict[str, Any]]:
        """Get a specific message from Slack.
        
        Args:
            channel_id: Slack channel ID
            timestamp: Message timestamp
            
        Returns:
            Message dict or None if error
        """
        if not self.bot_token:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/conversations.history",
                    headers={"Authorization": f"Bearer {self.bot_token}"},
                    params={
                        "channel": channel_id,
                        "latest": timestamp,
                        "limit": 1,
                        "inclusive": True,
                    },
                )
                data = response.json()
                
                if data.get("ok"):
                    messages = data.get("messages", [])
                    return messages[0] if messages else None
                else:
                    logger.warning(
                        "slack_api_error",
                        method="conversations.history",
                        error=data.get("error"),
                    )
                    return None
        except Exception as e:
            logger.error("slack_api_request_failed", error=str(e))
            return None
    
    async def get_thread_replies(
        self,
        channel_id: str,
        thread_ts: str,
    ) -> list:
        """Get all replies in a thread.
        
        Args:
            channel_id: Slack channel ID
            thread_ts: Thread parent timestamp
            
        Returns:
            List of message dicts
        """
        if not self.bot_token:
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/conversations.replies",
                    headers={"Authorization": f"Bearer {self.bot_token}"},
                    params={"channel": channel_id, "ts": thread_ts},
                )
                data = response.json()
                
                if data.get("ok"):
                    return data.get("messages", [])
                else:
                    logger.warning(
                        "slack_api_error",
                        method="conversations.replies",
                        error=data.get("error"),
                    )
                    return []
        except Exception as e:
            logger.error("slack_api_request_failed", error=str(e))
            return []
