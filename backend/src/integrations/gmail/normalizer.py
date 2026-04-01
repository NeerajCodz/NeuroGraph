"""Gmail event normalizer."""

import base64
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional

from src.core.logging import get_logger
from src.integrations.base.normalizer import (
    BaseNormalizer,
    ExtractedEntity,
    NormalizedEvent,
)

logger = get_logger(__name__)


class GmailNormalizer(BaseNormalizer):
    """Normalize Gmail push notification events to standard format.
    
    Gmail uses Pub/Sub push notifications, which only contain minimal data.
    The full message must be fetched using the Gmail API.
    """
    
    def __init__(self, gmail_client=None):
        super().__init__("gmail")
        self.gmail_client = gmail_client
    
    async def normalize(self, event_data: Dict[str, Any]) -> NormalizedEvent:
        """Normalize Gmail push notification to standard format.
        
        Gmail push notifications contain:
        - message.data: base64-encoded message with historyId and emailAddress
        - message.messageId: Pub/Sub message ID
        - message.publishTime: When notification was published
        
        We need to:
        1. Decode the message data
        2. Fetch the full email using Gmail API
        3. Extract content and entities
        
        Args:
            event_data: Raw Gmail push notification payload
            
        Returns:
            Normalized event
            
        Raises:
            ValueError: If notification is invalid or message cannot be fetched
        """
        # Extract data from push notification
        message = event_data.get("message", {})
        data_b64 = message.get("data", "")
        
        if not data_b64:
            raise ValueError("Gmail push notification missing data field")
        
        # Decode base64 data
        try:
            import json
            data_decoded = base64.b64decode(data_b64).decode("utf-8")
            data = json.loads(data_decoded)
        except Exception as e:
            raise ValueError(f"Failed to decode Gmail push notification data: {e}")
        
        # Extract email address and history ID
        email_address = data.get("emailAddress", "")
        history_id = data.get("historyId")
        
        logger.debug(
            "gmail_push_notification",
            email_address=email_address,
            history_id=history_id,
        )
        
        # Fetch full message using Gmail API
        # Note: Gmail push notifications don't include the message ID directly
        # We need to fetch recent history to find new messages
        if not self.gmail_client:
            raise ValueError("Gmail client not configured")
        
        # For simplicity, we'll fetch the latest message
        # In production, you should use the history API to get only new messages
        message_data = await self.gmail_client.get_latest_message()
        
        if not message_data:
            raise ValueError("Failed to fetch Gmail message")
        
        return await self._normalize_message(message_data, email_address)
    
    async def _normalize_message(
        self,
        message_data: Dict[str, Any],
        email_address: str,
    ) -> NormalizedEvent:
        """Normalize a Gmail message to standard format.
        
        Args:
            message_data: Full Gmail message data from API
            email_address: User's email address
            
        Returns:
            Normalized message event
        """
        # Extract message fields
        message_id = message_data.get("id", "")
        thread_id = message_data.get("threadId", "")
        labels = message_data.get("labelIds", [])
        
        # Parse headers
        headers = {
            h["name"]: h["value"]
            for h in message_data.get("payload", {}).get("headers", [])
        }
        
        subject = headers.get("Subject", "(No subject)")
        from_email = headers.get("From", "")
        to_email = headers.get("To", "")
        date_str = headers.get("Date", "")
        
        # Parse date
        try:
            timestamp = parsedate_to_datetime(date_str) if date_str else None
        except Exception:
            timestamp = None
        
        # Extract email body
        body = self._extract_body(message_data.get("payload", {}))
        
        # Create content
        content = f"Subject: {subject}\n\nFrom: {from_email}\nTo: {to_email}\n\n{body}"
        
        # Extract entities
        entities = self._extract_entities(from_email, to_email, subject)
        
        # Resolve user ID
        user_id = await self.resolve_user_id(email_address)
        
        return NormalizedEvent(
            event_type="email",
            source=self.integration_name,
            content=content,
            layer="personal",  # Email is personal
            user_external_id=email_address,
            user_id=user_id,
            entities=entities,
            metadata={
                "message_id": message_id,
                "thread_id": thread_id,
                "from": from_email,
                "to": to_email,
                "subject": subject,
                "labels": labels,
                "date": date_str,
            },
            timestamp=timestamp,
        )
    
    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Extract email body from Gmail message payload.
        
        Gmail message payloads can be nested. We need to traverse
        the structure to find the text/plain or text/html parts.
        
        Args:
            payload: Gmail message payload
            
        Returns:
            Email body text
        """
        # Check for simple single-part message
        if "body" in payload and payload["body"].get("data"):
            try:
                return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
            except Exception:
                return ""
        
        # Check for multipart message
        parts = payload.get("parts", [])
        for part in parts:
            mime_type = part.get("mimeType", "")
            
            # Prefer text/plain
            if mime_type == "text/plain":
                try:
                    data = part.get("body", {}).get("data", "")
                    if data:
                        return base64.urlsafe_b64decode(data).decode("utf-8")
                except Exception:
                    continue
            
            # Recurse for nested parts
            if "parts" in part:
                body = self._extract_body(part)
                if body:
                    return body
        
        # Fallback to HTML if no plain text
        for part in parts:
            if part.get("mimeType") == "text/html":
                try:
                    data = part.get("body", {}).get("data", "")
                    if data:
                        # Strip HTML tags (simple approach)
                        import re
                        html = base64.urlsafe_b64decode(data).decode("utf-8")
                        text = re.sub(r'<[^>]+>', '', html)
                        return text
                except Exception:
                    continue
        
        return ""
    
    def _extract_entities(
        self,
        from_email: str,
        to_email: str,
        subject: str,
    ) -> List[ExtractedEntity]:
        """Extract entities from email.
        
        Args:
            from_email: Sender email
            to_email: Recipient email
            subject: Email subject
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        # Extract sender
        if from_email:
            # Parse "Name <email@example.com>" format
            import re
            match = re.match(r'(.+?)\s*<(.+?)>', from_email)
            if match:
                name, email = match.groups()
                entities.append(
                    ExtractedEntity(
                        name=name.strip(),
                        type="person",
                        properties={"email": email.strip(), "role": "sender"},
                    )
                )
            else:
                entities.append(
                    ExtractedEntity(
                        name=from_email,
                        type="person",
                        properties={"email": from_email, "role": "sender"},
                    )
                )
        
        # Extract recipient
        if to_email:
            # Could be multiple recipients
            recipients = [r.strip() for r in to_email.split(",")]
            for recipient in recipients:
                match = re.match(r'(.+?)\s*<(.+?)>', recipient)
                if match:
                    name, email = match.groups()
                    entities.append(
                        ExtractedEntity(
                            name=name.strip(),
                            type="person",
                            properties={"email": email.strip(), "role": "recipient"},
                        )
                    )
                else:
                    entities.append(
                        ExtractedEntity(
                            name=recipient,
                            type="person",
                            properties={"email": recipient, "role": "recipient"},
                        )
                    )
        
        return entities
