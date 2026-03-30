# API Reference

## Base URL

```
Development: http://localhost:8000
Production: https://api.neurograph.example.com
```

## Authentication

All API requests require authentication using JWT tokens.

### Obtaining Tokens

**Endpoint**: `POST /auth/login`

**Request**:
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### Using Tokens

Include the access token in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Refreshing Tokens

**Endpoint**: `POST /auth/refresh`

**Request**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

## Rate Limiting

Rate limits are applied per user/API key:

| Tier | Requests/Minute | Requests/Hour | Requests/Day |
|------|-----------------|---------------|--------------|
| **Free** | 60 | 1,000 | 10,000 |
| **Pro** | 300 | 10,000 | 100,000 |
| **Enterprise** | 1,000 | 50,000 | Unlimited |

**Rate Limit Headers**:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640995200
```

## Chat API

### Send Message

Create a new chat message and receive an orchestrated response.

**Endpoint**: `POST /chat/message`

**Request**:
```json
{
  "message": "What did I discuss with the team yesterday?",
  "mode": "organization",
  "organization_id": "org_123abc",
  "global_memory": true,
  "conversation_id": "conv_456def",
  "context": {
    "timezone": "America/New_York",
    "location": "New York, NY"
  }
}
```

**Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | User message content |
| `mode` | string | Yes | "general" or "organization" |
| `organization_id` | string | Conditional | Required if mode is "organization" |
| `global_memory` | boolean | No | Enable cross-layer memory access (default: true) |
| `conversation_id` | string | No | Continue existing conversation |
| `context` | object | No | Additional context metadata |

**Response**:
```json
{
  "response": "Based on yesterday's team meeting, you discussed three main topics...",
  "conversation_id": "conv_456def",
  "agents_used": ["read", "graph"],
  "entities_retrieved": ["team_meeting_2024_01_15", "sarah_johnson", "project_alpha"],
  "sources": [
    {
      "type": "memory",
      "layer": "shared",
      "entity_id": "ent_789ghi",
      "confidence": 0.92
    }
  ],
  "execution_time_ms": 487,
  "tokens_used": 1523
}
```

### List Conversations

Retrieve conversation history.

**Endpoint**: `GET /chat/conversations`

**Query Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `mode` | string | Filter by mode (general/organization) |
| `organization_id` | string | Filter by organization |
| `limit` | integer | Max results (default: 50, max: 200) |
| `offset` | integer | Pagination offset |

**Response**:
```json
{
  "conversations": [
    {
      "id": "conv_456def",
      "mode": "organization",
      "organization_id": "org_123abc",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T14:22:00Z",
      "message_count": 12,
      "last_message": "Based on yesterday's team meeting..."
    }
  ],
  "total": 156,
  "limit": 50,
  "offset": 0
}
```

### Get Conversation

Retrieve a specific conversation with messages.

**Endpoint**: `GET /chat/conversations/{conversation_id}`

**Response**:
```json
{
  "id": "conv_456def",
  "mode": "organization",
  "organization_id": "org_123abc",
  "created_at": "2024-01-15T10:30:00Z",
  "messages": [
    {
      "id": "msg_001",
      "role": "user",
      "content": "What did I discuss with the team yesterday?",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "id": "msg_002",
      "role": "assistant",
      "content": "Based on yesterday's team meeting...",
      "timestamp": "2024-01-15T10:30:02Z",
      "metadata": {
        "agents_used": ["read", "graph"],
        "execution_time_ms": 487
      }
    }
  ]
}
```

## Memory API

### Remember (Write)

Store information in the memory system.

**Endpoint**: `POST /memory/remember`

**Request**:
```json
{
  "content": "Sarah mentioned that Project Alpha is ahead of schedule and should be completed by end of Q1.",
  "layer": "personal",
  "metadata": {
    "source": "meeting",
    "participants": ["sarah_johnson", "john_doe"],
    "date": "2024-01-15"
  },
  "extract_entities": true
}
```

**Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | string | Yes | Information to remember |
| `layer` | string | Yes | "personal", "shared", or "organization" |
| `metadata` | object | No | Additional context |
| `extract_entities` | boolean | No | Auto-extract entities (default: true) |

**Response**:
```json
{
  "memory_id": "mem_123abc",
  "entities_extracted": [
    {
      "id": "ent_sarah_johnson",
      "name": "Sarah Johnson",
      "type": "person"
    },
    {
      "id": "ent_project_alpha",
      "name": "Project Alpha",
      "type": "project"
    }
  ],
  "relationships_created": [
    {
      "source": "ent_sarah_johnson",
      "target": "ent_project_alpha",
      "type": "MENTIONED"
    }
  ],
  "confidence": 0.95,
  "layer": "personal"
}
```

### Recall (Read)

Retrieve information from memory.

**Endpoint**: `POST /memory/recall`

**Request**:
```json
{
  "query": "What did Sarah say about Project Alpha?",
  "layers": ["personal", "shared"],
  "max_results": 10,
  "min_confidence": 0.7,
  "temporal_weight": 0.3
}
```

**Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | Search query |
| `layers` | array | No | Layers to search (default: all accessible) |
| `max_results` | integer | No | Max results (default: 10, max: 100) |
| `min_confidence` | float | No | Minimum confidence score (default: 0.5) |
| `temporal_weight` | float | No | Recency weighting (0-1, default: 0.2) |

**Response**:
```json
{
  "results": [
    {
      "memory_id": "mem_123abc",
      "content": "Sarah mentioned that Project Alpha is ahead of schedule...",
      "confidence": 0.95,
      "layer": "personal",
      "created_at": "2024-01-15T10:30:00Z",
      "entities": ["ent_sarah_johnson", "ent_project_alpha"],
      "relevance_score": 0.89
    }
  ],
  "total_found": 3,
  "query_time_ms": 45
}
```

### Search

Hybrid search across graph and vector stores.

**Endpoint**: `POST /memory/search`

**Request**:
```json
{
  "query": "machine learning projects",
  "search_type": "hybrid",
  "filters": {
    "entity_types": ["project", "document"],
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-01-31"
    }
  },
  "limit": 20
}
```

**Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | Search query |
| `search_type` | string | No | "vector", "graph", or "hybrid" (default: hybrid) |
| `filters` | object | No | Filter criteria |
| `limit` | integer | No | Max results (default: 20, max: 100) |

**Response**:
```json
{
  "results": [
    {
      "entity_id": "ent_proj_ml_001",
      "name": "Machine Learning Pipeline",
      "type": "project",
      "score": 0.92,
      "snippet": "A scalable machine learning pipeline for...",
      "metadata": {
        "created_at": "2024-01-10T09:00:00Z",
        "tags": ["ml", "data-science", "python"]
      }
    }
  ],
  "search_stats": {
    "vector_results": 15,
    "graph_results": 8,
    "merged_results": 20,
    "query_time_ms": 78
  }
}
```

## Graph API

### Add Entity

Create a new entity in the knowledge graph.

**Endpoint**: `POST /graph/entities`

**Request**:
```json
{
  "name": "Project Beta",
  "type": "project",
  "properties": {
    "status": "active",
    "start_date": "2024-01-01",
    "budget": 50000,
    "team_size": 5
  },
  "layer": "shared"
}
```

**Response**:
```json
{
  "entity_id": "ent_proj_beta",
  "name": "Project Beta",
  "type": "project",
  "created_at": "2024-01-15T11:00:00Z",
  "layer": "shared"
}
```

### Add Relationship

Create a relationship between entities.

**Endpoint**: `POST /graph/relationships`

**Request**:
```json
{
  "source_id": "ent_sarah_johnson",
  "target_id": "ent_proj_beta",
  "relationship_type": "MANAGES",
  "properties": {
    "since": "2024-01-01",
    "role": "Project Lead"
  }
}
```

**Response**:
```json
{
  "relationship_id": "rel_123abc",
  "source_id": "ent_sarah_johnson",
  "target_id": "ent_proj_beta",
  "type": "MANAGES",
  "created_at": "2024-01-15T11:05:00Z"
}
```

### Get Entity

Retrieve entity details with relationships.

**Endpoint**: `GET /graph/entities/{entity_id}`

**Query Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `depth` | integer | Relationship traversal depth (default: 1, max: 3) |
| `relationship_types` | string | Comma-separated types to include |

**Response**:
```json
{
  "entity": {
    "id": "ent_proj_beta",
    "name": "Project Beta",
    "type": "project",
    "properties": {
      "status": "active",
      "start_date": "2024-01-01"
    },
    "created_at": "2024-01-01T09:00:00Z"
  },
  "relationships": [
    {
      "id": "rel_123abc",
      "type": "MANAGES",
      "direction": "incoming",
      "other_entity": {
        "id": "ent_sarah_johnson",
        "name": "Sarah Johnson",
        "type": "person"
      }
    }
  ]
}
```

### Traverse Graph

Perform graph traversal queries.

**Endpoint**: `POST /graph/traverse`

**Request**:
```json
{
  "start_entity_id": "ent_sarah_johnson",
  "relationship_types": ["MANAGES", "WORKS_ON"],
  "max_depth": 2,
  "filters": {
    "entity_types": ["project"],
    "properties": {
      "status": "active"
    }
  }
}
```

**Response**:
```json
{
  "paths": [
    {
      "nodes": [
        {"id": "ent_sarah_johnson", "name": "Sarah Johnson"},
        {"id": "ent_proj_beta", "name": "Project Beta"}
      ],
      "relationships": [
        {"type": "MANAGES"}
      ],
      "path_length": 1
    }
  ],
  "total_paths": 3,
  "query_time_ms": 23
}
```

## Organization API

### List Organizations

Get organizations accessible to the user.

**Endpoint**: `GET /organizations`

**Response**:
```json
{
  "organizations": [
    {
      "id": "org_123abc",
      "name": "Acme Corporation",
      "role": "admin",
      "member_count": 45,
      "created_at": "2023-06-01T00:00:00Z"
    }
  ]
}
```

### Get Organization Details

**Endpoint**: `GET /organizations/{organization_id}`

**Response**:
```json
{
  "id": "org_123abc",
  "name": "Acme Corporation",
  "description": "Technology consulting firm",
  "settings": {
    "global_memory_default": true,
    "retention_days": 365
  },
  "member_count": 45,
  "created_at": "2023-06-01T00:00:00Z"
}
```

## Webhook API

### Register Webhook

Create a webhook endpoint to receive events from NeuroGraph.

**Endpoint**: `POST /webhooks/register`

**Request**:
```json
{
  "url": "https://your-app.com/webhooks/neurograph",
  "events": ["entity.created", "relationship.created", "memory.added"],
  "secret": "your_webhook_secret"
}
```

**Response**:
```json
{
  "webhook_id": "wh_123abc",
  "url": "https://your-app.com/webhooks/neurograph",
  "events": ["entity.created", "relationship.created", "memory.added"],
  "created_at": "2024-01-15T12:00:00Z"
}
```

### Receive External Webhook

Accept webhooks from external services.

**Endpoint**: `POST /webhooks/inbound/{integration_type}`

**Supported Integration Types**: `slack`, `github`, `gmail`, `discord`, `notion`, `google-calendar`

**Headers**:
```
X-Signature: sha256=abc123...
X-Integration-Type: slack
```

**Example Request (Slack)**:
```json
{
  "event": {
    "type": "message",
    "channel": "C123ABC",
    "user": "U456DEF",
    "text": "Let's discuss the Q1 roadmap tomorrow",
    "ts": "1640995200.000100"
  }
}
```

**Response**:
```json
{
  "status": "accepted",
  "event_id": "evt_123abc",
  "processed": true
}
```

## Analytics API

### Get Usage Statistics

**Endpoint**: `GET /analytics/usage`

**Query Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `start_date` | string | ISO 8601 date |
| `end_date` | string | ISO 8601 date |
| `granularity` | string | "hour", "day", or "month" |

**Response**:
```json
{
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z"
  },
  "metrics": {
    "total_messages": 1523,
    "total_memories": 847,
    "entities_created": 234,
    "relationships_created": 456,
    "mcp_tool_calls": 3421,
    "webhook_events": 678
  },
  "by_day": [
    {
      "date": "2024-01-01",
      "messages": 45,
      "memories": 23
    }
  ]
}
```

### Get Graph Statistics

**Endpoint**: `GET /analytics/graph`

**Response**:
```json
{
  "total_entities": 12543,
  "total_relationships": 34567,
  "entity_types": {
    "person": 3421,
    "project": 856,
    "document": 4532,
    "event": 2109
  },
  "relationship_types": {
    "KNOWS": 5643,
    "WORKS_ON": 2341,
    "MENTIONS": 8923
  },
  "largest_connected_component": 8734,
  "avg_degree": 5.2
}
```

## Error Codes

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Resource already exists |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 502 | Bad Gateway | Upstream service unavailable |
| 503 | Service Unavailable | Temporary service outage |

### Error Response Format

```json
{
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "The 'layer' parameter must be one of: personal, shared, organization",
    "details": {
      "parameter": "layer",
      "provided": "invalid_layer",
      "allowed": ["personal", "shared", "organization"]
    },
    "request_id": "req_123abc"
  }
}
```

### Application Error Codes

| Code | Description |
|------|-------------|
| `INVALID_PARAMETER` | Invalid request parameter |
| `MISSING_REQUIRED_FIELD` | Required field not provided |
| `AUTHENTICATION_FAILED` | Invalid credentials |
| `TOKEN_EXPIRED` | JWT token has expired |
| `INSUFFICIENT_PERMISSIONS` | User lacks required permissions |
| `RESOURCE_NOT_FOUND` | Requested resource does not exist |
| `DUPLICATE_RESOURCE` | Resource already exists |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `LAYER_ACCESS_DENIED` | User cannot access memory layer |
| `ORGANIZATION_NOT_FOUND` | Organization does not exist |
| `INVALID_CONVERSATION` | Conversation ID not found |
| `ORCHESTRATION_FAILED` | Agent orchestration error |
| `LLM_API_ERROR` | External LLM API failure |
| `DATABASE_ERROR` | Database operation failed |
| `VALIDATION_ERROR` | Data validation failed |

## Pagination

List endpoints support cursor-based pagination:

**Request**:
```
GET /chat/conversations?limit=50&cursor=eyJpZCI6ImNvbnZfMTIzIn0
```

**Response**:
```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6ImNvbnZfNDU2In0",
    "has_more": true
  }
}
```

## Webhook Signatures

Verify webhook authenticity using HMAC-SHA256:

```python
import hmac
import hashlib

