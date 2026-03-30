# Third-Party Integrations Documentation

## Overview

NeuroGraph provides seamless integrations with popular third-party services to automatically capture and structure information from your workflow. Each integration uses webhooks to push events into the NeuroGraph memory system.

## Available Integrations

### Integration Matrix

| Service | Events Captured | Authentication | Real-Time | Supported Plans |
|---------|----------------|----------------|-----------|-----------------|
| **Slack** | Messages, reactions, threads | OAuth2 + Signing Secret | Yes | All |
| **GitHub** | Issues, PRs, commits, comments | OAuth2 + Webhook Secret | Yes | All |
| **Gmail** | Emails, labels, threads | OAuth2 | Yes (Push) | All |
| **Discord** | Messages, reactions | Bot Token | Yes | All |
| **Notion** | Pages, databases, blocks | OAuth2 + API Key | Yes | All |
| **Google Calendar** | Events, attendees, updates | OAuth2 | Yes (Push) | All |

## Slack Integration

### Setup Guide

#### Step 1: Create Slack App

1. Navigate to https://api.slack.com/apps
2. Click "Create New App" > "From scratch"
3. Enter app name: "NeuroGraph"
4. Select your workspace
5. Click "Create App"

#### Step 2: Configure OAuth Scopes

Navigate to "OAuth & Permissions" and add scopes:

**Bot Token Scopes**:
- `channels:history` - Read messages in public channels
- `channels:read` - View basic channel information
- `groups:history` - Read messages in private channels
- `groups:read` - View basic private channel information
- `im:history` - Read direct messages
- `im:read` - View direct message information
- `users:read` - View users in workspace
- `reactions:read` - Read emoji reactions

#### Step 3: Enable Event Subscriptions

1. Navigate to "Event Subscriptions"
2. Enable Events
3. Set Request URL: `https://your-domain.com/webhooks/inbound/slack`
4. Subscribe to bot events:
   - `message.channels` - Messages in public channels
   - `message.groups` - Messages in private channels
   - `message.im` - Direct messages
   - `reaction_added` - Reactions added

#### Step 4: Install App to Workspace

1. Navigate to "Install App"
2. Click "Install to Workspace"
3. Authorize the app
4. Copy the "Bot User OAuth Token"

#### Step 5: Configure NeuroGraph

```python
# .env
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-signing-secret
```

```python
# Configuration
INTEGRATIONS = {
    "slack": {
        "enabled": True,
        "bot_token": os.getenv("SLACK_BOT_TOKEN"),
        "signing_secret": os.getenv("SLACK_SIGNING_SECRET"),
        "layer": "shared"  # Store in shared layer
    }
}
```

### Event Mapping

| Slack Event | NeuroGraph Entity | Properties |
|-------------|-------------------|------------|
| **message** | Message | content, channel, user, timestamp |
| **channel** | Channel | name, purpose, members |
| **user** | Person | name, email, title |
| **reaction** | Reaction | emoji, user, message |
| **thread** | Thread | parent_message, replies |

### Example Usage

```python
# Slack message automatically creates entities
Slack Message:
"@john Let's review the Q1 roadmap in #planning tomorrow at 2pm"

NeuroGraph Creates:
- Entity: Person (John)
- Entity: Channel (#planning)
- Entity: Event (Meeting tomorrow 2pm)
- Entity: Project (Q1 roadmap)
- Relationships: John PARTICIPATES_IN Meeting, Meeting ABOUT Q1 roadmap
```

## GitHub Integration

### Setup Guide

#### Step 1: Create GitHub OAuth App

1. Navigate to GitHub Settings > Developer settings > OAuth Apps
2. Click "New OAuth App"
3. Fill in details:
   - Application name: "NeuroGraph"
   - Homepage URL: `https://your-domain.com`
   - Authorization callback URL: `https://your-domain.com/auth/github/callback`
4. Click "Register application"
5. Copy Client ID and generate Client Secret

#### Step 2: Configure Repository Webhook

For each repository:

