"""E2E tests for webhook integrations."""

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime
from uuid import uuid4

import pytest

from src.core.config import get_settings
from src.integrations.slack.normalizer import SlackNormalizer
from src.integrations.gmail.normalizer import GmailNormalizer
from src.integrations.notion.normalizer import NotionNormalizer


class TestSlackNormalizer:
    """Test Slack event normalization."""
    
    @pytest.mark.asyncio
    async def test_normalize_message(self):
        """Test normalizing a Slack message event."""
        normalizer = SlackNormalizer()
        
        event_data = {
            "type": "event_callback",
            "team_id": "T123ABC",
            "event": {
                "type": "message",
                "user": "U123ABC",
                "text": "Hello from Slack webhook test",
                "channel": "C123ABC",
                "ts": "1234567890.123456",
            },
        }
        
        result = await normalizer.normalize(event_data)
        
        assert result.event_type == "message"
        assert result.source == "slack"
        assert result.content == "Hello from Slack webhook test"
        assert result.layer == "tenant"
        assert result.tenant_id == "T123ABC"
        assert len(result.entities) >= 2  # At least user and channel
    
    @pytest.mark.asyncio
    async def test_normalize_reaction(self):
        """Test normalizing a Slack reaction event."""
        normalizer = SlackNormalizer()
        
        event_data = {
            "type": "event_callback",
            "team_id": "T123ABC",
            "event": {
                "type": "reaction_added",
                "user": "U123ABC",
                "reaction": "thumbsup",
                "item": {
                    "type": "message",
                    "channel": "C123ABC",
                    "ts": "1234567890.123456",
                },
            },
        }
        
        result = await normalizer.normalize(event_data)
        
        assert result.event_type == "reaction"
        assert result.source == "slack"
        assert "thumbsup" in result.content
        assert result.layer == "tenant"
    
    @pytest.mark.asyncio
    async def test_skip_bot_message(self):
        """Test that bot messages are skipped."""
        normalizer = SlackNormalizer()
        
        event_data = {
            "type": "event_callback",
            "team_id": "T123ABC",
            "event": {
                "type": "message",
                "subtype": "bot_message",
                "text": "Bot message",
                "channel": "C123ABC",
                "ts": "1234567890.123456",
            },
        }
        
        with pytest.raises(ValueError) as exc_info:
            await normalizer.normalize(event_data)
        
        assert "Skipping" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_extract_entities_from_mentions(self):
        """Test entity extraction from user and channel mentions."""
        normalizer = SlackNormalizer()
        
        event_data = {
            "type": "event_callback",
            "team_id": "T123ABC",
            "event": {
                "type": "message",
                "user": "U123ABC",
                "text": "Hey <@U456DEF>, let's discuss in <#C789GHI|engineering>",
                "channel": "C123ABC",
                "ts": "1234567890.123456",
            },
        }
        
        result = await normalizer.normalize(event_data)
        
        # Should extract: sender, channel, mentioned user, mentioned channel
        assert len(result.entities) >= 4
        
        # Check mentioned user exists
        mentioned_users = [e for e in result.entities if e.properties.get("mentioned")]
        assert len(mentioned_users) >= 1


class TestGmailNormalizer:
    """Test Gmail event normalization."""
    
    @pytest.mark.asyncio
    async def test_decode_push_notification(self):
        """Test decoding Gmail push notification."""
        normalizer = GmailNormalizer(gmail_client=None)
        
        notification_data = {
            "emailAddress": "test@example.com",
            "historyId": 12345,
        }
        
        data_b64 = base64.b64encode(
            json.dumps(notification_data).encode()
        ).decode()
        
        event_data = {
            "message": {
                "data": data_b64,
                "messageId": str(uuid4()),
                "publishTime": datetime.utcnow().isoformat() + "Z",
            },
        }
        
        # This will fail without Gmail client, but should decode the data first
        with pytest.raises(ValueError) as exc_info:
            await normalizer.normalize(event_data)
        
        # Should fail on client not configured, not on decoding
        assert "client not configured" in str(exc_info.value)


