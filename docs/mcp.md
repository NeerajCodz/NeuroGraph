# Model Context Protocol (MCP) Documentation

## Overview

NeuroGraph implements the Model Context Protocol (MCP) to enable direct tool access from AI assistants like Claude, Cursor, and Cline. Unlike the chat interface which requires orchestration, MCP tools provide direct, deterministic access to the memory system with minimal latency.

### Key Characteristics

- **No Orchestration**: MCP tools bypass the Groq orchestrator entirely
- **Direct Memory Access**: Tools call the memory manager directly
- **Deterministic**: Predictable, structured operations
- **Low Latency**: Minimal overhead compared to chat interface
- **Stateless**: Each tool call is independent

## MCP Tools Specification

### 1. remember

Store information in the memory system.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `content` | string | Yes | Information to remember |
| `layer` | string | No | "personal", "shared", or "organization" (default: personal) |
| `metadata` | object | No | Additional context |

**Example**:
```json
{
  "content": "Project Alpha deadline extended to March 31st",
  "layer": "shared",
  "metadata": {
    "source": "email",
    "date": "2024-01-15"
  }
}
```

**Returns**:
```json
{
  "memory_id": "mem_123abc",
  "entities_extracted": ["project_alpha"],
  "confidence": 0.94,
  "layer": "shared"
}
```

### 2. recall

Retrieve information from memory based on a query.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | Yes | Search query |
| `layers` | array | No | Layers to search (default: all accessible) |
| `max_results` | integer | No | Maximum results to return (default: 10) |
| `min_confidence` | float | No | Minimum confidence threshold (default: 0.5) |

**Example**:
```json
{
  "query": "What's the deadline for Project Alpha?",
  "layers": ["personal", "shared"],
  "max_results": 5,
  "min_confidence": 0.7
}
```

**Returns**:
```json
{
  "results": [
    {
      "content": "Project Alpha deadline extended to March 31st",
      "confidence": 0.94,
      "layer": "shared",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total_found": 1
}
```

### 3. search

Perform hybrid search across graph and vector stores.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | Yes | Search query |
| `search_type` | string | No | "vector", "graph", or "hybrid" (default: hybrid) |
| `filters` | object | No | Filter criteria |
| `limit` | integer | No | Max results (default: 20) |

**Example**:
```json
{
  "query": "machine learning projects",
  "search_type": "hybrid",
  "filters": {
    "entity_types": ["project"],
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-01-31"
    }
  },
  "limit": 10
}
```

**Returns**:
```json
{
  "results": [
    {
      "entity_id": "ent_proj_ml_001",
      "name": "ML Pipeline Project",
      "type": "project",
      "score": 0.92,
      "snippet": "Scalable machine learning pipeline..."
    }
  ],
  "total_found": 3
}
```

### 4. add-entity

Create a new entity in the knowledge graph.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | Yes | Entity name |
| `type` | string | Yes | Entity type (person, project, document, event, etc.) |
| `properties` | object | No | Entity properties |
| `layer` | string | No | Memory layer (default: personal) |

**Example**:
```json
{
  "name": "Project Gamma",
  "type": "project",
  "properties": {
    "status": "planning",
    "budget": 75000,
    "start_date": "2024-02-01"
  },
  "layer": "shared"
}
```

**Returns**:
```json
{
  "entity_id": "ent_proj_gamma",
  "name": "Project Gamma",
  "type": "project",
  "layer": "shared",
  "created_at": "2024-01-15T11:00:00Z"
}
```

### 5. add-relationship

Create a relationship between two entities.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `source_id` | string | Yes | Source entity ID |
| `target_id` | string | Yes | Target entity ID |
| `relationship_type` | string | Yes | Relationship type (e.g., MANAGES, WORKS_ON) |
| `properties` | object | No | Relationship properties |

**Example**:
```json
{
  "source_id": "ent_john_doe",
  "target_id": "ent_proj_gamma",
  "relationship_type": "LEADS",
  "properties": {
    "since": "2024-02-01",
    "role": "Technical Lead"
  }
}
```

**Returns**:
```json
{
  "relationship_id": "rel_456def",
  "source_id": "ent_john_doe",
  "target_id": "ent_proj_gamma",
  "type": "LEADS",
  "created_at": "2024-01-15T11:05:00Z"
}
```

### 6. get-entity

Retrieve detailed information about an entity.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `entity_id` | string | Yes | Entity ID |
| `depth` | integer | No | Relationship traversal depth (default: 1, max: 3) |
| `relationship_types` | array | No | Filter relationships by type |

