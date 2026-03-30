# Architecture Documentation

## Design Principles

### 1. Separation of Concerns

The system is divided into distinct layers with clear responsibilities:

- **Client Layer**: User interfaces (Web, MCP clients)
- **API Layer**: Request routing and protocol handling
- **Orchestration Layer**: Intent classification and agent coordination (chat only)
- **Processing Layer**: Memory operations and LLM interactions
- **Storage Layer**: Persistent data storage

### 2. Orchestration Boundary

**Critical Distinction**: Orchestration only applies to the chat interface. MCP clients and webhooks bypass the orchestrator entirely for direct, deterministic tool execution.

```mermaid
graph LR
    Chat[Chat Interface] -->|Requires Orchestration| Orch[Groq Orchestrator]
    MCP[MCP Tools] -->|Direct Access| Memory[Memory Manager]
    Webhook[Webhooks] -->|Direct Access| Memory
    
    Orch -->|Spawns| Agents[Agent System]
    Agents -->|Uses| Memory
```

### 3. Stateless Agent Design

All agents are stateless and ephemeral:

- No persistent state between invocations
- Context passed explicitly in each request
- Enables horizontal scaling
- Simplifies error recovery

### 4. Memory Isolation

Three-layer memory architecture with strict isolation:

- **Personal Layer**: User-specific, private
- **Shared Layer**: Team/project-specific, scoped access
- **Organization Layer**: Global, read-only for most users

### 5. Hybrid Search Strategy

Combines graph traversal with vector similarity:

- Graph provides relational context
- Vectors enable semantic similarity
- Fusion algorithms merge results

## Component Architecture

```mermaid
graph TB
    subgraph "Frontend Container"
        UI[React Application]
        Graph[D3.js Visualization]
        Store[Zustand State]
    end
    
    subgraph "Backend Container"
        API[FastAPI Server]
        WS[WebSocket Handler]
        MCP_Server[MCP Server]
        Webhook_Handler[Webhook Handler]
    end
    
    subgraph "Orchestration Container"
        Groq[Groq API Client]
        Orchestrator[Intent Classifier]
        Spawner[Agent Spawner]
    end
    
    subgraph "Agent Container"
        Writer[Write Agent]
        Reader[Read Agent]
        Search[Search Agent]
        Graph_Agent[Graph Agent]
        Integrate[Integration Agent]
    end
    
    subgraph "Memory Container"
        Memory_Manager[Memory Manager]
        Confidence[Confidence Scorer]
        Priority[Priority Engine]
    end
    
    subgraph "LLM Services"
        Gemini_Flash[Gemini Flash]
        Gemini_Pro[Gemini Pro]
        Gemini_Embed[Gemini Embeddings]
    end
    
    subgraph "Storage Container"
        Neo4j_DB[(Neo4j)]
        Postgres[(PostgreSQL)]
        Redis_Cache[(Redis)]
    end
    
    UI -->|HTTP/WS| API
    API -->|Chat| Orchestrator
    API -->|MCP| MCP_Server
    API -->|Events| Webhook_Handler
    
    Orchestrator -->|Classify| Groq
    Orchestrator -->|Spawn| Spawner
    Spawner -->|Create| Writer & Reader & Search & Graph_Agent & Integrate
    
    MCP_Server -->|Direct| Memory_Manager
    Webhook_Handler -->|Direct| Memory_Manager
    
    Writer & Reader & Search & Graph_Agent & Integrate -->|Use| Memory_Manager
    
    Memory_Manager -->|Score| Confidence
    Memory_Manager -->|Prioritize| Priority
    Memory_Manager -->|Query| Gemini_Flash & Gemini_Pro & Gemini_Embed
    Memory_Manager -->|Store| Neo4j_DB & Postgres & Redis_Cache
```

## Data Flow Diagrams

