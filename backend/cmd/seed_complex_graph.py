#!/usr/bin/env python3
"""
Complex graph memory seeding for NeuroGraph.
Creates 30+ interconnected memory nodes with multiple relationship types.
"""

import asyncio
import json
import os
import sys
from typing import Dict, List, Tuple

import asyncpg
from neo4j import GraphDatabase

# Memory concepts with rich interconnections
MEMORY_CONCEPTS = {
    # Technology Stack
    "tech_python": {"content": "Python is a versatile programming language", "domain": "technology"},
    "tech_fastapi": {"content": "FastAPI is a modern Python web framework", "domain": "technology"},
    "tech_neo4j": {"content": "Neo4j is a graph database", "domain": "technology"},
    "tech_postgres": {"content": "PostgreSQL is a relational database", "domain": "technology"},
    "tech_redis": {"content": "Redis provides in-memory caching", "domain": "technology"},
    "tech_docker": {"content": "Docker enables containerization", "domain": "technology"},
    "tech_kubernetes": {"content": "Kubernetes orchestrates containers", "domain": "technology"},
    
    # AI/ML Concepts
    "ai_llm": {"content": "Large Language Models understand natural language", "domain": "ai"},
    "ai_embedding": {"content": "Embeddings convert text to vector representations", "domain": "ai"},
    "ai_rag": {"content": "Retrieval Augmented Generation improves AI responses", "domain": "ai"},
    "ai_vector_search": {"content": "Vector search finds semantically similar content", "domain": "ai"},
    "ai_transformer": {"content": "Transformers are the architecture behind modern LLMs", "domain": "ai"},
    "ai_attention": {"content": "Attention mechanisms help models focus on relevant information", "domain": "ai"},
    
    # Architecture Patterns
    "arch_microservices": {"content": "Microservices decompose applications into small services", "domain": "architecture"},
    "arch_event_driven": {"content": "Event-driven architecture uses events for communication", "domain": "architecture"},
    "arch_caching": {"content": "Caching strategies improve application performance", "domain": "architecture"},
    "arch_load_balancing": {"content": "Load balancing distributes traffic across servers", "domain": "architecture"},
    "arch_api_gateway": {"content": "API gateways provide unified access to microservices", "domain": "architecture"},
    
    # Security Concepts
    "sec_oauth": {"content": "OAuth provides secure authorization framework", "domain": "security"},
    "sec_jwt": {"content": "JWT tokens enable stateless authentication", "domain": "security"},
    "sec_encryption": {"content": "Encryption protects data confidentiality", "domain": "security"},
    "sec_rate_limiting": {"content": "Rate limiting prevents API abuse", "domain": "security"},
    "sec_cors": {"content": "CORS controls cross-origin resource sharing", "domain": "security"},
    
    # Business Concepts
    "biz_user_experience": {"content": "User experience determines product success", "domain": "business"},
    "biz_scalability": {"content": "Scalability enables handling increased load", "domain": "business"},
    "biz_performance": {"content": "Performance optimization improves user satisfaction", "domain": "business"},
    "biz_reliability": {"content": "Reliability ensures system availability", "domain": "business"},
    "biz_monitoring": {"content": "Monitoring provides system observability", "domain": "business"},
    
    # Data Concepts
    "data_indexing": {"content": "Database indexing speeds up query performance", "domain": "data"},
    "data_partitioning": {"content": "Data partitioning improves large dataset handling", "domain": "data"},
    "data_replication": {"content": "Data replication ensures availability and backup", "domain": "data"},
    "data_consistency": {"content": "Data consistency maintains accuracy across systems", "domain": "data"},
}

