# NeuroGraph

**An Agentic Context Engine with Explainable Graph Memory**

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Development](#development)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## Overview

NeuroGraph is an enterprise-grade AI system that combines graph-based memory, autonomous agents, and explainable reasoning to dynamically build context for LLM applications. Unlike traditional RAG (Retrieval-Augmented Generation) systems that rely on static vector searches, NeuroGraph actively decides what information is relevant, explains its reasoning process, and evolves its knowledge over time.

The system implements a three-layer memory architecture (Personal, Organization, Global) with automatic conflict detection, temporal decay, and full provenance tracking for every stored fact.

## Key Features

### Three-Layer Memory Architecture

- **Personal Layer**: Private user memory, isolated per user
- **Organization Layer**: Shared team knowledge, scoped to tenant
- **Global Layer**: Public world knowledge, write-protected (confidence > 0.85)

### Explainable Reasoning

- Every relationship stored with reason, timestamp, and confidence score
- Traceable reasoning paths through the knowledge graph
- Temporal decay algorithm for confidence degradation
- Full provenance tracking (source, author, storage method)

### Agentic Orchestration

- Dynamic agent spawning based on query complexity
- Parallel and sequential execution strategies
- Stateless agent design for horizontal scalability
- Event-driven architecture with priority queueing

### MCP-Native Integration

- Model Context Protocol (MCP) server for direct LLM integration
- Plug into Claude Desktop, Cursor, Cline, or any MCP client
- Transport-agnostic: stdio for local clients, HTTP/SSE for remote
- No middleware required for MCP clients

### Hybrid Intelligence

- Internal graph memory (Neo4j) for structured knowledge
- External web search (Tavily) for current information
- Vector similarity search (pgvector) for semantic matching
- Context assembly with token budget management

### Real-Time Visualization

- D3.js-powered interactive graph visualization
- WebSocket updates for live graph changes
- Reasoning path highlighting
- Conflict detection visualization (red edges)

## Architecture

```mermaid
graph TB
    subgraph "User Interfaces"
        UI[Chat Interface<br/>React + Vite]
        MCP[MCP Clients<br/>Claude, Cursor]
        WH[Webhooks<br/>Slack, GitHub, Gmail]
    end
    
    subgraph "Processing Layer"
        ORC[Orchestrator<br/>Groq Llama 3.3<br/>Chat Only]
        MCPS[MCP Server<br/>FastAPI<br/>Direct Access]
        EB[Event Bus<br/>Upstash Redis<br/>Priority Queue]
    end
    
    subgraph "Agent Layer"
        MM[Memory Manager]
        CB[Context Builder]
        WS[Web Surfer]
        IA[Import Agent]
        CR[Conflict Resolver]
        RA[Reminder Agent]
    end
    
    subgraph "Data Layer"
        NEO[(Neo4j<br/>Graph DB<br/>Docker)]
        PG[(PostgreSQL<br/>pgvector<br/>Docker)]
        REDIS[(Upstash Redis<br/>Cache + Queue)]
    end
    
    UI -->|User Query| ORC
    MCP -->|Tool Call| MCPS
    WH -->|Event| EB
    
    ORC -->|Plan + Spawn| EB
    MCPS -->|Direct| MM
    
    EB --> MM
    EB --> WS
    EB --> IA
    
    MM --> CB
    MM --> CR
    MM --> RA
    
    MM --> NEO
    MM --> PG
    CR --> NEO
    RA --> REDIS
    
    style ORC fill:#f9f,stroke:#333
    style MCPS fill:#9ff,stroke:#333
    style MM fill:#ff9,stroke:#333
```

### Design Principles

1. **Separation of Orchestration**: Chat interface uses orchestrator for dynamic planning; MCP clients bypass orchestrator for direct access
2. **Event-Driven Processing**: All triggers (user, integration, LLM) normalize to standard events
3. **Stateless Agents**: Agents spawn, execute, return results, and terminate with no persistent state
4. **Graph as Source of Truth**: All memory operations flow through Neo4j for consistency
5. **Layer Isolation**: Memory layers enforce strict access controls and tenant boundaries

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/NeerajCodz/neurograph.git
cd neurograph
```

2. Copy environment templates:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

3. Edit `.env` files with your API keys:
   - `GEMINI_API_KEY`: Google Gemini API key
   - `GROQ_API_KEY`: Groq API key (optional, for orchestrator)
   - `TAVILY_API_KEY`: Tavily search API key
   - `UPSTASH_REDIS_URL` and `UPSTASH_REDIS_TOKEN`: Upstash Redis credentials

4. Start all services:

```bash
docker-compose -f docker/docker-compose.yml up -d
```

5. Access the application:
   - Chat Interface: http://localhost:3000
   - API Documentation: http://localhost:8000/docs
   - Neo4j Browser: http://localhost:7474 (username: neo4j, password: from .env)

### Using the Chat Interface

1. Navigate to http://localhost:3000
2. Log in or create an account
3. Select memory mode:
   - **General**: Uses personal memory only
   - **Organization**: Select organization from dropdown (uses personal + organization layers)
4. Toggle **Global Memory** in settings to include/exclude public knowledge
5. Start chatting - memory is handled automatically

### Using MCP Clients

Configure your MCP client (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "neurograph": {
      "command": "python",
      "args": ["-m", "neurograph.mcp.server"],
      "env": {
        "NEO4J_URI": "neo4j://localhost:7687",
        "NEO4J_PASSWORD": "your-password",
        "POSTGRES_URI": "postgresql://user:pass@localhost:5432/neurograph",
        "TENANT_ID": "your-org-id",
        "USER_ID": "your-user-id"
      }
    }
  }
}
```

Available MCP tools:
- `recall(query)` - Retrieve relevant memory
- `remember(entity1, relation, entity2, reason)` - Store new fact
- `explain(node_id)` - Get provenance of a fact
- `forget(entity1, relation, entity2)` - Delete a relationship
- `switch_mode(mode)` - Change active memory layer
- `memory_status()` - Get memory statistics
- `resolve_conflict(conflict_id, resolution)` - Resolve memory conflicts
- `import_context(source, content)` - Bulk import from integrations
- `search_assets(query)` - Search stored files and documents
- `explain_last_response()` - Get full reasoning trail

## Documentation

Comprehensive documentation is available in the `/docs` folder:

| Document | Description |
|----------|-------------|
| [Architecture](./docs/architecture.md) | System design, components, data flows |
| [API Reference](./docs/api-reference.md) | REST API and MCP tool specifications |
| [MCP](./docs/mcp.md) | MCP server setup and client integration |
| [Frontend](./docs/frontend.md) | React application, D3.js visualization |
| [Backend](./docs/backend.md) | FastAPI services, Docker configuration |
| [Agents](./docs/agents.md) | Agent system, orchestration, lifecycle |
| [Memory](./docs/memory.md) | Three-layer architecture, scoring, decay |
| [Graph](./docs/graph.md) | Neo4j schema, queries, indexing |
| [Databases](./docs/databases.md) | Neo4j, PostgreSQL, Upstash configuration |
| [RAG](./docs/rag.md) | Vector embeddings, similarity search, hybrid retrieval |
| [Models](./docs/models.md) | Gemini and Groq integration |
| [Webhooks](./docs/webhooks.md) | Integration endpoints, event normalization |
| [Integrations](./docs/integrations.md) | Slack, GitHub, Gmail, and other third-party connections |

## Technology Stack

### Backend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | Python FastAPI | High-performance async API server |
| MCP Server | Python MCP SDK | Model Context Protocol implementation |
| Graph Database | Neo4j (Docker) | Knowledge graph storage |
| Vector Store | PostgreSQL + pgvector (Docker) | Semantic similarity search |
| Cache/Queue | Upstash Redis | Event bus and distributed cache |
| LLM (Main) | Google Gemini | Primary reasoning model |
| LLM (Orchestrator) | Groq Llama 3.3 | Fast agent planning |
| Embeddings | Gemini Embeddings | Vector generation |
| Web Search | Tavily API | External knowledge retrieval |

### Frontend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Build Tool | Vite | Fast development and build |
| Framework | React 18 | UI component library |
| Language | TypeScript | Type-safe development |
| State Management | Zustand | Lightweight state management |
| Visualization | D3.js | Interactive graph rendering |
| Styling | Tailwind CSS | Utility-first CSS |
| Real-time | WebSocket | Live graph updates |

### Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Containerization | Docker + Docker Compose | Service orchestration |
| Reverse Proxy | Nginx | Request routing and SSL termination |
| Monitoring | Prometheus + Grafana | Metrics and dashboards |
| Tracing | Jaeger | Distributed request tracing |
| Logging | Structured JSON logs | Centralized log aggregation |

## Project Structure

```
neurograph/
├── backend/                 # Python FastAPI backend
│   ├── src/
│   │   ├── api/            # REST API endpoints
│   │   ├── mcp/            # MCP server and tools
│   │   ├── agents/         # Agent system
│   │   ├── memory/         # Memory management
│   │   ├── rag/            # RAG pipeline
│   │   ├── models/         # LLM integration
│   │   ├── integrations/   # Third-party connections
│   │   ├── webhooks/       # Webhook handlers
│   │   └── events/         # Event system
│   └── tests/              # Backend tests
│
├── frontend/                # React frontend
│   ├── src/
│   │   ├── pages/          # Page components
│   │   ├── components/     # Reusable components
│   │   ├── stores/         # Zustand stores
│   │   ├── hooks/          # Custom React hooks
│   │   └── services/       # API clients
│   └── tests/              # Frontend tests
│
├── docker/                  # Docker configurations
│   ├── docker-compose.yml
│   ├── neo4j/
│   ├── postgres/
│   └── nginx/
│
├── docs/                    # Documentation
└── scripts/                 # Utility scripts
```

See [FOLDER_STRUCTURE.md](./FOLDER_STRUCTURE.md) for complete project structure.

## Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Database Migrations

```bash
# Neo4j
python backend/scripts/migrate.py --database neo4j --version latest

# PostgreSQL
python backend/scripts/migrate.py --database postgres --version latest
```

## Deployment

### Local Development

```bash
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up
```

### Production

```bash
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d
```

### Environment Variables

Required environment variables for production:

```bash
# Backend
NEO4J_URI=neo4j+s://production-instance.databases.neo4j.io
NEO4J_PASSWORD=<strong-password>
POSTGRES_URI=postgresql://user:pass@postgres-host:5432/neurograph
UPSTASH_REDIS_URL=https://production.upstash.io
UPSTASH_REDIS_TOKEN=<token>
GEMINI_API_KEY=<key>
GROQ_API_KEY=<key>
TAVILY_API_KEY=<key>
SECRET_KEY=<strong-secret-key>
ENVIRONMENT=production

# Frontend
VITE_API_URL=https://api.yourcompany.com
VITE_WS_URL=wss://api.yourcompany.com/ws
```

## Use Cases

### Fraud Detection
Track device-user relationships across time to identify suspicious patterns and explain detection reasoning.

### Cybersecurity Analysis
Map threat actors, affected systems, and remediation actions with full audit trail and temporal tracking.

### Knowledge Management
Maintain organizational memory that explains decision provenance, tracks context changes, and surfaces relevant historical information.

### Personalized AI Assistants
Build context-aware assistants that remember user preferences, adapt to organizational knowledge, and explain their reasoning.

### Healthcare Decision Support
Track patient history, treatment relationships, and outcomes with explainability and confidence scoring for clinical decisions.

## Contributing

Contributions are welcome. Please follow these guidelines:

1. **Code Style**: Follow PEP 8 for Python, ESLint configuration for TypeScript
2. **Naming Convention**: lowercase-hyphen-separated for files, PascalCase for classes, snake_case for functions
3. **Testing**: All new features must include unit tests and integration tests
4. **Documentation**: Update relevant documentation for any feature changes
5. **Commit Messages**: Use conventional commits format (feat:, fix:, docs:, etc.)

## License

MIT License. See [LICENSE](./LICENSE) for details.

## Support

- **Documentation**: See `/docs` folder
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: support@neurograph.dev

## Roadmap

- Multi-agent collaboration (agents spawning other agents)
- What-if simulation mode for scenario planning
- Real-time learning feedback loop
- Domain-specific fine-tuning for specialized use cases
- Mobile applications (iOS/Android)
- Additional integrations (Jira, Linear, Confluence)
- GraphQL API endpoint
- SSO/SAML authentication support

---

**NeuroGraph** - Memory that thinks, explains, and evolves.