### Flow 1: Chat Interface Query

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Orchestrator
    participant Agent
    participant Memory
    participant LLM
    participant DB
    
    User->>Frontend: Send message
    Frontend->>API: POST /chat/message
    API->>Orchestrator: Classify intent
    Orchestrator->>LLM: Groq API call
    LLM-->>Orchestrator: Intent + params
    Orchestrator->>Agent: Spawn agent(s)
    
    loop Agent Processing
        Agent->>Memory: Request operation
        Memory->>DB: Read/Write
        DB-->>Memory: Data
        Memory->>LLM: Generate response
        LLM-->>Memory: Result
        Memory-->>Agent: Processed data
    end
    
    Agent-->>API: Agent results
    API-->>Frontend: WebSocket update
    Frontend-->>User: Display response
```

**Key Characteristics**:
- Intent classification via Groq
- Dynamic agent spawning
- Parallel agent execution where possible
- Aggregated response assembly

### Flow 2: MCP Tool Call

```mermaid
sequenceDiagram
    participant MCP_Client as MCP Client
    participant MCP_Server as MCP Server
    participant Memory
    participant DB
    participant LLM
    
    MCP_Client->>MCP_Server: Tool call (e.g., remember)
    Note over MCP_Server: NO orchestration
    MCP_Server->>Memory: Direct operation
    Memory->>DB: Write/Read
    DB-->>Memory: Data
    
    opt If LLM needed
        Memory->>LLM: Generate embedding/summary
        LLM-->>Memory: Result
    end
    
    Memory-->>MCP_Server: Operation result
    MCP_Server-->>MCP_Client: Tool response
```

**Key Characteristics**:
- No orchestration overhead
- Direct memory access
- Deterministic tool execution
- Minimal latency

### Flow 3: Webhook Event Processing

```mermaid
sequenceDiagram
    participant External as External Service
    participant Webhook
    participant Normalizer
    participant Memory
    participant DB
    participant LLM
    
    External->>Webhook: POST webhook event
    Webhook->>Webhook: Verify signature
    Webhook->>Normalizer: Normalize event
    
    Note over Normalizer: Convert to standard schema
    
    Normalizer->>Memory: Store event
    Memory->>LLM: Extract entities
    LLM-->>Memory: Entities + relationships
    Memory->>DB: Write graph
    DB-->>Memory: Confirmation
    Memory-->>Webhook: Success
    Webhook-->>External: 200 OK
```

**Key Characteristics**:
- Signature verification for security
- Event normalization across providers
- Asynchronous processing via queue
- Automatic entity extraction

## Interface Comparison

### Chat Interface vs MCP Access

| Aspect | Chat Interface | MCP Tools |
|--------|---------------|-----------|
| **Orchestration** | Required (Groq) | None |
| **Agent System** | Dynamic spawning | Direct memory access |
| **Latency** | Higher (orchestration + agents) | Lower (direct calls) |
| **Flexibility** | Natural language, adaptive | Structured tool calls |
| **Use Case** | Interactive exploration | Programmatic integration |
| **Memory Mode** | General or Organization | Determined by API key |
| **Global Memory Toggle** | User-controlled | Always enabled |
| **Cost** | Higher (Groq + Gemini) | Lower (Gemini only) |
| **Parallelization** | Automatic agent coordination | Client-controlled |

### Mode Selection Behavior

#### Chat Interface Modes

**General Mode**:
- Personal memory layer only
- User-specific entities and relationships
- Private context retrieval
- Global Memory toggle controls cross-mode access

**Organization Mode**:
- Select organization from dropdown
- Shared + Organizational layers
- Team-wide context visibility
- Global Memory toggle adds personal layer

#### MCP Client Context

MCP clients operate based on API key scope:
- User-level key: Personal layer access
- Organization-level key: Shared/Organizational layer access
- No mode selection required

## Scaling Strategy

### Horizontal Scaling

```mermaid
graph TB
    LB[Load Balancer]
    
    subgraph "API Tier - Auto-scaled"
        API1[FastAPI Instance 1]
        API2[FastAPI Instance 2]
        API3[FastAPI Instance N]
    end
    
    subgraph "Orchestration Tier - Auto-scaled"
        Orch1[Orchestrator 1]
        Orch2[Orchestrator 2]
    end
    
    subgraph "Worker Tier - Auto-scaled"
        Worker1[Agent Worker 1]
        Worker2[Agent Worker 2]
        Worker3[Agent Worker N]
    end
    
    subgraph "Storage Tier - Clustered"
        Neo4j_Cluster[(Neo4j Cluster)]
        PG_Cluster[(PostgreSQL Cluster)]
        Redis_Cluster[(Redis Cluster)]
    end
    
    LB -->|Round-robin| API1 & API2 & API3
    API1 & API2 & API3 -->|Task queue| Worker1 & Worker2 & Worker3
    API1 & API2 & API3 -->|Classify| Orch1 & Orch2
    Worker1 & Worker2 & Worker3 -->|Read/Write| Neo4j_Cluster & PG_Cluster & Redis_Cluster