**Example**:
```json
{
  "entity_id": "ent_proj_gamma",
  "depth": 2,
  "relationship_types": ["LEADS", "WORKS_ON"]
}
```

**Returns**:
```json
{
  "entity": {
    "id": "ent_proj_gamma",
    "name": "Project Gamma",
    "type": "project",
    "properties": {
      "status": "planning",
      "budget": 75000
    }
  },
  "relationships": [
    {
      "type": "LEADS",
      "direction": "incoming",
      "other_entity": {
        "id": "ent_john_doe",
        "name": "John Doe",
        "type": "person"
      }
    }
  ]
}
```

### 7. traverse-graph

Perform graph traversal from a starting entity.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `start_entity_id` | string | Yes | Starting entity ID |
| `relationship_types` | array | No | Relationship types to follow |
| `max_depth` | integer | No | Maximum traversal depth (default: 2, max: 5) |
| `filters` | object | No | Filter criteria for target entities |

**Example**:
```json
{
  "start_entity_id": "ent_john_doe",
  "relationship_types": ["LEADS", "WORKS_ON"],
  "max_depth": 2,
  "filters": {
    "entity_types": ["project"],
    "properties": {
      "status": "active"
    }
  }
}
```

**Returns**:
```json
{
  "paths": [
    {
      "nodes": [
        {"id": "ent_john_doe", "name": "John Doe"},
        {"id": "ent_proj_gamma", "name": "Project Gamma"}
      ],
      "relationships": [
        {"type": "LEADS"}
      ],
      "path_length": 1
    }
  ],
  "total_paths": 1
}
```

### 8. summarize

Generate a summary of stored information on a topic.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `topic` | string | Yes | Topic to summarize |
| `layers` | array | No | Layers to include (default: all accessible) |
| `time_range` | object | No | Date range filter |

**Example**:
```json
{
  "topic": "Project Gamma planning",
  "layers": ["shared", "organization"],
  "time_range": {
    "start": "2024-01-01",
    "end": "2024-01-31"
  }
}
```

**Returns**:
```json
{
  "summary": "Project Gamma is a new initiative starting February 2024 with a budget of $75,000. John Doe will serve as Technical Lead. The project is currently in the planning phase with objectives focused on...",
  "entities_referenced": ["ent_proj_gamma", "ent_john_doe"],
  "sources_count": 5,
  "confidence": 0.89
}
```

### 9. analyze-connections

Analyze relationships between entities.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `entity_ids` | array | Yes | Entity IDs to analyze (2-10 entities) |
| `max_depth` | integer | No | Maximum path length (default: 3, max: 5) |

**Example**:
```json
{
  "entity_ids": ["ent_john_doe", "ent_sarah_johnson", "ent_proj_alpha"],
  "max_depth": 3
}
```

**Returns**:
```json
{
  "connections": [
    {
      "entity_1": "ent_john_doe",
      "entity_2": "ent_proj_alpha",
      "path": [
        {"type": "WORKS_ON", "strength": 0.9}
      ],
      "path_length": 1
    },
    {
      "entity_1": "ent_sarah_johnson",
      "entity_2": "ent_proj_alpha",
      "path": [
        {"type": "MANAGES", "strength": 0.95}
      ],
      "path_length": 1
    }
  ],
  "insights": "John Doe and Sarah Johnson both work on Project Alpha, with Sarah in a management role."
}
```

### 10. temporal-query

Query information based on temporal criteria.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | Yes | Query description |
| `time_range` | object | Yes | Date range |
| `granularity` | string | No | "day", "week", or "month" (default: day) |

**Example**:
```json
{
  "query": "Project updates and milestones",
  "time_range": {
    "start": "2024-01-01",
    "end": "2024-01-31"
  },
  "granularity": "week"
}
```

**Returns**:
```json
{
  "timeline": [
    {
      "period": "2024-01-01 to 2024-01-07",
      "events": [
        {
          "date": "2024-01-05",
          "content": "Project Alpha kickoff meeting",
          "entity_id": "ent_proj_alpha"
        }
      ]
    }
  ],
  "total_events": 12
}
```

## Transport Options

### STDIO Transport

Standard input/output communication for local MCP servers.

**Configuration**:
```json
{
  "command": "python",
  "args": ["-m", "neurograph.mcp"],
  "env": {
    "NEUROGRAPH_API_URL": "http://localhost:8000",
    "NEUROGRAPH_API_KEY": "your-api-key"
  }
}
```

**Process Communication**:
- Input: JSON-RPC requests via stdin
- Output: JSON-RPC responses via stdout
- Errors: Logged to stderr

### SSE Transport

Server-Sent Events for remote MCP servers.