1. Go to Settings > Webhooks > Add webhook
2. Payload URL: `https://your-domain.com/webhooks/inbound/github`
3. Content type: `application/json`
4. Secret: Generate a secure random string
5. Select events:
   - Issues
   - Pull requests
   - Push
   - Commit comments
   - Pull request reviews
6. Set Active
7. Add webhook

#### Step 3: Configure NeuroGraph

```python
# .env
GITHUB_CLIENT_ID=your-client-id
GITHUB_CLIENT_SECRET=your-client-secret
GITHUB_WEBHOOK_SECRET=your-webhook-secret
```

### Event Mapping

| GitHub Event | NeuroGraph Entity | Properties |
|--------------|-------------------|------------|
| **issue** | Issue | title, body, state, labels |
| **pull_request** | Pull Request | title, body, state, reviewers |
| **commit** | Commit | message, author, sha |
| **repository** | Project | name, description, language |
| **user** | Person | username, email |
| **label** | Tag | name, color |

### Example Usage

```python
# GitHub issue creates structured knowledge
GitHub Issue:
Title: "Implement user authentication"
Body: "Add OAuth support with Google and GitHub providers"
Labels: ["feature", "security"]
Assigned: @sarah

NeuroGraph Creates:
- Entity: Issue (Implement user authentication)
- Entity: Person (Sarah)
- Entity: Project (Repository name)
- Tags: feature, security
- Relationship: Sarah ASSIGNED_TO Issue
```

## Gmail Integration

### Setup Guide

#### Step 1: Enable Gmail API

1. Go to Google Cloud Console: https://console.cloud.google.com
2. Create or select project
3. Enable Gmail API
4. Navigate to "APIs & Services" > "Credentials"
5. Create OAuth 2.0 Client ID
6. Add authorized redirect URI: `https://your-domain.com/auth/gmail/callback`

#### Step 2: Set Up Push Notifications

```python
# Subscribe to Gmail push notifications
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

async def subscribe_to_gmail(user_credentials: Credentials):
    service = build('gmail', 'v1', credentials=user_credentials)
    
    request = {
        'labelIds': ['INBOX'],
        'topicName': 'projects/your-project/topics/gmail-notifications'
    }
    
    result = service.users().watch(userId='me', body=request).execute()
    return result
```

#### Step 3: Configure NeuroGraph

```python
# .env
GMAIL_CLIENT_ID=your-client-id
GMAIL_CLIENT_SECRET=your-client-secret
GMAIL_TOPIC_NAME=projects/your-project/topics/gmail-notifications
```

### Event Mapping

| Gmail Event | NeuroGraph Entity | Properties |
|-------------|-------------------|------------|
| **email** | Email | subject, body, from, to |
| **thread** | Thread | subject, participants |
| **sender** | Person | name, email |
| **label** | Tag | name |

### Example Usage

```python
# Email creates knowledge graph
Email:
From: john@example.com
Subject: "Q1 Budget Approval"
Body: "The Q1 budget of $100k has been approved. Sarah will manage allocation."

NeuroGraph Creates:
- Entity: Email (Q1 Budget Approval)
- Entity: Person (John)
- Entity: Person (Sarah)
- Entity: Project (Q1 Budget)
- Properties: budget=$100k, status=approved
- Relationship: Sarah MANAGES Q1 Budget
```

## Discord Integration

### Setup Guide

#### Step 1: Create Discord Application

1. Go to Discord Developer Portal: https://discord.com/developers/applications
2. Click "New Application"
3. Enter name: "NeuroGraph"
4. Navigate to "Bot" section
5. Click "Add Bot"
6. Enable "Message Content Intent"
7. Copy bot token

#### Step 2: Invite Bot to Server

Generate OAuth2 URL with permissions:
- Read Messages/View Channels
- Send Messages
- Read Message History

#### Step 3: Configure NeuroGraph

```python
# .env
DISCORD_BOT_TOKEN=your-bot-token
DISCORD_APPLICATION_ID=your-app-id
```

