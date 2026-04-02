# Backend Commands

Production command-line tools that use environment variables only. Safe for version control.

## Environment Variables

These commands require the following environment variables:

```bash
DATABASE_URL=postgresql://user:pass@host:port/db
NEO4J_URI=neo4j+s://host:port
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

## Commands

### Database Status
Check status of both databases:
```bash
python -m cmd.db_status
```

### Sync Neo4j
Sync data from Postgres to Neo4j:
```bash
python -m cmd.sync_neo4j
```

## Usage in Production

From your deployment environment:

```bash
# Set environment variables (via .env, secrets, etc.)
export DATABASE_URL=postgresql://...
export NEO4J_URI=neo4j+s://...
export NEO4J_PASSWORD=...

# Run commands
cd backend
python -m cmd.db_status
python -m cmd.sync_neo4j
```

All commands use only environment variables - no hardcoded credentials.