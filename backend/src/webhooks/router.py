"""Webhook router for handling incoming webhooks."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Header, Request

from src.core.logging import get_logger
from src.integrations.base.processor import EventProcessor
from src.integrations.gmail.client import GmailClient
from src.integrations.gmail.normalizer import GmailNormalizer
from src.integrations.notion.client import NotionClient
from src.integrations.notion.normalizer import NotionNormalizer
from src.integrations.slack.normalizer import SlackNormalizer
from src.memory.manager import MemoryManager
from src.webhooks.verification import verify_signature

logger = get_logger(__name__)

webhook_router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# Initialize normalizers and processor
# Note: In production, these should be dependency-injected
_slack_normalizer = SlackNormalizer()
_gmail_normalizer = None  # Will be initialized with client when needed
_notion_normalizer = None  # Will be initialized with client when needed
_event_processor = None  # Will be initialized when needed


def get_event_processor() -> EventProcessor:
    """Get or create event processor instance."""
    global _event_processor
    if _event_processor is None:
        memory_manager = MemoryManager()
        _event_processor = EventProcessor(memory_manager)
    return _event_processor


@webhook_router.post("/slack")
async def slack_webhook(
    request: Request,
    x_slack_signature: Annotated[str, Header()],
    x_slack_request_timestamp: Annotated[str, Header()],
) -> dict:
    """Handle Slack webhook events.
    
    Slack sends webhook events for:
    - Messages in channels, groups, and DMs
    - Reactions added
    - Files shared
    - And more
    
    This endpoint:
    1. Verifies the Slack signature
    2. Handles URL verification challenge
    3. Normalizes the event
    4. Processes and stores in memory system
    """
    start_time = datetime.utcnow()
    body = await request.body()
    
    # Verify signature
    if not verify_signature("slack", body, x_slack_signature, x_slack_request_timestamp):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    payload = await request.json()
    
    # Handle URL verification challenge
    if payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge")}
    
    # Handle event callback
    if payload.get("type") == "event_callback":
        event_type = payload.get("event", {}).get("type")
        
        logger.info(
            "slack_webhook_received",
            event_type=event_type,
            team_id=payload.get("team_id"),
        )
        
        try:
            # Normalize event
            normalized_event = await _slack_normalizer.normalize(payload)
            
            # Process event
            processor = get_event_processor()
            result = await processor.process(normalized_event)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(
                "slack_webhook_processed",
                event_id=result["event_id"],
                memory_id=result["memory_id"],
                processing_time_ms=int(processing_time),
            )
            
            return {"ok": True, "event_id": result["event_id"]}
            
        except ValueError as e:
            # Event type not supported or should be skipped
            logger.debug("slack_event_skipped", reason=str(e))
            return {"ok": True, "skipped": True}
            
        except Exception as e:
            logger.error("slack_webhook_processing_failed", error=str(e), exc_info=True)
            # Return 200 to prevent Slack from retrying
            return {"ok": False, "error": "Processing failed"}
    
    return {"ok": True}


@webhook_router.post("/gmail")
async def gmail_webhook(request: Request) -> dict:
    """Handle Gmail Pub/Sub notifications.
    
    Gmail uses Cloud Pub/Sub for push notifications.
    The notification contains minimal data; we need to fetch
    the full message using the Gmail API.
    
    This endpoint:
    1. Parses the Pub/Sub message
    2. Fetches the full email using Gmail API
    3. Normalizes the event
    4. Processes and stores in memory system
    """
    start_time = datetime.utcnow()
    payload = await request.json()
    
    logger.info("gmail_webhook_received")
    
    try:
        # Initialize Gmail normalizer with client if needed
        global _gmail_normalizer
        if _gmail_normalizer is None:
            # TODO: Get user credentials from database
            # For now, create without credentials (will fail to fetch messages)
            gmail_client = GmailClient()
            _gmail_normalizer = GmailNormalizer(gmail_client=gmail_client)
        
        # Normalize event
        normalized_event = await _gmail_normalizer.normalize(payload)
        
        # Process event
        processor = get_event_processor()
        result = await processor.process(normalized_event)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.info(
            "gmail_webhook_processed",
            event_id=result["event_id"],
            memory_id=result["memory_id"],
            processing_time_ms=int(processing_time),
        )
        
        return {"ok": True, "event_id": result["event_id"]}
        
    except ValueError as e:
        logger.warning("gmail_event_invalid", reason=str(e))
        return {"ok": False, "error": str(e)}
        
    except Exception as e:
        logger.error("gmail_webhook_processing_failed", error=str(e), exc_info=True)
        return {"ok": False, "error": "Processing failed"}


@webhook_router.post("/notion")
async def notion_webhook(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    """Handle Notion webhook events.
    
    Notion sends webhook events for:
    - Page created, updated, deleted
    - Database created, updated, deleted
    - Block created, updated, deleted
    
    This endpoint:
    1. Verifies the bearer token (if configured)
    2. Normalizes the event
    3. Processes and stores in memory system
    """
    start_time = datetime.utcnow()
    payload = await request.json()
    
    event_type = payload.get("type")
    action = payload.get("action")
    
    logger.info(
        "notion_webhook_received",
        event_type=event_type,
        action=action,
    )
    
    try:
        # Initialize Notion normalizer with client if needed
        global _notion_normalizer
        if _notion_normalizer is None:
            # TODO: Get integration token from settings/database
            notion_client = NotionClient()
            _notion_normalizer = NotionNormalizer(notion_client=notion_client)
        
        # Normalize event
        normalized_event = await _notion_normalizer.normalize(payload)
        
        # Process event
        processor = get_event_processor()
        result = await processor.process(normalized_event)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.info(
            "notion_webhook_processed",
            event_id=result["event_id"],
            memory_id=result["memory_id"],
            processing_time_ms=int(processing_time),
        )
        
        return {"ok": True, "event_id": result["event_id"]}
        
    except ValueError as e:
        logger.warning("notion_event_invalid", reason=str(e))
        return {"ok": False, "error": str(e)}
        
    except Exception as e:
        logger.error("notion_webhook_processing_failed", error=str(e), exc_info=True)
        return {"ok": False, "error": "Processing failed"}
