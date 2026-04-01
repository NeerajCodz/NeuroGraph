"""Gmail API client for fetching messages."""

from typing import Any, Dict, Optional

from src.core.logging import get_logger

logger = get_logger(__name__)


class GmailClient:
    """Client for interacting with Gmail API.
    
    Used to fetch full email messages from Gmail push notifications.
    Requires OAuth2 credentials for the user's Gmail account.
    
    Note: This is a simplified client. In production, you should:
    1. Implement proper OAuth2 flow and token storage
    2. Use the official Google API Python client
    3. Handle token refresh
    4. Support batch requests
    """
    
    def __init__(self, credentials: Optional[Any] = None):
        """Initialize Gmail client.
        
        Args:
            credentials: Google OAuth2 credentials object
        """
        self.credentials = credentials
        self.service = None
        
        if credentials:
            try:
                from googleapiclient.discovery import build
                self.service = build('gmail', 'v1', credentials=credentials)
            except ImportError:
                logger.warning(
                    "google_api_client_not_installed",
                    hint="Install with: pip install google-api-python-client",
                )
            except Exception as e:
                logger.error("gmail_client_init_failed", error=str(e))
    
    async def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific email message by ID.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            Message data dict or None if error
        """
        if not self.service:
            logger.warning("gmail_service_not_initialized")
            return None
        
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full',
            ).execute()
            
            return message
        except Exception as e:
            logger.error("gmail_get_message_failed", message_id=message_id, error=str(e))
            return None
    
    async def get_latest_message(self) -> Optional[Dict[str, Any]]:
        """Get the most recent email message.
        
        Returns:
            Message data dict or None if error
        """
        if not self.service:
            logger.warning("gmail_service_not_initialized")
            return None
        
        try:
            # List messages (returns IDs only)
            results = self.service.users().messages().list(
                userId='me',
                maxResults=1,
            ).execute()
            
            messages = results.get('messages', [])
            if not messages:
                logger.info("no_gmail_messages_found")
                return None
            
            # Fetch full message
            message_id = messages[0]['id']
            return await self.get_message(message_id)
            
        except Exception as e:
            logger.error("gmail_get_latest_message_failed", error=str(e))
            return None
    
    async def get_messages_since_history(
        self,
        history_id: int,
    ) -> list:
        """Get messages that arrived since a specific history ID.
        
        This is the recommended way to process Gmail push notifications.
        
        Args:
            history_id: Gmail history ID from push notification
            
        Returns:
            List of message data dicts
        """
        if not self.service:
            logger.warning("gmail_service_not_initialized")
            return []
        
        try:
            # Get history
            history = self.service.users().history().list(
                userId='me',
                startHistoryId=history_id,
                historyTypes=['messageAdded'],
            ).execute()
            
            changes = history.get('history', [])
            messages = []
            
            for change in changes:
                messages_added = change.get('messagesAdded', [])
                for message_added in messages_added:
                    message_id = message_added['message']['id']
                    full_message = await self.get_message(message_id)
                    if full_message:
                        messages.append(full_message)
            
            return messages
            
        except Exception as e:
            logger.error("gmail_get_history_failed", history_id=history_id, error=str(e))
            return []
    
    async def watch_mailbox(
        self,
        topic_name: str,
        label_ids: Optional[list] = None,
    ) -> Optional[Dict[str, Any]]:
        """Set up push notifications for the mailbox.
        
        Args:
            topic_name: Pub/Sub topic name (projects/{project}/topics/{topic})
            label_ids: Optional list of label IDs to watch (default: all)
            
        Returns:
            Watch response or None if error
        """
        if not self.service:
            logger.warning("gmail_service_not_initialized")
            return None
        
        try:
            request = {
                'topicName': topic_name,
            }
            
            if label_ids:
                request['labelIds'] = label_ids
            
            response = self.service.users().watch(
                userId='me',
                body=request,
            ).execute()
            
            logger.info(
                "gmail_watch_setup",
                expiration=response.get('expiration'),
                history_id=response.get('historyId'),
            )
            
            return response
            
        except Exception as e:
            logger.error("gmail_watch_failed", error=str(e))
            return None
    
    async def stop_watch(self) -> bool:
        """Stop push notifications for the mailbox.
        
        Returns:
            True if successful
        """
        if not self.service:
            logger.warning("gmail_service_not_initialized")
            return False
        
        try:
            self.service.users().stop(userId='me').execute()
            logger.info("gmail_watch_stopped")
            return True
            
        except Exception as e:
            logger.error("gmail_stop_watch_failed", error=str(e))
            return False