```python
# Bot implementation
import discord
from discord.ext import commands

class NeuroGraphBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!ng ', intents=intents)
    
    async def on_message(self, message):
        if message.author.bot:
            return
        
        # Send message to NeuroGraph webhook
        await send_to_neurograph({
            "type": "message",
            "content": message.content,
            "channel": str(message.channel.id),
            "author": str(message.author.id),
            "timestamp": message.created_at.isoformat()
        })
```

### Event Mapping

| Discord Event | NeuroGraph Entity | Properties |
|---------------|-------------------|------------|
| **message** | Message | content, channel, author |
| **channel** | Channel | name, type, topic |
| **user** | Person | username, discriminator |
| **server** | Organization | name, member_count |

## Notion Integration

### Setup Guide

#### Step 1: Create Notion Integration

1. Go to https://www.notion.so/my-integrations
2. Click "New integration"
3. Enter name: "NeuroGraph"
4. Select capabilities:
   - Read content
   - Update content
5. Submit

#### Step 2: Share Pages with Integration

For each page/database:
1. Open page in Notion
2. Click "Share"
3. Invite "NeuroGraph" integration
4. Set permissions

#### Step 3: Configure NeuroGraph

```python
# .env
NOTION_API_KEY=your-api-key
NOTION_WEBHOOK_SECRET=your-webhook-secret
```

```python
# Notion API client
from notion_client import AsyncClient

class NotionService:
    def __init__(self, api_key: str):
        self.client = AsyncClient(auth=api_key)
    
    async def get_page(self, page_id: str):
        return await self.client.pages.retrieve(page_id=page_id)
    
    async def get_database(self, database_id: str):
        return await self.client.databases.query(database_id=database_id)
```

### Event Mapping

| Notion Event | NeuroGraph Entity | Properties |
|--------------|-------------------|------------|
| **page** | Document | title, content, url |
| **database** | Database | name, properties |
| **block** | Content Block | type, content |
| **user** | Person | name, email |

## Google Calendar Integration

### Setup Guide

#### Step 1: Enable Calendar API

1. Go to Google Cloud Console
2. Enable Google Calendar API
3. Create OAuth 2.0 credentials
4. Add authorized redirect URI

#### Step 2: Watch Calendar for Changes

```python
# Subscribe to calendar notifications
from googleapiclient.discovery import build

async def watch_calendar(credentials: Credentials, calendar_id: str = 'primary'):
    service = build('calendar', 'v3', credentials=credentials)
    
    request = {
        'id': str(uuid.uuid4()),
        'type': 'web_hook',
        'address': 'https://your-domain.com/webhooks/inbound/google-calendar'
    }
    
    result = service.events().watch(calendarId=calendar_id, body=request).execute()
    return result
```

#### Step 3: Configure NeuroGraph

```python
# .env
GOOGLE_CALENDAR_CLIENT_ID=your-client-id
GOOGLE_CALENDAR_CLIENT_SECRET=your-client-secret
```

### Event Mapping

| Calendar Event | NeuroGraph Entity | Properties |
|----------------|-------------------|------------|
| **event** | Event | summary, start, end, location |
| **attendee** | Person | email, response_status |
| **calendar** | Calendar | name, description |

## Adding New Integrations

### Integration Template

```python
# app/integrations/custom-integration.py
from app.webhooks.normalizers.base import BaseNormalizer
from typing import Dict, Any

class CustomIntegrationNormalizer(BaseNormalizer):
    """
    Normalizer for CustomIntegration events.
    """
    
    async def normalize(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize CustomIntegration event to standard format.
        """
        return {
            "event_type": "custom_event",
            "content": self.extract_content(event_data),
            "layer": self.determine_layer(event_data),
            "entities": await self.extract_entities(event_data),
            "metadata": {
                "source": "custom_integration",
                "timestamp": event_data.get("timestamp"),
                "user": self.extract_user(event_data),
                **event_data.get("metadata", {})
            }
        }
    
    def extract_user(self, event_data: Dict[str, Any]) -> str:
        """
        Extract user identifier from event.
        """
        return event_data.get("user", {}).get("id")
    
    def extract_content(self, event_data: Dict[str, Any]) -> str:
        """
        Extract text content from event.
        """
        return event_data.get("content", "")
    
    def determine_layer(self, event_data: Dict[str, Any]) -> str:
        """
        Determine appropriate memory layer.
        """
        if event_data.get("is_private"):
            return "personal"
        elif event_data.get("organization_id"):
            return "organization"
        else:
            return "shared"
    
    async def extract_entities(
        self,
        event_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract entities from event data.
        """
        entities = []
        
        # Extract user as person entity
        if "user" in event_data:
            entities.append({
                "name": event_data["user"].get("name"),
                "type": "person",
                "properties": {
                    "user_id": event_data["user"].get("id"),
                    "email": event_data["user"].get("email")
                }
            })
        
        # Extract other entities based on event type
        # ...
        
        return entities
```

