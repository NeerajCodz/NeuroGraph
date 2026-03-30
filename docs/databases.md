# Database Configuration Documentation

## Overview

NeuroGraph uses three database systems, each serving a specific purpose in the architecture:

- **Neo4j**: Graph database for entities and relationships
- **PostgreSQL with pgvector**: Vector embeddings and structured data
- **Upstash Redis**: Caching and task queue

All databases are containerized using Docker for consistent deployment across environments.

## Neo4j Setup

### Docker Configuration

```yaml
# docker-compose.yml
neo4j:
  image: neo4j:5.16
  container_name: neurograph-neo4j
  environment:
    NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
    NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
    NEO4J_dbms_memory_heap_initial__size: 1G
    NEO4J_dbms_memory_heap_max__size: 2G
    NEO4J_dbms_memory_pagecache_size: 1G
    NEO4J_dbms_default__listen__address: 0.0.0.0
    NEO4J_dbms_connector_bolt_listen__address: 0.0.0.0:7687
    NEO4J_dbms_connector_http_listen__address: 0.0.0.0:7474
  ports:
    - "7474:7474"  # HTTP (Neo4j Browser)
    - "7687:7687"  # Bolt protocol
  volumes:
    - neo4j-data:/data
    - neo4j-logs:/logs
    - neo4j-import:/import
    - neo4j-plugins:/plugins
  networks:
    - neurograph-network
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "${NEO4J_PASSWORD}", "RETURN 1"]
    interval: 30s
    timeout: 10s
    retries: 3
```

### Configuration File

```conf
# neo4j.conf
# Memory settings
dbms.memory.heap.initial_size=1G
dbms.memory.heap.max_size=2G
dbms.memory.pagecache.size=1G

# Network settings
dbms.default_listen_address=0.0.0.0
dbms.connector.bolt.enabled=true
dbms.connector.http.enabled=true

# Security settings
dbms.security.auth_enabled=true
dbms.security.procedures.unrestricted=apoc.*,gds.*

# Performance settings
dbms.transaction.timeout=30s
dbms.lock.acquisition.timeout=30s
dbms.checkpoint.interval.time=15m

# Logging
dbms.logs.query.enabled=true
dbms.logs.query.threshold=1s
```

### Python Driver Setup

```python
# app/services/neo4j-service.py
from neo4j import GraphDatabase
from typing import List, Dict, Any

class Neo4jService:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    async def create_entity(
        self,
        name: str,
        entity_type: str,
        properties: Dict[str, Any],
        layer: str
    ) -> str:
        """
        Create an entity node in Neo4j.
        """
        async with self.driver.session() as session:
            result = await session.execute_write(
                self._create_entity_tx,
                name, entity_type, properties, layer
            )
            return result
    
    @staticmethod
    def _create_entity_tx(tx, name, entity_type, properties, layer):
        query = """
        CREATE (e:Entity {
            id: randomUUID(),
            name: $name,
            type: $type,
            layer: $layer,
            created_at: datetime(),
            updated_at: datetime(),
            properties: $properties
        })
        RETURN e.id as id
        """
        result = tx.run(
            query,
            name=name,
            type=entity_type,
            layer=layer,
            properties=properties
        )
        return result.single()["id"]
    
    async def find_entities(
        self,
        entity_type: str = None,
        layer: str = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find entities with optional filters.
        """
        async with self.driver.session() as session:
            result = await session.execute_read(
                self._find_entities_tx,
                entity_type, layer, limit
            )
            return result
    
    @staticmethod
    def _find_entities_tx(tx, entity_type, layer, limit):
        query = """
        MATCH (e:Entity)
        WHERE ($type IS NULL OR e.type = $type)
          AND ($layer IS NULL OR e.layer = $layer)
        RETURN e
        LIMIT $limit
        """
        result = tx.run(query, type=entity_type, layer=layer, limit=limit)
        return [dict(record["e"]) for record in result]
```