def verify_signature(payload_body, signature_header, secret):
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload_body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(
        f"sha256={expected_signature}",
        signature_header
    )
```

## SDK Examples

### Python

```python
from neurograph import NeuroGraphClient

client = NeuroGraphClient(
    api_key="your_api_key",
    base_url="https://api.neurograph.example.com"
)

# Send chat message
response = client.chat.send_message(
    message="What did I discuss yesterday?",
    mode="general",
    global_memory=True
)

# Remember information
memory = client.memory.remember(
    content="Meeting notes from Q1 planning",
    layer="personal"
)

# Search
results = client.memory.search(
    query="Q1 planning",
    search_type="hybrid"
)
```

### JavaScript

```javascript
import { NeuroGraphClient } from '@neurograph/client';

const client = new NeuroGraphClient({
  apiKey: 'your_api_key',
  baseUrl: 'https://api.neurograph.example.com'
});

// Send chat message
const response = await client.chat.sendMessage({
  message: 'What did I discuss yesterday?',
  mode: 'general',
  globalMemory: true
});

// Remember information
const memory = await client.memory.remember({
  content: 'Meeting notes from Q1 planning',
  layer: 'personal'
});
```

## WebSocket API

### Connect

```
ws://localhost:8000/ws?token=your_jwt_token
```

### Message Format

**Client to Server**:
```json
{
  "type": "subscribe",
  "channel": "graph_updates",
  "filters": {
    "entity_types": ["project"]
  }
}
```

**Server to Client**:
```json
{
  "type": "graph_update",
  "event": "entity_created",
  "data": {
    "entity_id": "ent_123abc",
    "name": "New Project",
    "type": "project"
  },
  "timestamp": "2024-01-15T14:30:00Z"
}
```

## Related Documentation

- [Architecture](./architecture.md) - System architecture and data flows
- [MCP](./mcp.md) - Model Context Protocol integration
- [Webhooks](./webhooks.md) - Webhook integration details
- [Frontend](./frontend.md) - Frontend API usage examples