### Register New Integration

```python
# app/webhooks/handler.py
from app.integrations.custom_integration import CustomIntegrationNormalizer

NORMALIZERS = {
    "slack": SlackNormalizer(),
    "github": GitHubNormalizer(),
    "gmail": GmailNormalizer(),
    "discord": DiscordNormalizer(),
    "notion": NotionNormalizer(),
    "google-calendar": GoogleCalendarNormalizer(),
    "custom-integration": CustomIntegrationNormalizer(),  # Add here
}
```

### Add Webhook Route

```python
# app/api/routes/webhooks.py
@router.post("/inbound/custom-integration")
async def handle_custom_integration(
    request: Request,
    x_signature: str = Header(None)
):
    """
    Handle webhooks from CustomIntegration.
    """
    body = await request.body()
    
    # Verify signature
    if not validator.verify_custom_integration(body, x_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Process webhook
    event_data = await request.json()
    result = await process_webhook("custom-integration", event_data)
    
    return {"status": "accepted", "event_id": result["event_id"]}
```

## Authentication Methods

### OAuth2 Flow

```python
# app/api/routes/auth.py
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

router = APIRouter()

@router.get("/auth/{provider}/login")
async def oauth_login(provider: str):
    """
    Initiate OAuth2 flow.
    """
    oauth_urls = {
        "slack": "https://slack.com/oauth/v2/authorize",
        "github": "https://github.com/login/oauth/authorize",
        "google": "https://accounts.google.com/o/oauth2/v2/auth"
    }
    
    client_ids = {
        "slack": os.getenv("SLACK_CLIENT_ID"),
        "github": os.getenv("GITHUB_CLIENT_ID"),
        "google": os.getenv("GOOGLE_CLIENT_ID")
    }
    
    redirect_uris = {
        "slack": f"{BASE_URL}/auth/slack/callback",
        "github": f"{BASE_URL}/auth/github/callback",
        "google": f"{BASE_URL}/auth/google/callback"
    }
    
    scopes = {
        "slack": "channels:history,channels:read,users:read",
        "github": "repo,user",
        "google": "https://www.googleapis.com/auth/gmail.readonly"
    }
    
    url = oauth_urls[provider]
    params = {
        "client_id": client_ids[provider],
        "redirect_uri": redirect_uris[provider],
        "scope": scopes[provider],
        "state": generate_state_token()
    }
    
    auth_url = f"{url}?{urlencode(params)}"
    return RedirectResponse(auth_url)

@router.get("/auth/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str,
    state: str
):
    """
    Handle OAuth2 callback.
    """
    # Verify state token
    if not verify_state_token(state):
        raise HTTPException(status_code=400, detail="Invalid state")
    
    # Exchange code for token
    token = await exchange_code_for_token(provider, code)
    
    # Store token for user
    await store_integration_token(provider, token)
    
    return {"status": "success", "provider": provider}
```

### API Key Authentication

```python
# For integrations using API keys
INTEGRATION_API_KEYS = {
    "notion": os.getenv("NOTION_API_KEY"),
    "discord": os.getenv("DISCORD_BOT_TOKEN")
}

async def authenticate_with_api_key(provider: str, api_key: str) -> bool:
    """
    Verify API key for integration.
    """
    expected_key = INTEGRATION_API_KEYS.get(provider)
    return expected_key and api_key == expected_key
```

