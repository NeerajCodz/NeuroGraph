#!/usr/bin/env python3
"""
Production Neo4j sync command using environment variables only.
Usage: python -m cmd.sync_neo4j
"""

import asyncio
import os
import sys
from typing import Dict, List

import asyncpg
from neo4j import GraphDatabase

async def main():
    """Sync Postgres data to Neo4j using environment variables."""
    
    # Get credentials from environment
    postgres_url = os.getenv('DATABASE_URL')
    neo4j_uri = os.getenv('NEO4J_URI')
    neo4j_username = os.getenv('NEO4J_USERNAME', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD')
    
    if not all([postgres_url, neo4j_uri, neo4j_password]):
        print("❌ Missing required environment variables:")
        print("   DATABASE_URL, NEO4J_URI, NEO4J_PASSWORD")
        sys.exit(1)
    
    print("🔄 Starting Neo4j sync from Postgres...")
    print(f"📊 Postgres: {postgres_url.split('@')[1] if '@' in postgres_url else 'configured'}")
    print(f"🔗 Neo4j: {neo4j_uri}")
    
    try:
        # Connect to Postgres
        conn = await asyncpg.connect(postgres_url)
        print("✅ Connected to Postgres")
        
        # Connect to Neo4j
        neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
        print("✅ Connected to Neo4j")
        
        # Get counts
        user_count = await conn.fetchval("SELECT COUNT(*) FROM auth.users")
        memory_count = await conn.fetchval("SELECT COUNT(*) FROM memory.embeddings")
        edge_count = await conn.fetchval("SELECT COUNT(*) FROM memory.canvas_edges")
        
        print(f"\n📊 Postgres Data:")
        print(f"   Users: {user_count}")
        print(f"   Memories: {memory_count}")
        print(f"   Edges: {edge_count}")
        
        # Clear Neo4j
        with neo4j_driver.session() as session:
            print("\n🗑️ Clearing Neo4j...")
            result = session.run("MATCH (n) DETACH DELETE n RETURN count(n) as deleted")
            deleted_count = result.single()["deleted"]
            print(f"   Deleted {deleted_count} nodes")
        
        # Sync Users
        print("\n👥 Syncing Users...")
        users = await conn.fetch("SELECT id, email, full_name FROM auth.users")
        
        with neo4j_driver.session() as session:
            for user in users:
                session.run("""
                    CREATE (u:User {
                        id: $user_id,
                        email: $email,
                        full_name: $full_name
                    })
                """, user_id=str(user['id']), email=user['email'], full_name=user['full_name'])
        
        print(f"   Created {len(users)} User nodes")
        
        # Sync Memories
        print("\n🧠 Syncing Memories...")
        memories = await conn.fetch("""
            SELECT id, node_id, content, layer, user_id, tenant_id, created_at
            FROM memory.embeddings
            ORDER BY created_at
        """)
        
        batch_size = 100
        memory_batches = [memories[i:i + batch_size] for i in range(0, len(memories), batch_size)]
        
        for i, batch in enumerate(memory_batches):
            with neo4j_driver.session() as session:
                for memory in batch:
                    # Create Memory node
                    session.run("""
                        CREATE (m:Memory {
                            id: $memory_id,
                            node_id: $node_id,
                            content: $content,
                            layer: $layer,
                            created_at: $created_at
                        })
                    """, 
                        memory_id=str(memory['id']),
                        node_id=memory['node_id'],
                        content=memory['content'],
                        layer=memory['layer'],
                        created_at=memory['created_at'].isoformat()
                    )
                    
                    # Create relationship to User
                    if memory['user_id']:
                        session.run("""
                            MATCH (u:User {id: $user_id})
                            MATCH (m:Memory {id: $memory_id})
                            CREATE (u)-[:HAS_MEMORY]->(m)
                        """, user_id=str(memory['user_id']), memory_id=str(memory['id']))
            
            print(f"   Batch {i+1}/{len(memory_batches)} complete ({len(batch)} memories)")
        
        print(f"   Created {len(memories)} Memory nodes")
        
        # Sync Edges
        print("\n🔗 Syncing Memory Edges...")
        edges = await conn.fetch("""
            SELECT source_memory_id, target_memory_id, relationship_type, strength
            FROM memory.canvas_edges
        """)
        
        edge_batches = [edges[i:i + batch_size] for i in range(0, len(edges), batch_size)]
        created_edges = 0
        
        for i, batch in enumerate(edge_batches):
            with neo4j_driver.session() as session:
                for edge in batch:
                    try:
                        result = session.run("""
                            MATCH (source:Memory {id: $source_id})
                            MATCH (target:Memory {id: $target_id})
                            CREATE (source)-[:CONNECTS {
                                type: $relationship_type,
                                strength: $strength
                            }]->(target)
                            RETURN count(*) as created
                        """,
                            source_id=str(edge['source_memory_id']),
                            target_id=str(edge['target_memory_id']),
                            relationship_type=edge['relationship_type'],
                            strength=edge['strength']
                        )
                        created_edges += result.single()["created"]
                    except Exception as e:
                        print(f"   Warning: Failed to create edge {edge['source_memory_id']}->{edge['target_memory_id']}: {e}")
            
            print(f"   Batch {i+1}/{len(edge_batches)} complete")
        
        print(f"   Created {created_edges} memory connections")
        
        # Final verification
        with neo4j_driver.session() as session:
            neo4j_users = session.run("MATCH (u:User) RETURN count(u) as count").single()["count"]
            neo4j_memories = session.run("MATCH (m:Memory) RETURN count(m) as count").single()["count"]
            neo4j_relationships = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
        
        print(f"\n✅ Neo4j Sync Complete!")
        print(f"   Users: {neo4j_users}")
        print(f"   Memories: {neo4j_memories}")
        print(f"   Relationships: {neo4j_relationships}")
        
    except Exception as e:
        print(f"❌ Error during sync: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        await conn.close()
        neo4j_driver.close()
        print("\n🔌 Connections closed")

if __name__ == "__main__":
    asyncio.run(main())