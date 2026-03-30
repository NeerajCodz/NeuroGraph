"""Webhook router for handling incoming webhooks."""

from fastapi import APIRouter, Request, HTTPException, Depends, Header
from typing import Annotated

from src.core.logging import get_logger
from src.webhooks.verification import verify_signature

logger = get_logger(__name__)

webhook_router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@webhook_router.post("/slack")
async def slack_webhook(
    request: Request,
    x_slack_signature: Annotated[str, Header()],
    x_slack_request_timestamp: Annotated[str, Header()],
) -> dict:
    """Handle Slack webhook events."""
    body = await request.body()
    
    # Verify signature
    if not verify_signature("slack", body, x_slack_signature, x_slack_request_timestamp):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    payload = await request.json()
    
    # Handle URL verification challenge
    if payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge")}
    
    logger.info("slack_webhook_received", event_type=payload.get("type"))
    
    # TODO: Process Slack event
    
    return {"ok": True}


@webhook_router.post("/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: Annotated[str | None, Header()] = None,
) -> dict:
    """Handle GitHub webhook events."""
    body = await request.body()
    
    # Verify signature
    if x_hub_signature_256 and not verify_signature("github", body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    payload = await request.json()
    event_type = request.headers.get("X-GitHub-Event", "unknown")
    
    logger.info("github_webhook_received", event_type=event_type)
    
    # TODO: Process GitHub event
    
    return {"ok": True}


@webhook_router.post("/gmail")
async def gmail_webhook(request: Request) -> dict:
    """Handle Gmail Pub/Sub notifications."""
    payload = await request.json()
    
    logger.info("gmail_webhook_received")
    
    # TODO: Process Gmail notification
    
    return {"ok": True}