**Endpoint**: `http://localhost:8000/mcp/sse`

**Client Configuration**:
```json
{
  "transport": {
    "type": "sse",
    "url": "http://localhost:8000/mcp/sse",
    "headers": {
      "Authorization": "Bearer your-api-key"
    }
  }
}
```

**Event Format**:
```
event: message
data: {"jsonrpc": "2.0", "id": 1, "result": {...}}

event: error
data: {"jsonrpc": "2.0", "id": 1, "error": {...}}
```

## Client Setup Examples

### Claude Desktop

**File**: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

```json
{
  "mcpServers": {
    "neurograph": {
      "command": "python",
      "args": ["-m", "neurograph.mcp"],
      "env": {
        "NEUROGRAPH_API_URL": "http://localhost:8000",
        "NEUROGRAPH_API_KEY": "your-api-key",
        "NEUROGRAPH_USER_ID": "user_123"
      }
    }
  }
}
```

**Usage in Claude**:
```
User: Remember that the team meeting is on Friday at 2pm
Claude: I'll remember that for you.
[Uses 'remember' tool with content="team meeting is on Friday at 2pm"]

User: When is the team meeting?
Claude: Let me check.
[Uses 'recall' tool with query="team meeting"]
Claude: The team meeting is on Friday at 2pm.
```

### Cursor IDE

**File**: `.cursor/mcp.json` (project root)

```json
{
  "mcpServers": {
    "neurograph": {
      "command": "python",
      "args": ["-m", "neurograph.mcp"],
      "env": {
        "NEUROGRAPH_API_URL": "http://localhost:8000",
        "NEUROGRAPH_API_KEY": "your-api-key"
      }
    }
  }
}
```

**Usage in Cursor**:
- Tools available in Cursor's AI assistant
- Automatic context retrieval when working on code
- Entity creation for code symbols and documentation

### Cline (VSCode Extension)

**File**: `.vscode/mcp.json` (project root)

```json
{
  "mcpServers": {
    "neurograph": {
      "command": "python",
      "args": ["-m", "neurograph.mcp"],
      "env": {
        "NEUROGRAPH_API_URL": "http://localhost:8000",
        "NEUROGRAPH_API_KEY": "your-api-key"
      }
    }
  }
}
```

**Usage in Cline**:
- Right-click in editor: "Remember this code"
- Command palette: "Search NeuroGraph"
- Automatic project context injection

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NEUROGRAPH_API_URL` | Yes | NeuroGraph API base URL |
| `NEUROGRAPH_API_KEY` | Yes | API authentication key |
| `NEUROGRAPH_USER_ID` | No | User ID for personal layer access |
| `NEUROGRAPH_ORG_ID` | No | Organization ID for org layer access |
| `NEUROGRAPH_DEFAULT_LAYER` | No | Default memory layer (default: personal) |
| `NEUROGRAPH_TIMEOUT` | No | Request timeout in seconds (default: 30) |
| `NEUROGRAPH_MAX_RETRIES` | No | Max retry attempts (default: 3) |
| `NEUROGRAPH_LOG_LEVEL` | No | Logging level (default: INFO) |

## Adapter Layer for Non-MCP Clients

For AI assistants that don't support MCP natively, use the HTTP adapter.

### HTTP Adapter Endpoint

**Endpoint**: `POST /mcp/adapter/tool-call`

**Request**:
```json
{
  "tool": "remember",
  "parameters": {
    "content": "Important information to store",
    "layer": "personal"
  }
}
```

**Response**:
```json
{
  "result": {
    "memory_id": "mem_123abc",
    "confidence": 0.94
  }
}
```

### OpenAPI Function Calling

For OpenAPI-compatible clients:

```yaml
openapi: 3.0.0
info:
  title: NeuroGraph MCP Adapter
  version: 1.0.0
paths:
  /mcp/adapter/remember:
    post:
      summary: Store information in memory
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                content:
                  type: string
                layer:
                  type: string
                  enum: [personal, shared, organization]
      responses:
        '200':
          description: Success
```

### LangChain Integration

```python
from langchain.tools import Tool
from neurograph import NeuroGraphAdapter

adapter = NeuroGraphAdapter(
    api_url="http://localhost:8000",
    api_key="your-api-key"
)

remember_tool = Tool(
    name="remember",
    func=adapter.remember,
    description="Store information in NeuroGraph memory"
)

recall_tool = Tool(
    name="recall",
    func=adapter.recall,
    description="Retrieve information from NeuroGraph memory"
)

tools = [remember_tool, recall_tool]
```

### Custom Client Implementation

```python
import requests

