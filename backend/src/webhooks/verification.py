"""Webhook signature verification."""

import hashlib
import hmac
import time

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)


def verify_signature(
    provider: str,
    body: bytes,
    signature: str,
    timestamp: str | None = None,
) -> bool:
    """Verify webhook signature based on provider.
    
    Args:
        provider: Webhook provider (slack, github, etc.)
        body: Raw request body
        signature: Signature header value
        timestamp: Timestamp header value (for Slack)
        
    Returns:
        True if signature is valid
    """
    settings = get_settings()
    
    if provider == "slack":
        return _verify_slack_signature(body, signature, timestamp, settings)
    elif provider == "github":
        return _verify_github_signature(body, signature, settings)
    else:
        logger.warning("unknown_webhook_provider", provider=provider)
        return False


def _verify_slack_signature(
    body: bytes,
    signature: str,
    timestamp: str | None,
    settings,
) -> bool:
    """Verify Slack webhook signature."""
    if not timestamp:
        return False
    
    secret = settings.slack_signing_secret
    if not secret:
        logger.warning("slack_signing_secret_not_configured")
        return True  # Allow in dev if not configured
    
    # Check timestamp is recent (within 5 minutes)
    try:
        ts = int(timestamp)
        if abs(time.time() - ts) > 60 * 5:
            return False
    except ValueError:
        return False
    
    # Compute expected signature
    sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
    expected = "v0=" + hmac.new(
        secret.get_secret_value().encode(),
        sig_basestring.encode(),
        hashlib.sha256,
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)


def _verify_github_signature(
    body: bytes,
    signature: str,
    settings,
) -> bool:
    """Verify GitHub webhook signature."""
    secret = settings.github_webhook_secret
    if not secret:
        logger.warning("github_webhook_secret_not_configured")
        return True  # Allow in dev if not configured
    
    # Remove "sha256=" prefix
    if signature.startswith("sha256="):
        signature = signature[7:]
    
    expected = hmac.new(
        secret.get_secret_value().encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)