# Rich relationship patterns with multiple connection types
RELATIONSHIP_PATTERNS = [
    # Technology relationships
    ("tech_python", "tech_fastapi", "IMPLEMENTS", 0.9),
    ("tech_fastapi", "tech_postgres", "CONNECTS_TO", 0.8),
    ("tech_fastapi", "tech_redis", "USES", 0.7),
    ("tech_fastapi", "tech_neo4j", "INTEGRATES_WITH", 0.8),
    ("tech_docker", "tech_kubernetes", "ORCHESTRATED_BY", 0.9),
    ("tech_postgres", "tech_docker", "CONTAINERIZED_IN", 0.7),
    ("tech_redis", "tech_docker", "CONTAINERIZED_IN", 0.7),
    ("tech_neo4j", "tech_docker", "CONTAINERIZED_IN", 0.7),
    
    # AI/ML relationships
    ("ai_llm", "ai_embedding", "GENERATES", 0.9),
    ("ai_embedding", "ai_vector_search", "ENABLES", 0.9),
    ("ai_vector_search", "ai_rag", "SUPPORTS", 0.8),
    ("ai_rag", "ai_llm", "ENHANCES", 0.9),
    ("ai_transformer", "ai_llm", "POWERS", 0.9),
    ("ai_attention", "ai_transformer", "COMPONENT_OF", 0.9),
    ("ai_rag", "tech_postgres", "RETRIEVES_FROM", 0.7),
    ("ai_embedding", "tech_redis", "CACHED_IN", 0.6),
    
    # Architecture relationships
    ("arch_microservices", "arch_event_driven", "COMBINES_WITH", 0.8),
    ("arch_microservices", "arch_api_gateway", "MANAGED_BY", 0.8),
    ("arch_load_balancing", "arch_api_gateway", "IMPLEMENTED_IN", 0.7),
    ("arch_caching", "tech_redis", "IMPLEMENTED_USING", 0.9),
    ("arch_microservices", "tech_docker", "DEPLOYED_WITH", 0.8),
    ("arch_microservices", "tech_kubernetes", "ORCHESTRATED_BY", 0.8),
    
    # Security relationships
    ("sec_oauth", "sec_jwt", "IMPLEMENTS", 0.8),
    ("sec_jwt", "tech_fastapi", "SECURED_BY", 0.8),
    ("sec_encryption", "tech_postgres", "PROTECTS", 0.9),
    ("sec_rate_limiting", "arch_api_gateway", "ENFORCED_BY", 0.8),
    ("sec_cors", "tech_fastapi", "CONFIGURED_IN", 0.7),
    ("sec_oauth", "arch_api_gateway", "HANDLES_AUTH", 0.8),
    
    # Business relationships  
    ("biz_user_experience", "biz_performance", "DEPENDS_ON", 0.9),
    ("biz_performance", "arch_caching", "IMPROVED_BY", 0.8),
    ("biz_performance", "arch_load_balancing", "ENHANCED_BY", 0.8),
    ("biz_scalability", "arch_microservices", "ACHIEVED_WITH", 0.9),
    ("biz_reliability", "data_replication", "ENSURED_BY", 0.8),
    ("biz_monitoring", "biz_reliability", "SUPPORTS", 0.9),
    ("biz_scalability", "tech_kubernetes", "ENABLED_BY", 0.8),
    
    # Data relationships
    ("data_indexing", "tech_postgres", "OPTIMIZES", 0.9),
    ("data_partitioning", "biz_scalability", "ENABLES", 0.8),
    ("data_replication", "data_consistency", "CHALLENGES", 0.7),
    ("data_consistency", "tech_postgres", "MAINTAINED_BY", 0.8),
    ("data_indexing", "biz_performance", "IMPROVES", 0.8),
    
    # Cross-domain relationships
    ("ai_llm", "biz_user_experience", "ENHANCES", 0.8),
    ("tech_python", "ai_llm", "IMPLEMENTS", 0.7),
    ("arch_event_driven", "ai_rag", "SUPPORTS_REALTIME", 0.6),
    ("sec_encryption", "ai_embedding", "PROTECTS", 0.7),
    ("biz_monitoring", "tech_fastapi", "OBSERVES", 0.7),
    ("data_partitioning", "arch_microservices", "ALIGNS_WITH", 0.6),
    
    # Multi-hop connections for complex traversal
    ("tech_python", "biz_performance", "CONTRIBUTES_TO", 0.6),
    ("ai_transformer", "biz_user_experience", "IMPROVES", 0.7),
    ("sec_oauth", "biz_reliability", "STRENGTHENS", 0.6),
    ("arch_caching", "data_consistency", "AFFECTS", 0.5),
    ("tech_kubernetes", "biz_monitoring", "REQUIRES", 0.7),
    ("ai_vector_search", "arch_caching", "BENEFITS_FROM", 0.6),
]