```

### Scaling Targets

| Component | Scaling Metric | Target |
|-----------|---------------|--------|
| **API Servers** | CPU utilization | 70% average |
| **Orchestrators** | Request queue depth | <100 pending |
| **Agent Workers** | Task queue depth | <500 pending |
| **Neo4j** | Connections | <1000 per instance |
| **PostgreSQL** | Connections | <500 per instance |
| **Redis** | Memory utilization | 75% average |

### Caching Strategy

```mermaid
graph LR
    Request[Request] -->|Check| L1[L1: Application Cache<br/>In-Memory]
    L1 -->|Miss| L2[L2: Redis Cache<br/>5 min TTL]
    L2 -->|Miss| L3[L3: Database<br/>PostgreSQL/Neo4j]
    L3 -->|Write-through| L2
    L2 -->|Write-through| L1
```

**Cache Layers**:

1. **L1 - Application Memory**: Hot data, 1-minute TTL
2. **L2 - Redis**: Warm data, 5-minute TTL
3. **L3 - Database**: Cold data, persistent

**Cache Invalidation**:
- Write operations invalidate related cache entries
- Time-based expiration for stale data
- Event-driven invalidation for real-time updates

## Security Architecture

### Authentication Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Auth
    participant DB
    
    Client->>API: Request with credentials
    API->>Auth: Validate credentials
    Auth->>DB: Check user/org
    DB-->>Auth: User data + permissions
    Auth->>Auth: Generate JWT
    Auth-->>API: JWT token
    API-->>Client: Token + refresh token
    
    Note over Client,API: Subsequent requests
    
    Client->>API: Request with JWT
    API->>Auth: Verify JWT
    Auth-->>API: Claims + permissions
    API->>API: Authorize action
    API-->>Client: Response
```

### Security Layers

| Layer | Mechanism | Purpose |
|-------|-----------|---------|
| **Transport** | TLS 1.3 | Encryption in transit |
| **Authentication** | JWT tokens | User identity verification |
| **Authorization** | Role-based access control (RBAC) | Permission enforcement |
| **Data** | AES-256 encryption at rest | Data protection |
| **API** | Rate limiting + IP filtering | DDoS protection |
| **Webhook** | HMAC signature verification | Event authenticity |
| **MCP** | API key authentication | Tool access control |

### Memory Layer Isolation

```mermaid
graph TB
    User[User Request]
    
    User -->|Auth| Check{Layer Access Check}
    
    Check -->|Personal| Personal[Personal Layer<br/>User-owned data]
    Check -->|Shared| Shared[Shared Layer<br/>Project/team data]
    Check -->|Org| Org[Organization Layer<br/>Company-wide data]
    
    Personal -.->|Global Memory ON| Shared
    Shared -.->|Global Memory ON| Org
    
    Personal -->|Isolated| Write_P[Write: User only]
    Shared -->|Scoped| Write_S[Write: Team members]
    Org -->|Restricted| Write_O[Write: Admins only]
```

**Isolation Guarantees**:

1. **Personal Layer**: Only accessible by owning user
2. **Shared Layer**: Accessible by project/team members
3. **Organization Layer**: Read access for all org members, write for admins
4. **Global Memory Toggle**: User-controlled cross-layer retrieval (read-only)

## Performance Targets

### Latency Targets

