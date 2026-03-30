# NeuroGraph Backend

Agentic context engine with explainable graph memory.

## Features

- **Three-layer memory system**: Personal, Tenant, Global
- **Hybrid search**: Vector (pgvector) + Graph (Neo4j)
- **MCP server**: Direct memory access for AI assistants
- **REST API**: Full-featured chat and memory endpoints

## Quick Start

```bash
# Start infrastructure
docker compose up -d neo4j postgres redis

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Start server
uvicorn src.main:app --reload
```

## Architecture

```
src/
├── core/       # Config, logging, exceptions
├── db/         # Neo4j, PostgreSQL, Redis drivers
├── memory/     # Three-layer memory system
├── models/     # Gemini & Groq clients
├── rag/        # Hybrid search pipeline
├── agents/     # Orchestrator & spawner
├── mcp/        # MCP server with tools
├── api/        # REST routes & middleware
└── webhooks/   # Integration handlers
```

## Environment

Copy `.env.example` to `.env` and configure API keys.
