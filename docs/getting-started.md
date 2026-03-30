# NeuroGraph - Getting Started Guide

**Complete Setup and Deployment Guide**

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Structure](#project-structure)
3. [Initial Setup](#initial-setup)
4. [Environment Configuration](#environment-configuration)
5. [Running Locally](#running-locally)
6. [Running with Docker](#running-with-docker)
7. [Accessing the System](#accessing-the-system)
8. [First Steps](#first-steps)
9. [Troubleshooting](#troubleshooting)
10. [Next Steps](#next-steps)

---

## Prerequisites

### Required Software

- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Python** 3.11+ (for local development)
- **Node.js** 18+ (for frontend development)
- **Git** 2.0+

### Required API Keys

1. **Google Gemini API Key** - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Groq API Key** (Optional) - Get from [Groq Console](https://console.groq.com/)
3. **Tavily API Key** (Optional) - Get from [Tavily](https://tavily.com/)
4. **Upstash Redis** (Required) - Get from [Upstash Console](https://console.upstash.com/)

### System Requirements

- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: 10GB free disk space
- **OS**: Linux, macOS, or Windows with WSL2

---

## Project Structure

```
neurograph/
├── backend/              # Python FastAPI backend
├── frontend/             # React + Vite frontend
├── docker/               # Docker configurations
├── docs/                 # Documentation (you are here)
├── scripts/              # Utility scripts
├── README.md
└── FOLDER_STRUCTURE.md   # Complete folder structure
```

See [FOLDER_STRUCTURE.md](../FOLDER_STRUCTURE.md) for complete project layout.

---

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourorg/neurograph.git
cd neurograph
```

### 2. Run Setup Script

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

This script will:
- Create `.env` files from templates
- Install Python dependencies
- Install Node.js dependencies
- Create necessary directories
- Initialize database schemas

### 3. Manual Setup (Alternative)

If the setup script fails, follow these steps manually:

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Return to root
cd ..
```

---

## Environment Configuration

### Backend Environment (.env)

Create `backend/.env` from template:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:

```bash
# ==========================================
# DATABASE CONFIGURATION
# ==========================================

# Neo4j Graph Database
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-strong-password-here

# PostgreSQL + pgvector
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=neurograph
POSTGRES_PASSWORD=your-strong-password-here
POSTGRES_DB=neurograph

# Upstash Redis (REQUIRED - get from console.upstash.com)
UPSTASH_REDIS_URL=https://your-instance.upstash.io
UPSTASH_REDIS_TOKEN=your-upstash-token-here

# ==========================================
# LLM API KEYS
# ==========================================

# Google Gemini (REQUIRED - get from makersuite.google.com)
GEMINI_API_KEY=your-gemini-api-key-here

# Groq (Optional - for orchestrator, can use Gemini instead)
GROQ_API_KEY=your-groq-api-key-here

# Tavily Search (Optional - for web search agent)
TAVILY_API_KEY=your-tavily-api-key-here

# ==========================================
# APPLICATION SETTINGS
# ==========================================

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
DEBUG=true

# Security
SECRET_KEY=generate-a-strong-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=10080  # 7 days

# MCP Server
MCP_TRANSPORT=stdio  # stdio or sse
MCP_PORT=8000

# API Server
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# ==========================================
# MEMORY CONFIGURATION
# ==========================================

# Layer defaults
DEFAULT_LAYER=personal
GLOBAL_WRITE_THRESHOLD=0.85

# Scoring weights
SEMANTIC_WEIGHT=0.35
HOP_WEIGHT=0.25
CENTRALITY_WEIGHT=0.20
TEMPORAL_WEIGHT=0.20

# Token budgets
TOTAL_TOKEN_BUDGET=4000
GRAPH_TOKEN_BUDGET=2000
ASSET_TOKEN_BUDGET=800
INTEGRATION_TOKEN_BUDGET=600
SEARCH_TOKEN_BUDGET=400
SYSTEM_TOKEN_BUDGET=200

# Temporal decay
DECAY_RATE=0.05  # e^(-0.05 * days)

# Graph traversal
MAX_HOP_DISTANCE=3
MAX_NODES_PER_QUERY=200
```

### Frontend Environment (.env)

Create `frontend/.env` from template:

```bash
cp frontend/.env.example frontend/.env
```

Edit `frontend/.env`:

```bash
# API endpoints
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws

# Environment
VITE_ENVIRONMENT=development

# Feature flags
VITE_ENABLE_GRAPH_VIZ=true
VITE_ENABLE_WEB_SEARCH=true
VITE_ENABLE_INTEGRATIONS=true
```

### Generate Secret Key

```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output to `SECRET_KEY` in `backend/.env`.

---

## Running Locally

### Option 1: Development Mode (Recommended)

Start all services with hot reload:

```bash
./scripts/dev.sh
```

This starts:
- Backend FastAPI server (port 8000)
- Frontend Vite dev server (port 3000)
- Neo4j (port 7687, 7474)
- PostgreSQL (port 5432)

### Option 2: Manual Start

**Terminal 1 - Databases:**
```bash
docker-compose -f docker/docker-compose.yml up neo4j postgres
```

**Terminal 2 - Backend:**
```bash
cd backend
source venv/bin/activate
python src/main.py
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm run dev
```

### Option 3: Docker Compose (Full Stack)

```bash
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up
```

---

## Running with Docker

### Development with Docker

```bash
# Start all services
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### Production with Docker

```bash
# Build images
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml build

# Start services
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml logs -f
```

### Docker Compose Services

| Service | Port | Description |
|---------|------|-------------|
| backend | 8000 | FastAPI API server |
| frontend | 3000 | React frontend |
| neo4j | 7474, 7687 | Graph database + browser |
| postgres | 5432 | PostgreSQL + pgvector |
| nginx | 80, 443 | Reverse proxy (prod only) |

---

## Accessing the System

### Web Interfaces

| Interface | URL | Credentials |
|-----------|-----|-------------|
| Chat Interface | http://localhost:3000 | Sign up on first visit |
| API Documentation | http://localhost:8000/docs | N/A (Swagger UI) |
| Neo4j Browser | http://localhost:7474 | neo4j / (from .env) |

### API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# API version
curl http://localhost:8000/version

# Chat endpoint (requires auth)
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "mode": "personal"}'
```

### MCP Client Setup

**Claude Desktop:**

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or  
`%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "neurograph": {
      "command": "python",
      "args": ["-m", "neurograph.mcp.server"],
      "env": {
        "NEO4J_URI": "neo4j://localhost:7687",
        "NEO4J_PASSWORD": "your-password",
        "POSTGRES_URI": "postgresql://neurograph:your-password@localhost:5432/neurograph",
        "UPSTASH_REDIS_URL": "https://your-instance.upstash.io",
        "UPSTASH_REDIS_TOKEN": "your-token",
        "GEMINI_API_KEY": "your-key",
        "USER_ID": "your-user-id",
        "TENANT_ID": "your-org-id"
      }
    }
  }
}
```

Restart Claude Desktop. You should see "neurograph" in the MCP tools list.

**Cursor:**

Similar configuration in Cursor settings panel under MCP Servers.

---

## First Steps

### 1. Create an Account

Navigate to http://localhost:3000 and sign up:

```
Email: your-email@example.com
Password: (strong password)
```

### 2. Select Memory Mode

In the left sidebar:
- **General**: Personal memory only
- **Organization**: Create or select organization

### 3. Configure Global Memory

In settings, toggle **Global Memory** on/off.

### 4. Start Chatting

Ask your first question:

```
User: Remember that I prefer dark mode
AI: Stored in personal memory: You → prefers → dark mode
```

```
User: What do I prefer?
AI: Based on my memory, you prefer dark mode (confidence: 0.95, stored 1 minute ago)
```

### 5. Explore the Graph

Click "Graph View" to see visual representation of your memory.

### 6. Test MCP Integration

If using Claude Desktop:

```
User: Use the neurograph recall tool to remember my preferences
Claude: [calls recall tool]
Based on your NeuroGraph memory, you prefer dark mode.
```

---

## Troubleshooting

### Database Connection Issues

**Problem:** `Connection refused to Neo4j`

**Solution:**
```bash
# Check if Neo4j is running
docker ps | grep neo4j

# View Neo4j logs
docker-compose logs neo4j

# Restart Neo4j
docker-compose restart neo4j
```

**Problem:** `FATAL: password authentication failed for user "neurograph"`

**Solution:**
- Check `POSTGRES_PASSWORD` in `.env` matches `docker/postgres/init.sql`
- Rebuild PostgreSQL container:
  ```bash
  docker-compose down -v
  docker-compose up -d postgres
  ```

### API Key Issues

**Problem:** `Invalid API key for Gemini`

**Solution:**
- Verify key at https://makersuite.google.com/app/apikey
- Ensure no extra spaces in `.env` file
- Restart backend after changing `.env`

### Port Conflicts

**Problem:** `Port 8000 already in use`

**Solution:**
```bash
# Find process using port
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process or change port in .env
API_PORT=8001
```

### Frontend Build Issues

**Problem:** `Module not found: D3.js`

**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Docker Issues

**Problem:** `Cannot connect to Docker daemon`

**Solution:**
```bash
# Start Docker Desktop (macOS/Windows)
# Or start Docker service (Linux)
sudo systemctl start docker
```

**Problem:** `Permission denied while trying to connect`

**Solution:**
```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker
```

### MCP Client Issues

**Problem:** Claude Desktop doesn't show neurograph tools

**Solution:**
1. Check JSON syntax in config file
2. Verify Python path: `which python`
3. Check Claude Desktop logs:
   - macOS: `~/Library/Logs/Claude/`
   - Windows: `%APPDATA%\Claude\logs\`

### Memory/Performance Issues

**Problem:** High memory usage

**Solution:**
```bash
# Limit Neo4j memory in docker-docker-compose.yml
NEO4J_server_memory_heap_initial__size=512m
NEO4J_server_memory_heap_max__size=2G

# Limit PostgreSQL shared buffers
shared_buffers=256MB
```

---

## Next Steps

### Learning Resources

1. **Documentation**
   - [Architecture](./architecture.md) - System design
   - [Pipeline](./pipeline.md) - Hybrid retrieval explained
   - [API Reference](./api-reference.md) - REST API docs
   - [MCP](./mcp.md) - MCP integration guide

2. **Tutorials**
   - [Memory Layers Tutorial](./memory.md#tutorial)
   - [Graph Querying Guide](./graph.md#querying)
   - [Integration Setup](./integrations.md)

3. **Advanced Topics**
   - [Agent Development](./agents.md)
   - [Custom RAG Pipelines](./rag.md)
   - [Scaling Guide](./architecture.md#scaling-strategy)

### Development Workflow

1. **Make Changes**
   - Backend: Edit files in `backend/src/`, hot reload active
   - Frontend: Edit files in `frontend/src/`, HMR active

2. **Run Tests**
   ```bash
   # Backend tests
   cd backend
   pytest
   
   # Frontend tests
   cd frontend
   npm test
   ```

3. **Format Code**
   ```bash
   # Python
   black backend/src
   
   # TypeScript
   cd frontend
   npm run format
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push
   ```

### Production Deployment

See [Backend Documentation](./backend.md#production-deployment) for:
- Cloud deployment (AWS, GCP, Azure)
- Kubernetes setup
- SSL/TLS configuration
- Backup and recovery
- Monitoring and logging

### Community

- **GitHub Issues**: Report bugs or request features
- **Discussions**: Ask questions and share ideas
- **Contributing**: See CONTRIBUTING.md

---

## Summary

You now have a fully functional NeuroGraph installation:

✅ Backend API running on port 8000  
✅ Frontend running on port 3000  
✅ Neo4j graph database operational  
✅ PostgreSQL with pgvector ready  
✅ MCP server configured (optional)  
✅ Memory system initialized  

**Next:** Start using the chat interface or integrate with your MCP client!

For issues, see [Troubleshooting](#troubleshooting) or open a GitHub issue.