## Integration Management

### Enable/Disable Integrations

```python
# User settings API
@router.post("/integrations/{integration_type}/enable")
async def enable_integration(
    integration_type: str,
    user: User = Depends(get_current_user)
):
    """
    Enable integration for user.
    """
    await db.execute(
        """
        INSERT INTO user_integrations (user_id, integration_type, enabled)
        VALUES (:user_id, :integration_type, true)
        ON CONFLICT (user_id, integration_type)
        DO UPDATE SET enabled = true
        """,
        {"user_id": user.id, "integration_type": integration_type}
    )
    
    return {"status": "enabled"}

@router.post("/integrations/{integration_type}/disable")
async def disable_integration(
    integration_type: str,
    user: User = Depends(get_current_user)
):
    """
    Disable integration for user.
    """
    await db.execute(
        """
        UPDATE user_integrations
        SET enabled = false
        WHERE user_id = :user_id AND integration_type = :integration_type
        """,
        {"user_id": user.id, "integration_type": integration_type}
    )
    
    return {"status": "disabled"}
```

### List User Integrations

```python
@router.get("/integrations")
async def list_integrations(user: User = Depends(get_current_user)):
    """
    List all integrations for user.
    """
    integrations = await db.fetch_all(
        """
        SELECT integration_type, enabled, last_sync_at, created_at
        FROM user_integrations
        WHERE user_id = :user_id
        """,
        {"user_id": user.id}
    )
    
    return {
        "integrations": [dict(row) for row in integrations]
    }
```

## Data Privacy

### User Data Control

All integrations respect user privacy:

1. **Data Access**: Users control which data sources are connected
2. **Data Deletion**: Users can delete integration data at any time
3. **Access Revocation**: Revoking integration access stops data collection
4. **Export**: Users can export all data collected from integrations

### GDPR Compliance

```python
# Delete user integration data
@router.delete("/integrations/{integration_type}/data")
async def delete_integration_data(
    integration_type: str,
    user: User = Depends(get_current_user)
):
    """
    Delete all data collected from integration.
    """
    # Delete memories from this integration
    await db.execute(
        """
        DELETE FROM memories
        WHERE user_id = :user_id
        AND metadata->>'source' = :integration_type
        """,
        {"user_id": user.id, "integration_type": integration_type}
    )
    
    # Delete integration connection
    await db.execute(
        """
        DELETE FROM user_integrations
        WHERE user_id = :user_id AND integration_type = :integration_type
        """,
        {"user_id": user.id, "integration_type": integration_type}
    )
    
    return {"status": "deleted"}
```

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| **Webhook not receiving events** | Invalid URL or firewall | Verify URL is publicly accessible |
| **Signature verification fails** | Incorrect secret | Check secret matches integration config |
| **Rate limiting** | Too many requests | Implement exponential backoff |
| **Token expired** | OAuth token not refreshed | Implement token refresh flow |
| **Missing events** | Webhook subscription expired | Re-subscribe to push notifications |

### Debug Mode

```python
# Enable debug logging for integrations
INTEGRATION_DEBUG = {
    "slack": os.getenv("DEBUG_SLACK", "false").lower() == "true",
    "github": os.getenv("DEBUG_GITHUB", "false").lower() == "true"
}

async def process_webhook_with_debug(integration_type: str, event_data: dict):
    if INTEGRATION_DEBUG.get(integration_type):
        logger.debug(f"Raw webhook data: {json.dumps(event_data, indent=2)}")
    
    result = await process_webhook(integration_type, event_data)
    
    if INTEGRATION_DEBUG.get(integration_type):
        logger.debug(f"Processed result: {json.dumps(result, indent=2)}")
    
    return result
```

## Related Documentation

- [Webhooks](./webhooks.md) - Webhook implementation details
- [Architecture](./architecture.md) - Integration data flow
- [Memory](./memory.md) - Memory storage from integrations
- [API Reference](./api-reference.md) - Integration API endpoints
