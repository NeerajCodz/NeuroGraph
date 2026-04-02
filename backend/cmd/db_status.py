#!/usr/bin/env python3
"""
Production database status checker using environment variables only.
Usage: python -m cmd.db_status
"""

import asyncio
import os
import sys

import asyncpg
from neo4j import GraphDatabase

async def main():
    """Check database status using environment variables."""
    
    # Get credentials from environment
    postgres_url = os.getenv('DATABASE_URL')
    neo4j_uri = os.getenv('NEO4J_URI')
    neo4j_username = os.getenv('NEO4J_USERNAME', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD')
    
    if not postgres_url:
        print("❌ Missing DATABASE_URL environment variable")
        sys.exit(1)
    
    print("📊 Checking database status...")
    
    # Check Postgres
    try:
        conn = await asyncpg.connect(postgres_url)
        
        user_count = await conn.fetchval("SELECT COUNT(*) FROM auth.users")
        memory_count = await conn.fetchval("SELECT COUNT(*) FROM memory.embeddings")
        edge_count = await conn.fetchval("SELECT COUNT(*) FROM memory.canvas_edges")
        
        print(f"\n✅ Postgres Connection: Success")
        print(f"   Users: {user_count}")
        print(f"   Memories: {memory_count}")
        print(f"   Edges: {edge_count}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Postgres Connection: Failed")
        print(f"   Error: {e}")
    
    # Check Neo4j
    if neo4j_uri and neo4j_password:
        try:
            driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
            
            with driver.session() as session:
                node_count = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
                rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
                user_count = session.run("MATCH (u:User) RETURN count(u) as count").single()["count"]
                memory_count = session.run("MATCH (m:Memory) RETURN count(m) as count").single()["count"]
            
            print(f"\n✅ Neo4j Connection: Success")
            print(f"   Total Nodes: {node_count}")
            print(f"   Total Relationships: {rel_count}")
            print(f"   Users: {user_count}")
            print(f"   Memories: {memory_count}")
            
            driver.close()
            
        except Exception as e:
            print(f"❌ Neo4j Connection: Failed")
            print(f"   Error: {e}")
    else:
        print("\n⚠️  Neo4j: Skipped (missing NEO4J_URI or NEO4J_PASSWORD)")

if __name__ == "__main__":
    asyncio.run(main())