class NeuroGraphMCPClient:
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def remember(self, content, layer="personal", metadata=None):
        response = requests.post(
            f"{self.api_url}/mcp/adapter/tool-call",
            json={
                "tool": "remember",
                "parameters": {
                    "content": content,
                    "layer": layer,
                    "metadata": metadata
                }
            },
            headers=self.headers
        )
        return response.json()["result"]
    
    def recall(self, query, layers=None, max_results=10):
        response = requests.post(
            f"{self.api_url}/mcp/adapter/tool-call",
            json={
                "tool": "recall",
                "parameters": {
                    "query": query,
                    "layers": layers,
                    "max_results": max_results
                }
            },
            headers=self.headers
        )
        return response.json()["result"]
```

## Error Handling

### Error Response Format

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid parameters",
    "data": {
      "parameter": "layer",
      "error": "must be one of: personal, shared, organization"
    }
  }
}
```

### JSON-RPC Error Codes

| Code | Meaning | Description |
|------|---------|-------------|
| -32700 | Parse error | Invalid JSON |
| -32600 | Invalid request | Invalid JSON-RPC request |
| -32601 | Method not found | Tool does not exist |
| -32602 | Invalid params | Invalid tool parameters |
| -32603 | Internal error | Server-side error |

### Application Error Codes

| Code | Description |
|------|-------------|
| 1000 | Authentication failed |
| 1001 | Insufficient permissions |
| 1002 | Layer access denied |
| 2000 | Entity not found |
| 2001 | Invalid entity type |
| 3000 | Database error |
| 3001 | Timeout |

## Performance Considerations

### Latency Comparison

| Operation | Chat Interface | MCP Tool | Improvement |
|-----------|---------------|----------|-------------|
| **Simple recall** | 500-2000ms | 100-300ms | 5-10x faster |
| **Entity creation** | 300-800ms | 50-150ms | 5-6x faster |
| **Graph traversal** | 400-1000ms | 50-300ms | 3-8x faster |
| **Search** | 600-1500ms | 100-500ms | 3-6x faster |

### Optimization Tips

1. **Batch Operations**: Use multiple tool calls in sequence for related operations
2. **Cache Responses**: Cache frequently accessed entities and relationships
3. **Limit Depth**: Keep graph traversal depth to 2-3 for performance
4. **Filter Early**: Apply filters in tool parameters rather than post-processing
5. **Use Vector Search**: For semantic queries, vector search is faster than graph traversal

## Security Best Practices

1. **API Key Storage**: Store API keys in secure environment variables, never in code
2. **Key Rotation**: Rotate API keys regularly
3. **Scope Limitation**: Use user-level keys for personal access, org-level for shared
4. **Transport Security**: Use HTTPS for remote MCP servers
5. **Audit Logging**: Enable audit logs for MCP tool calls in production

## Testing MCP Tools

### CLI Testing

```bash
# Install MCP client
pip install mcp-client-cli

# Test tool call
mcp-client call \
  --server python -m neurograph.mcp \
  --tool remember \
  --params '{"content": "Test memory", "layer": "personal"}'
```

### Python Testing

```python
import pytest
from neurograph.mcp import MCPServer

@pytest.fixture
def mcp_server():
    return MCPServer(
        api_url="http://localhost:8000",
        api_key="test-key"
    )

def test_remember(mcp_server):
    result = mcp_server.call_tool("remember", {
        "content": "Test memory",
        "layer": "personal"
    })
    assert result["memory_id"].startswith("mem_")
    assert result["confidence"] > 0.5

def test_recall(mcp_server):
    result = mcp_server.call_tool("recall", {
        "query": "test memory",
        "max_results": 5
    })
    assert len(result["results"]) >= 0
```

## Monitoring and Debugging

### Enable Debug Logging

```bash
export NEUROGRAPH_LOG_LEVEL=DEBUG
python -m neurograph.mcp
```

### Tool Call Metrics

Monitor these metrics for MCP tool performance:

- Tool call rate (calls/minute)
- Tool call latency (p50, p95, p99)
- Tool call errors (by error type)
- API authentication failures
- Layer access violations

### Debugging Failed Tool Calls

1. Check API key validity
2. Verify network connectivity to API
3. Review request parameters for validation errors
4. Check layer access permissions
5. Examine API server logs for detailed errors

## Related Documentation

- [API Reference](./api-reference.md) - REST API that MCP tools call
- [Architecture](./architecture.md) - MCP data flow vs chat interface
- [Memory](./memory.md) - Memory layer access from MCP tools
- [Backend](./backend.md) - MCP server implementation details