async def main():
    """Seed complex interconnected graph memory."""
    
    # Get credentials from environment
    postgres_url = os.getenv('DATABASE_URL')
    neo4j_uri = os.getenv('NEO4J_URI')
    neo4j_username = os.getenv('NEO4J_USERNAME', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD')
    
    if not all([postgres_url, neo4j_uri, neo4j_password]):
        print("❌ Missing required environment variables:")
        print("   DATABASE_URL, NEO4J_URI, NEO4J_PASSWORD")
        sys.exit(1)
    
    print("🔄 Seeding complex graph memory...")
    print(f"📊 Concepts: {len(MEMORY_CONCEPTS)}")
    print(f"🔗 Relationships: {len(RELATIONSHIP_PATTERNS)}")
    
    try:
        # Connect to Postgres
        conn = await asyncpg.connect(postgres_url)
        print("✅ Connected to Postgres")
        
        # Connect to Neo4j
        neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
        print("✅ Connected to Neo4j")
        
        # Get user for memory ownership
        users = await conn.fetch("SELECT id, email FROM auth.users WHERE email = 'frank@neurograph.ai'")
        if not users:
            print("❌ User frank@neurograph.ai not found")
            return
        
        user_id = users[0]['id']
        print(f"👤 Using user: {users[0]['email']}")
        
        # Add memories to Postgres first
        print("\n🧠 Adding concept memories to Postgres...")
        memory_id_map = {}
        
        for concept_key, concept_data in MEMORY_CONCEPTS.items():
            # Insert memory into embeddings table
            memory_id = await conn.fetchval("""
                INSERT INTO memory.embeddings (node_id, content, layer, user_id, confidence, embedding)
                VALUES ($1, $2, 'personal', $3, 0.95, $4)
                RETURNING id
            """, 
                concept_key, 
                concept_data['content'], 
                user_id,
                [0.0] * 768  # Placeholder embedding vector
            )
            memory_id_map[concept_key] = memory_id
        
        print(f"   Created {len(MEMORY_CONCEPTS)} memory records")
        
        # Add relationships to Postgres canvas_edges
        print("\n🔗 Adding relationships to Postgres...")
        edge_count = 0
        
        for source_key, target_key, relationship_type, strength in RELATIONSHIP_PATTERNS:
            if source_key in memory_id_map and target_key in memory_id_map:
                await conn.execute("""
                    INSERT INTO memory.canvas_edges (source_memory_id, target_memory_id, relationship_type, strength, user_id)
                    VALUES ($1, $2, $3, $4, $5)
                """, 
                    memory_id_map[source_key],
                    memory_id_map[target_key], 
                    relationship_type,
                    strength,
                    user_id
                )
                edge_count += 1
        
        print(f"   Created {edge_count} relationship records")
        
        # Sync to Neo4j with rich structure
        print("\n🔄 Syncing to Neo4j...")
        with neo4j_driver.session() as session:
            # Clear existing complex memories
            session.run("MATCH (m:Memory) WHERE m.node_id STARTS WITH 'tech_' OR m.node_id STARTS WITH 'ai_' OR m.node_id STARTS WITH 'arch_' OR m.node_id STARTS WITH 'sec_' OR m.node_id STARTS WITH 'biz_' OR m.node_id STARTS WITH 'data_' DETACH DELETE m")
            
            # Create concept nodes with domain labels
            for concept_key, concept_data in MEMORY_CONCEPTS.items():
                memory_id = memory_id_map[concept_key]
                domain = concept_data['domain']
                
                session.run(f"""
                    CREATE (m:Memory:{domain.title()} {{
                        id: $memory_id,
                        node_id: $node_id,
                        content: $content,
                        domain: $domain,
                        layer: 'personal',
                        created_at: datetime()
                    }})
                """, 
                    memory_id=str(memory_id),
                    node_id=concept_key,
                    content=concept_data['content'],
                    domain=domain
                )
            
            print(f"   Created {len(MEMORY_CONCEPTS)} Neo4j concept nodes")
            
            # Create rich relationships
            relationship_count = 0
            for source_key, target_key, relationship_type, strength in RELATIONSHIP_PATTERNS:
                if source_key in memory_id_map and target_key in memory_id_map:
                    try:
                        session.run(f"""
                            MATCH (source:Memory {{node_id: $source_id}})
                            MATCH (target:Memory {{node_id: $target_id}})
                            CREATE (source)-[:{relationship_type} {{
                                strength: $strength,
                                type: $relationship_type,
                                created_at: datetime()
                            }}]->(target)
                        """,
                            source_id=source_key,
                            target_id=target_key,
                            strength=strength,
                            relationship_type=relationship_type
                        )
                        relationship_count += 1
                    except Exception as e:
                        print(f"   Warning: Failed to create relationship {source_key}->{target_key}: {e}")
            
            print(f"   Created {relationship_count} Neo4j relationships")
            
            # Add domain connections (connect concepts within domains)
            print("\n🌐 Creating domain clusters...")
            domains = set(concept['domain'] for concept in MEMORY_CONCEPTS.values())
            
            for domain in domains:
                domain_concepts = [k for k, v in MEMORY_CONCEPTS.items() if v['domain'] == domain]
                # Create SAME_DOMAIN relationships within each domain
                for i, concept1 in enumerate(domain_concepts):
                    for concept2 in domain_concepts[i+1:]:
                        session.run("""
                            MATCH (c1:Memory {node_id: $concept1})
                            MATCH (c2:Memory {node_id: $concept2})
                            CREATE (c1)-[:SAME_DOMAIN {
                                strength: 0.4,
                                type: 'SAME_DOMAIN',
                                created_at: datetime()
                            }]->(c2)
                        """, concept1=concept1, concept2=concept2)
            
            # Final verification with rich analytics
            result = session.run("""
                MATCH (n:Memory)
                OPTIONAL MATCH (n)-[r]->()
                RETURN 
                    count(DISTINCT n) as nodes,
                    count(r) as relationships,
                    collect(DISTINCT labels(n)) as node_types
            """)
            
            stats = result.single()
            
            # Get domain distribution
            domain_stats = session.run("""
                MATCH (n:Memory)
                RETURN n.domain as domain, count(n) as count
                ORDER BY count DESC
            """)
            
            print(f"\n✅ Complex Graph Memory Created!")
            print(f"   Total Nodes: {stats['nodes']}")
            print(f"   Total Relationships: {stats['relationships']}")
            print(f"   Node Types: {stats['node_types']}")
            print(f"\n📊 Domain Distribution:")
            
            for record in domain_stats:
                domain = record['domain']
                count = record['count']
                print(f"   {domain.title()}: {count} concepts")
            
            # Show relationship types
            rel_types = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as relationship_type, count(r) as count
                ORDER BY count DESC
            """)
            
            print(f"\n🔗 Relationship Types:")
            for record in rel_types:
                rel_type = record['relationship_type']
                count = record['count']
                print(f"   {rel_type}: {count}")
        
    except Exception as e:
        print(f"❌ Error during complex seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        await conn.close()
        neo4j_driver.close()
        print("\n🔌 Connections closed")
        print("\n🎯 Complex graph memory ready for multi-hop traversal!")

if __name__ == "__main__":
    asyncio.run(main())