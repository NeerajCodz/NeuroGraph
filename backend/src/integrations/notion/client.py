"""Notion API client for fetching pages and blocks."""

from typing import Any, Dict, Optional

import httpx

from src.core.logging import get_logger

logger = get_logger(__name__)


class NotionClient:
    """Client for interacting with Notion API.
    
    Used to fetch full page content and blocks from Notion webhooks.
    Requires a Notion integration token.
    """
    
    BASE_URL = "https://api.notion.com/v1"
    NOTION_VERSION = "2022-06-28"
    
    def __init__(self, token: Optional[str] = None):
        """Initialize Notion client.
        
        Args:
            token: Notion integration token
        """
        self.token = token
        
        if not self.token:
            logger.warning("notion_token_not_configured")
    
    async def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get a Notion page by ID.
        
        Args:
            page_id: Notion page ID
            
        Returns:
            Page data dict or None if error
        """
        if not self.token:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/pages/{page_id}",
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Notion-Version": self.NOTION_VERSION,
                    },
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(
                        "notion_api_error",
                        method="get_page",
                        status_code=response.status_code,
                        error=response.text,
                    )
                    return None
        except Exception as e:
            logger.error("notion_api_request_failed", error=str(e))
            return None
    
    async def get_database(self, database_id: str) -> Optional[Dict[str, Any]]:
        """Get a Notion database by ID.
        
        Args:
            database_id: Notion database ID
            
        Returns:
            Database data dict or None if error
        """
        if not self.token:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/databases/{database_id}",
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Notion-Version": self.NOTION_VERSION,
                    },
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(
                        "notion_api_error",
                        method="get_database",
                        status_code=response.status_code,
                        error=response.text,
                    )
                    return None
        except Exception as e:
            logger.error("notion_api_request_failed", error=str(e))
            return None
    
    async def get_block(self, block_id: str) -> Optional[Dict[str, Any]]:
        """Get a Notion block by ID.
        
        Args:
            block_id: Notion block ID
            
        Returns:
            Block data dict or None if error
        """
        if not self.token:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/blocks/{block_id}",
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Notion-Version": self.NOTION_VERSION,
                    },
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(
                        "notion_api_error",
                        method="get_block",
                        status_code=response.status_code,
                        error=response.text,
                    )
                    return None
        except Exception as e:
            logger.error("notion_api_request_failed", error=str(e))
            return None
    
    async def get_block_children(
        self,
        block_id: str,
        page_size: int = 100,
    ) -> list:
        """Get children blocks of a block.
        
        Args:
            block_id: Parent block ID
            page_size: Number of blocks to fetch per page
            
        Returns:
            List of child blocks
        """
        if not self.token:
            return []
        
        try:
            blocks = []
            start_cursor = None
            has_more = True
            
            async with httpx.AsyncClient() as client:
                while has_more:
                    params = {"page_size": page_size}
                    if start_cursor:
                        params["start_cursor"] = start_cursor
                    
                    response = await client.get(
                        f"{self.BASE_URL}/blocks/{block_id}/children",
                        headers={
                            "Authorization": f"Bearer {self.token}",
                            "Notion-Version": self.NOTION_VERSION,
                        },
                        params=params,
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        blocks.extend(data.get("results", []))
                        has_more = data.get("has_more", False)
                        start_cursor = data.get("next_cursor")
                    else:
                        logger.warning(
                            "notion_api_error",
                            method="get_block_children",
                            status_code=response.status_code,
                        )
                        break
            
            return blocks
            
        except Exception as e:
            logger.error("notion_api_request_failed", error=str(e))
            return []
    
    async def query_database(
        self,
        database_id: str,
        filter_params: Optional[Dict[str, Any]] = None,
        page_size: int = 100,
    ) -> list:
        """Query a Notion database.
        
        Args:
            database_id: Database ID
            filter_params: Optional filter parameters
            page_size: Number of results per page
            
        Returns:
            List of database entries
        """
        if not self.token:
            return []
        
        try:
            results = []
            start_cursor = None
            has_more = True
            
            async with httpx.AsyncClient() as client:
                while has_more:
                    body = {"page_size": page_size}
                    if start_cursor:
                        body["start_cursor"] = start_cursor
                    if filter_params:
                        body["filter"] = filter_params
                    
                    response = await client.post(
                        f"{self.BASE_URL}/databases/{database_id}/query",
                        headers={
                            "Authorization": f"Bearer {self.token}",
                            "Notion-Version": self.NOTION_VERSION,
                            "Content-Type": "application/json",
                        },
                        json=body,
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        results.extend(data.get("results", []))
                        has_more = data.get("has_more", False)
                        start_cursor = data.get("next_cursor")
                    else:
                        logger.warning(
                            "notion_api_error",
                            method="query_database",
                            status_code=response.status_code,
                        )
                        break
            
            return results
            
        except Exception as e:
            logger.error("notion_api_request_failed", error=str(e))
            return []