| Operation | p50 | p95 | p99 |
|-----------|-----|-----|-----|
| **Chat message** (orchestrated) | <500ms | <2s | <5s |
| **MCP tool call** (direct) | <100ms | <300ms | <500ms |
| **Graph traversal** | <50ms | <150ms | <300ms |
| **Vector search** | <100ms | <250ms | <500ms |
| **Webhook processing** | <200ms | <500ms | <1s |
| **Entity extraction** | <300ms | <800ms | <2s |
| **WebSocket update** | <50ms | <100ms | <200ms |

### Throughput Targets

| Metric | Target |
|--------|--------|
| **Concurrent users** | 10,000+ |
| **Requests per second** | 1,000+ |
| **Chat messages/minute** | 5,000+ |
| **MCP tool calls/minute** | 10,000+ |
| **Webhook events/minute** | 2,000+ |
| **Graph nodes** | 10M+ |
| **Vector embeddings** | 50M+ |

### Resource Utilization

| Resource | Target | Alert Threshold |
|----------|--------|-----------------|
| **CPU** | 60-70% average | >85% for 5 min |
| **Memory** | 70-80% average | >90% for 2 min |
| **Disk I/O** | <70% utilization | >85% for 5 min |
| **Network** | <60% bandwidth | >80% for 5 min |
| **Database connections** | <60% pool | >80% pool |

## Deployment Architecture

### Local Development

```
Docker Compose Stack:
- Frontend (Vite dev server)
- Backend (FastAPI with hot reload)
- Neo4j (single instance)
- PostgreSQL (single instance)
- Redis (single instance)
```

### Production Deployment

```
Kubernetes Cluster:
- Ingress (NGINX)
- Frontend (static files via CDN)
- Backend (replicated pods)
- Orchestrator (replicated pods)
- Agent workers (horizontal pod autoscaling)
- Neo4j (StatefulSet, 3 replicas)
- PostgreSQL (StatefulSet, streaming replication)
- Redis (StatefulSet, cluster mode)
```

## Monitoring and Observability

### Metrics Collection

- **Application Metrics**: Prometheus
- **Logging**: Structured JSON logs to stdout
- **Tracing**: OpenTelemetry distributed tracing
- **Visualization**: Grafana dashboards

### Key Metrics

1. **Request Metrics**: Rate, duration, errors
2. **Agent Metrics**: Spawn rate, execution time, failure rate
3. **Memory Metrics**: Read/write latency, cache hit rate
4. **Database Metrics**: Query time, connection pool, index usage
5. **LLM Metrics**: API latency, token usage, cost
6. **Business Metrics**: Active users, messages, entities created

## Error Handling

### Error Recovery Strategy

```mermaid
graph TD
    Error[Error Occurs] --> Type{Error Type}
    
    Type -->|Transient| Retry[Exponential Backoff Retry]
    Type -->|Permanent| Fallback[Fallback Strategy]
    
    Retry -->|Success| Complete[Complete Operation]
    Retry -->|Max Retries| Fallback
    
    Fallback -->|Cache| Cached[Return Cached Data]
    Fallback -->|Degraded| Partial[Partial Response]
    Fallback -->|Fail| User[User-Friendly Error]
    
    Cached --> Complete
    Partial --> Complete
    User --> Log[Log + Alert]
```

### Retry Policies

| Service | Max Retries | Backoff | Timeout |
|---------|-------------|---------|---------|
| **Gemini API** | 3 | Exponential (1s, 2s, 4s) | 30s |
| **Groq API** | 3 | Exponential (1s, 2s, 4s) | 30s |
| **Neo4j** | 5 | Linear (500ms) | 10s |
| **PostgreSQL** | 5 | Linear (500ms) | 10s |
| **Redis** | 3 | Exponential (100ms, 200ms, 400ms) | 5s |
| **Webhooks** | 10 | Exponential (1m, 5m, 15m, 1h) | 24h |

## Related Documentation

- [API Reference](./api-reference.md) - Detailed API specifications
- [Backend](./backend.md) - Implementation details
- [Agents](./agents.md) - Agent system architecture
- [Memory](./memory.md) - Memory layer design
- [Databases](./databases.md) - Database configuration and optimization
