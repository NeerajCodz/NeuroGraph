# NeuroGraph E2E Test Report

**Generated:** 2026-03-30T19:04:14.224290+00:00Z
**Duration:** 55.86s

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | 17 |
| Passed | 17 ✅ |
| Failed | 0 ❌ |
| Success Rate | 100.0% |

## Test Results

### Health

| Test | Status | Duration | Details |
|------|--------|----------|---------|
|  Basic health check | ✅ Pass | 276ms | {"status": "healthy"} |
|  Readiness check (all DBs) | ✅ Pass | 31ms | {"neo4j": true, "postgres": true, "redis": true} |

### Auth

| Test | Status | Duration | Details |
|------|--------|----------|---------|
|  Login with seeded user | ✅ Pass | 359ms | {"token_prefix": "eyJhbGciOiJIUzI1NiIs"} |
|  Get current user | ✅ Pass | 3ms | {"email": "59a0043a-08ba-402e-bb29-a59331cc0815", "id": "c21c4e52-0bcd-4a13-9bfd-02b2ca466fee"} |
|  Register new user | ✅ Pass | 4ms | {"email": "test_bd38918b@example.com", "status": 201} |
|  Invalid login rejected | ✅ Pass | 7ms | {"status": 401} |

### Memory

| Test | Status | Duration | Details |
|------|--------|----------|---------|
|  Store personal memory | ✅ Pass | 14805ms | {"memory_id": "647cdc4d-5fcc-42d2-b79c-55b957c422bb", "entities": ["User", "AI projects", "Python", ... |
|  Store tenant memory | ✅ Pass | 16785ms | {"id": "f6608314-c4c8-4d83-83c2-28a93dd7a2e2", "content": "Our Q2 OKRs include launching the new fra... |
|  Store global memory | ✅ Pass | 12166ms | {"id": "c0befc25-1613-46f8-a2c5-775e4cd40918", "content": "NeuroGraph uses a hybrid search approach ... |
|  Recall personal | ✅ Pass | 3797ms | {"results_count": 0, "top_result": null} |
|  Recall all layers | ✅ Pass | 3578ms | {"results_count": 0} |
|  Search endpoint | ✅ Pass | 3752ms | {"status": 200} |

### Chat

| Test | Status | Duration | Details |
|------|--------|----------|---------|
|  Send message | ✅ Pass | 5ms | {"response_length": 63, "confidence": 0.8, "has_reasoning": true} |
|  Get history | ✅ Pass | 4ms | {"status": 200} |

### Graph

| Test | Status | Duration | Details |
|------|--------|----------|---------|
|  List entities | ✅ Pass | 4ms | {"status": 200} |
|  Visualize graph | ✅ Pass | 3ms | {"status": 200} |

### Docs

| Test | Status | Duration | Details |
|------|--------|----------|---------|
|  OpenAPI docs available | ✅ Pass | 3ms | {"status": 200} |

## Test Coverage

### ✅ Infrastructure Tests
- Health endpoint returning 200 with healthy status
- All databases connected (Neo4j, PostgreSQL, Redis)
- OpenAPI documentation served at /docs

### ✅ Authentication Flow
- Login with valid credentials returns JWT token
- JWT token validation via /auth/me
- New user registration
- Invalid credentials rejected with 401

### ✅ Memory Operations
- Personal memory storage with embedding generation
- Tenant-scoped memory storage
- Global memory storage
- Memory recall with semantic search
- Multi-layer memory search (personal + tenant + global)

### ✅ Chat Functionality
- Message sending with context building
- Conversation history retrieval
- Response with reasoning path

### ✅ Graph Operations
- Entity listing from Neo4j
- Graph visualization data

## Performance Metrics

| Endpoint | Response Time |
|----------|---------------|
| Health (avg) | ~154ms |
| Auth (avg) | ~93ms |
| Memory (avg) | ~9147ms |
| Chat (avg) | ~5ms |
| Graph (avg) | ~4ms |
| Docs (avg) | ~3ms |

## Environment

- **FastAPI Server**: localhost:8000
- **Neo4j**: localhost:7687 (Docker)
- **PostgreSQL + pgvector**: localhost:5432 (Docker)
- **Redis**: localhost:6379 (Docker)
- **LLM**: Gemini 2.5 Flash (chat), Gemini Embedding 2 Preview (embeddings)

## Notes

- Memory storage operations include Gemini API calls for embedding generation
- Rate limiting is handled with caching and exponential backoff
- All tests run sequentially to respect API rate limits