class TestNotionNormalizer:
    """Test Notion event normalization."""
    
    @pytest.mark.asyncio
    async def test_normalize_page_created(self):
        """Test normalizing a Notion page created event."""
        normalizer = NotionNormalizer(notion_client=None)
        
        event_data = {
            "type": "page",
            "action": "created",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "page": {
                "id": "page_123",
                "properties": {
                    "title": {
                        "type": "title",
                        "title": [
                            {
                                "plain_text": "Test Page",
                            }
                        ],
                    }
                },
                "url": "https://notion.so/page_123",
            },
            "workspace": {
                "id": "workspace_123",
            },
        }
        
        result = await normalizer.normalize(event_data)
        
        assert result.event_type == "page_created"
        assert result.source == "notion"
        assert "Test Page" in result.content
        assert result.layer == "tenant"
        assert result.tenant_id == "workspace_123"
    
    @pytest.mark.asyncio
    async def test_normalize_database_updated(self):
        """Test normalizing a Notion database updated event."""
        normalizer = NotionNormalizer(notion_client=None)
        
        event_data = {
            "type": "database",
            "action": "updated",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "database": {
                "id": "database_123",
                "title": [
                    {
                        "plain_text": "Test Database",
                    }
                ],
                "url": "https://notion.so/database_123",
            },
            "workspace": {
                "id": "workspace_123",
            },
        }
        
        result = await normalizer.normalize(event_data)
        
        assert result.event_type == "database_updated"
        assert result.source == "notion"
        assert "Test Database" in result.content
    
    @pytest.mark.asyncio
    async def test_normalize_block_created(self):
        """Test normalizing a Notion block created event."""
        normalizer = NotionNormalizer(notion_client=None)
        
        event_data = {
            "type": "block",
            "action": "created",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "block": {
                "id": "block_123",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "plain_text": "Test paragraph block",
                        }
                    ],
                },
            },
            "workspace": {
                "id": "workspace_123",
            },
        }
        
        result = await normalizer.normalize(event_data)
        
        assert result.event_type == "block_created"
        assert result.source == "notion"
        assert "Test paragraph block" in result.content


class TestSignatureVerification:
    """Test webhook signature verification."""
    
    def test_slack_signature_verification(self):
        """Test Slack HMAC-SHA256 signature verification."""
        from src.webhooks.verification import _verify_slack_signature
        from src.core.config import Settings
        from pydantic import SecretStr
        
        # Mock settings
        settings = Settings(
            app_secret_key=SecretStr("test"),
            neo4j_password=SecretStr("test"),
            postgres_password=SecretStr("test"),
            gemini_api_key=SecretStr("test"),
            groq_api_key=SecretStr("test"),
            jwt_secret_key=SecretStr("test"),
            slack_signing_secret=SecretStr("test_secret"),
        )
        
        body = b'{"type":"url_verification","challenge":"test"}'
        timestamp = str(int(time.time()))
        
        # Generate valid signature
        sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
        valid_signature = "v0=" + hmac.new(
            b"test_secret",
            sig_basestring.encode(),
            hashlib.sha256,
        ).hexdigest()
        
        # Test valid signature
        assert _verify_slack_signature(body, valid_signature, timestamp, settings)
        
        # Test invalid signature
        assert not _verify_slack_signature(body, "v0=invalid", timestamp, settings)
    
    def test_github_signature_verification(self):
        """Test GitHub HMAC-SHA256 signature verification."""
        from src.webhooks.verification import _verify_github_signature
        from src.core.config import Settings
        from pydantic import SecretStr
        
        # Mock settings
        settings = Settings(
            app_secret_key=SecretStr("test"),
            neo4j_password=SecretStr("test"),
            postgres_password=SecretStr("test"),
            gemini_api_key=SecretStr("test"),
            groq_api_key=SecretStr("test"),
            jwt_secret_key=SecretStr("test"),
            github_webhook_secret=SecretStr("test_secret"),
        )
        
        body = b'{"action":"opened","issue":{"number":42}}'
        
        # Generate valid signature
        valid_signature = "sha256=" + hmac.new(
            b"test_secret",
            body,
            hashlib.sha256,
        ).hexdigest()
        
        # Test valid signature
        assert _verify_github_signature(body, valid_signature, settings)
        
        # Test invalid signature
        assert not _verify_github_signature(body, "sha256=invalid", settings)