### Neo4j Initialization Script

```python
# scripts/init-neo4j.py
from neo4j import GraphDatabase

def initialize_neo4j(uri, user, password):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    with driver.session() as session:
        # Create constraints
        session.run("CREATE CONSTRAINT entity_id_unique IF NOT EXISTS ON (e:Entity) ASSERT e.id IS UNIQUE")
        
        # Create indexes
        session.run("CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)")
        session.run("CREATE INDEX entity_layer IF NOT EXISTS FOR (e:Entity) ON (e.layer)")
        session.run("CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)")
        session.run("CREATE INDEX entity_created IF NOT EXISTS FOR (e:Entity) ON (e.created_at)")
        
        # Create full-text index
        session.run("""
            CREATE FULLTEXT INDEX entity_search IF NOT EXISTS
            FOR (e:Entity)
            ON EACH [e.name, e.description]
        """)
        
        print("Neo4j initialization complete")
    
    driver.close()

if __name__ == "__main__":
    initialize_neo4j(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="your-password"
    )
```

## PostgreSQL + pgvector Setup

### Docker Configuration

```yaml
# docker-compose.yml
postgres:
  image: pgvector/pgvector:pg16
  container_name: neurograph-postgres
  environment:
    POSTGRES_DB: neurograph
    POSTGRES_USER: neurograph
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    POSTGRES_INITDB_ARGS: "-E UTF8 --locale=en_US.UTF-8"
  ports:
    - "5432:5432"
  volumes:
    - postgres-data:/var/lib/postgresql/data
    - ./scripts/init-postgres.sql:/docker-entrypoint-initdb.d/init.sql
  networks:
    - neurograph-network
  restart: unless-stopped
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U neurograph -d neurograph"]
    interval: 30s
    timeout: 10s
    retries: 3
  command:
    - "postgres"
    - "-c"
    - "max_connections=200"
    - "-c"
    - "shared_buffers=256MB"
    - "-c"
    - "effective_cache_size=1GB"
    - "-c"
    - "maintenance_work_mem=64MB"
    - "-c"
    - "checkpoint_completion_target=0.9"
    - "-c"
    - "wal_buffers=16MB"
    - "-c"
    - "default_statistics_target=100"
    - "-c"
    - "random_page_cost=1.1"
```

### Schema Definitions

```sql
-- scripts/init-postgres.sql

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Organizations table
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Organization members table
CREATE TABLE organization_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, user_id)
);

-- Memory table with vector embeddings
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content TEXT NOT NULL,
    embedding vector(768),  -- Gemini embedding dimension
    layer VARCHAR(50) NOT NULL CHECK (layer IN ('personal', 'shared', 'organization')),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    scope_id UUID,  -- Project or team ID for shared layer
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    confidence FLOAT DEFAULT 0.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_memories_user_id ON memories(user_id);
CREATE INDEX idx_memories_layer ON memories(layer);
CREATE INDEX idx_memories_organization_id ON memories(organization_id);
CREATE INDEX idx_memories_created_at ON memories(created_at);
CREATE INDEX idx_memories_confidence ON memories(confidence);

-- Vector similarity index (HNSW for fast approximate search)
CREATE INDEX idx_memories_embedding ON memories USING hnsw (embedding vector_cosine_ops);

-- Composite index for common queries
CREATE INDEX idx_memories_layer_user ON memories(layer, user_id);

-- Full-text search
CREATE INDEX idx_memories_content_fts ON memories USING gin(to_tsvector('english', content));

-- Conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    mode VARCHAR(50) NOT NULL CHECK (mode IN ('general', 'organization')),
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_memories_updated_at BEFORE UPDATE ON memories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Python Connection Setup

```python
# app/services/postgres-service.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from pgvector.sqlalchemy import Vector
from typing import List, Dict, Any

class PostgresService:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def insert_memory(
        self,
        content: str,
        embedding: List[float],
        layer: str,
        user_id: str,
        scope_id: str = None,
        organization_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Insert a memory with vector embedding.
        """
        async with self.SessionLocal() as session:
            query = """
            INSERT INTO memories (content, embedding, layer, user_id, scope_id, organization_id, metadata)
            VALUES (:content, :embedding, :layer, :user_id, :scope_id, :organization_id, :metadata)
            RETURNING id
            """
            result = await session.execute(
                query,
                {
                    "content": content,
                    "embedding": embedding,
                    "layer": layer,
                    "user_id": user_id,
                    "scope_id": scope_id,
                    "organization_id": organization_id,
                    "metadata": metadata or {}
                }
            )
            await session.commit()
            return result.scalar()
    
    async def vector_search(
        self,
        embedding: List[float],
        layer: str,
        user_id: str,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search.
        """
        async with self.SessionLocal() as session:
            query = """
            SELECT
                id,
                content,
                layer,
                confidence,
                created_at,
                1 - (embedding <=> :embedding::vector) as similarity_score
            FROM memories
            WHERE layer = :layer
              AND user_id = :user_id
              AND 1 - (embedding <=> :embedding::vector) > :threshold
            ORDER BY embedding <=> :embedding::vector
            LIMIT :limit
            """
            result = await session.execute(
                query,
                {
                    "embedding": embedding,
                    "layer": layer,
                    "user_id": user_id,
                    "threshold": similarity_threshold,
                    "limit": limit
                }
            )
            return [dict(row) for row in result]
```

## Upstash Redis Configuration

### Docker Configuration (Local Development)

```yaml
# docker-compose.yml
redis:
  image: redis:7-alpine
  container_name: neurograph-redis
  command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 512mb --maxmemory-policy allkeys-lru
  ports:
    - "6379:6379"
  volumes:
    - redis-data:/data
  networks:
    - neurograph-network
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
    interval: 30s
    timeout: 10s
    retries: 3
```

### Production (Upstash Cloud)

For production, use Upstash Redis cloud service:

```python
# app/config.py
REDIS_URL = os.getenv("UPSTASH_REDIS_URL")  # Get from Upstash dashboard
REDIS_TOKEN = os.getenv("UPSTASH_REDIS_TOKEN")
```

### Python Client Setup

```python
# app/services/redis-service.py
import redis.asyncio as redis
from typing import Any, Optional
import json

class RedisService:
    def __init__(self, redis_url: str, password: str = None):
        self.client = redis.from_url(
            redis_url,
            password=password,
            decode_responses=True
        )
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        """
        value = await self.client.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ex: int = None  # Expiration in seconds
    ) -> bool:
        """
        Set value in cache with optional expiration.
        """
        serialized = json.dumps(value)
        return await self.client.set(key, serialized, ex=ex)
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        """
        return await self.client.delete(key) > 0
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists.
        """
        return await self.client.exists(key) > 0
    
    async def increment(self, key: str) -> int:
        """
        Increment counter.
        """
        return await self.client.incr(key)
    
    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration on key.
        """
        return await self.client.expire(key, seconds)
    
    async def push_to_queue(self, queue_name: str, item: Any) -> int:
        """
        Push item to queue (list).
        """
        serialized = json.dumps(item)
        return await self.client.rpush(queue_name, serialized)
    
    async def pop_from_queue(
        self,
        queue_name: str,
        timeout: int = 0
    ) -> Optional[Any]:
        """
        Pop item from queue (blocking).
        """
        result = await self.client.blpop(queue_name, timeout=timeout)
        if result:
            _, value = result
            return json.loads(value)
        return None
```

### Cache Patterns

```python
# app/utils/cache.py
from functools import wraps
from app.services.redis-service import RedisService

def cache_result(ttl: int = 300):
    """
    Decorator to cache function results.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            redis = RedisService()
            
            # Generate cache key
            cache_key = f"cache:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Check cache
            cached = await redis.get(cache_key)
            if cached is not None:
                return cached
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await redis.set(cache_key, result, ex=ttl)
            
            return result
        return wrapper
    return decorator

# Usage
@cache_result(ttl=300)
async def get_user_data(user_id: str):
    # Expensive database query
    return await db.query(user_id)
```

## Backup and Recovery

### Neo4j Backup

```bash
#!/bin/bash
# scripts/backup-neo4j.sh

BACKUP_DIR="/backups/neo4j"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/neurograph-$DATE.dump"

# Create backup directory
mkdir -p $BACKUP_DIR

# Stop Neo4j
docker-compose stop neo4j

# Perform backup
docker exec neurograph-neo4j neo4j-admin dump \
    --database=neo4j \
    --to=/backups/neurograph.dump

# Copy backup from container
docker cp neurograph-neo4j:/backups/neurograph.dump $BACKUP_FILE

# Start Neo4j
docker-compose start neo4j

# Compress backup
gzip $BACKUP_FILE

# Remove old backups (keep last 7 days)
find $BACKUP_DIR -name "*.dump.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

### PostgreSQL Backup

```bash
#!/bin/bash
# scripts/backup-postgres.sh

BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/neurograph-$DATE.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup
docker exec neurograph-postgres pg_dump \
    -U neurograph \
    -d neurograph \
    -F c \
    -f /tmp/backup.dump

# Copy backup from container
docker cp neurograph-postgres:/tmp/backup.dump $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Remove old backups (keep last 7 days)
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

### Restore Scripts

```bash
#!/bin/bash
# scripts/restore-neo4j.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: ./restore-neo4j.sh <backup-file>"
    exit 1
fi

# Stop Neo4j
docker-compose stop neo4j

# Decompress if needed
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip $BACKUP_FILE
    BACKUP_FILE=${BACKUP_FILE%.gz}
fi

# Copy backup to container
docker cp $BACKUP_FILE neurograph-neo4j:/backups/restore.dump

# Restore backup
docker exec neurograph-neo4j neo4j-admin load \
    --from=/backups/restore.dump \
    --database=neo4j \
    --force

# Start Neo4j
docker-compose start neo4j

echo "Restore completed"
```

## Connection Pooling

### PostgreSQL Connection Pool

```python
# app/core/database.py
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,  # Number of connections to maintain
    max_overflow=10,  # Additional connections when pool is full
    pool_timeout=30,  # Timeout waiting for connection
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Verify connections before using
)
```

### Neo4j Connection Pool

```python
# app/services/neo4j-service.py
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD),
    max_connection_lifetime=3600,
    max_connection_pool_size=50,
    connection_acquisition_timeout=30
)
```

### Redis Connection Pool

```python
# app/services/redis-service.py
import redis.asyncio as redis

pool = redis.ConnectionPool.from_url(
    REDIS_URL,
    max_connections=50,
    decode_responses=True
)

client = redis.Redis(connection_pool=pool)
```

## Monitoring

### Database Health Checks

```python
# app/api/routes/health.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/health/databases")
async def check_databases():
    """
    Check health of all databases.
    """
    return {
        "postgres": await check_postgres_health(),
        "neo4j": await check_neo4j_health(),
        "redis": await check_redis_health()
    }

async def check_postgres_health():
    try:
        async with postgres.SessionLocal() as session:
            await session.execute("SELECT 1")
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

async def check_neo4j_health():
    try:
        async with neo4j.driver.session() as session:
            await session.run("RETURN 1")
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

async def check_redis_health():
    try:
        await redis.client.ping()
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

## Related Documentation

- [Architecture](./architecture.md) - Database role in system architecture
- [Backend](./backend.md) - Backend integration with databases
- [Graph](./graph.md) - Neo4j schema and queries
- [Memory](./memory.md) - Memory system using databases
