#!/usr/bin/env python3
"""
Complex graph seeding using proper /graph endpoints.
Creates rich interconnected entity structure with multiple relationship types.
"""

import json
import requests
import time
from typing import Dict, List, Tuple

BASE_URL = "https://neuro-graph-be.vercel.app"

# Rich entity concepts organized by domain
ENTITIES = {
    # Technology Domain
    "python": {"name": "Python", "type": "ProgrammingLanguage", "domain": "technology", "properties": {"popularity": "high", "paradigm": "multi"}},
    "fastapi": {"name": "FastAPI", "type": "WebFramework", "domain": "technology", "properties": {"language": "python", "async": True}},
    "neo4j": {"name": "Neo4j", "type": "Database", "domain": "technology", "properties": {"type": "graph", "query_language": "cypher"}},
    "postgresql": {"name": "PostgreSQL", "type": "Database", "domain": "technology", "properties": {"type": "relational", "acid": True}},
    "redis": {"name": "Redis", "type": "Database", "domain": "technology", "properties": {"type": "cache", "in_memory": True}},
    "docker": {"name": "Docker", "type": "Container", "domain": "technology", "properties": {"purpose": "containerization"}},
    "kubernetes": {"name": "Kubernetes", "type": "Orchestrator", "domain": "technology", "properties": {"purpose": "container_orchestration"}},
    "vercel": {"name": "Vercel", "type": "Platform", "domain": "technology", "properties": {"type": "deployment", "serverless": True}},
    
    # AI/ML Domain
    "llm": {"name": "Large Language Model", "type": "AIModel", "domain": "ai", "properties": {"capability": "text_generation", "training": "unsupervised"}},
    "embedding": {"name": "Text Embedding", "type": "AITechnique", "domain": "ai", "properties": {"output": "vector", "purpose": "semantic_representation"}},
    "rag": {"name": "Retrieval Augmented Generation", "type": "AIPattern", "domain": "ai", "properties": {"combines": "retrieval_generation"}},
    "vector_search": {"name": "Vector Search", "type": "SearchMethod", "domain": "ai", "properties": {"similarity": "cosine", "purpose": "semantic_search"}},
    "transformer": {"name": "Transformer", "type": "Architecture", "domain": "ai", "properties": {"mechanism": "attention", "application": "nlp"}},
    "attention": {"name": "Attention Mechanism", "type": "Technique", "domain": "ai", "properties": {"focus": "relevant_information"}},
    
    # Architecture Domain
    "microservices": {"name": "Microservices", "type": "Pattern", "domain": "architecture", "properties": {"granularity": "service", "coupling": "loose"}},
    "event_driven": {"name": "Event-Driven Architecture", "type": "Pattern", "domain": "architecture", "properties": {"communication": "asynchronous"}},
    "api_gateway": {"name": "API Gateway", "type": "Component", "domain": "architecture", "properties": {"purpose": "unified_access"}},
    "load_balancer": {"name": "Load Balancer", "type": "Component", "domain": "architecture", "properties": {"purpose": "traffic_distribution"}},
    "cache_strategy": {"name": "Caching Strategy", "type": "Pattern", "domain": "architecture", "properties": {"purpose": "performance"}},
    
    # Security Domain
    "oauth": {"name": "OAuth", "type": "Protocol", "domain": "security", "properties": {"purpose": "authorization", "version": "2.0"}},
    "jwt": {"name": "JWT Token", "type": "Standard", "domain": "security", "properties": {"stateless": True, "format": "json"}},
    "encryption": {"name": "Encryption", "type": "Technique", "domain": "security", "properties": {"purpose": "confidentiality"}},
    "rate_limiting": {"name": "Rate Limiting", "type": "Protection", "domain": "security", "properties": {"prevents": "abuse"}},
    "cors": {"name": "CORS", "type": "Mechanism", "domain": "security", "properties": {"controls": "cross_origin_access"}},
    
    # Business Domain
    "user_experience": {"name": "User Experience", "type": "Concept", "domain": "business", "properties": {"impact": "adoption"}},
    "scalability": {"name": "Scalability", "type": "Quality", "domain": "business", "properties": {"handles": "growth"}},
    "performance": {"name": "Performance", "type": "Quality", "domain": "business", "properties": {"affects": "satisfaction"}},
    "reliability": {"name": "Reliability", "type": "Quality", "domain": "business", "properties": {"ensures": "availability"}},
    "monitoring": {"name": "Monitoring", "type": "Practice", "domain": "business", "properties": {"provides": "observability"}},
    
    # Data Domain
    "indexing": {"name": "Database Indexing", "type": "Optimization", "domain": "data", "properties": {"improves": "query_performance"}},
    "partitioning": {"name": "Data Partitioning", "type": "Strategy", "domain": "data", "properties": {"handles": "large_datasets"}},
    "replication": {"name": "Data Replication", "type": "Strategy", "domain": "data", "properties": {"ensures": "availability"}},
    "consistency": {"name": "Data Consistency", "type": "Principle", "domain": "data", "properties": {"maintains": "accuracy"}},
}

# Rich relationship patterns with multiple types
RELATIONSHIPS = [
    # Technology relationships
    ("python", "fastapi", "IMPLEMENTS", "Python implements FastAPI framework", 0.9),
    ("fastapi", "postgresql", "CONNECTS_TO", "FastAPI connects to PostgreSQL", 0.8),
    ("fastapi", "redis", "USES", "FastAPI uses Redis for caching", 0.7),
    ("fastapi", "neo4j", "INTEGRATES_WITH", "FastAPI integrates with Neo4j", 0.8),
    ("docker", "kubernetes", "ORCHESTRATED_BY", "Docker containers orchestrated by Kubernetes", 0.9),
    ("postgresql", "docker", "CONTAINERIZED_IN", "PostgreSQL containerized in Docker", 0.8),
    ("redis", "docker", "CONTAINERIZED_IN", "Redis containerized in Docker", 0.8),
    ("vercel", "docker", "SUPPORTS", "Vercel supports Docker deployments", 0.7),
    
    # AI/ML relationships
    ("llm", "embedding", "GENERATES", "LLM generates text embeddings", 0.9),
    ("embedding", "vector_search", "ENABLES", "Embeddings enable vector search", 0.9),
    ("vector_search", "rag", "SUPPORTS", "Vector search supports RAG", 0.8),
    ("rag", "llm", "ENHANCES", "RAG enhances LLM capabilities", 0.9),
    ("transformer", "llm", "POWERS", "Transformer architecture powers LLM", 0.9),
    ("attention", "transformer", "COMPONENT_OF", "Attention is component of Transformer", 0.9),
    ("rag", "postgresql", "RETRIEVES_FROM", "RAG retrieves from PostgreSQL", 0.7),
    ("embedding", "redis", "CACHED_IN", "Embeddings cached in Redis", 0.6),
    
    # Architecture relationships
    ("microservices", "event_driven", "COMBINES_WITH", "Microservices combine with event-driven", 0.8),
    ("microservices", "api_gateway", "MANAGED_BY", "Microservices managed by API gateway", 0.8),
    ("load_balancer", "api_gateway", "IMPLEMENTED_IN", "Load balancer implemented in API gateway", 0.7),
    ("cache_strategy", "redis", "IMPLEMENTED_USING", "Caching strategy implemented using Redis", 0.9),
    ("microservices", "docker", "DEPLOYED_WITH", "Microservices deployed with Docker", 0.8),
    ("microservices", "kubernetes", "ORCHESTRATED_BY", "Microservices orchestrated by Kubernetes", 0.8),
    
    # Security relationships
    ("oauth", "jwt", "IMPLEMENTS", "OAuth implements JWT tokens", 0.8),
    ("jwt", "fastapi", "SECURES", "JWT secures FastAPI", 0.8),
    ("encryption", "postgresql", "PROTECTS", "Encryption protects PostgreSQL", 0.9),
    ("rate_limiting", "api_gateway", "ENFORCED_BY", "Rate limiting enforced by API gateway", 0.8),
    ("cors", "fastapi", "CONFIGURED_IN", "CORS configured in FastAPI", 0.7),
    ("oauth", "api_gateway", "HANDLES_AUTH", "OAuth handles auth in API gateway", 0.8),
    
    # Business relationships
    ("user_experience", "performance", "DEPENDS_ON", "UX depends on performance", 0.9),
    ("performance", "cache_strategy", "IMPROVED_BY", "Performance improved by caching", 0.8),
    ("performance", "load_balancer", "ENHANCED_BY", "Performance enhanced by load balancing", 0.8),
    ("scalability", "microservices", "ACHIEVED_WITH", "Scalability achieved with microservices", 0.9),
    ("reliability", "replication", "ENSURED_BY", "Reliability ensured by replication", 0.8),
    ("monitoring", "reliability", "SUPPORTS", "Monitoring supports reliability", 0.9),
    ("scalability", "kubernetes", "ENABLED_BY", "Scalability enabled by Kubernetes", 0.8),
    
    # Data relationships
    ("indexing", "postgresql", "OPTIMIZES", "Indexing optimizes PostgreSQL", 0.9),
    ("partitioning", "scalability", "ENABLES", "Partitioning enables scalability", 0.8),
    ("replication", "consistency", "CHALLENGES", "Replication challenges consistency", 0.7),
    ("consistency", "postgresql", "MAINTAINED_BY", "Consistency maintained by PostgreSQL", 0.8),
    ("indexing", "performance", "IMPROVES", "Indexing improves performance", 0.8),
    
    # Cross-domain relationships
    ("llm", "user_experience", "ENHANCES", "LLM enhances user experience", 0.8),
    ("python", "llm", "IMPLEMENTS", "Python implements LLM", 0.7),
    ("event_driven", "rag", "SUPPORTS_REALTIME", "Event-driven supports realtime RAG", 0.6),
    ("encryption", "embedding", "PROTECTS", "Encryption protects embeddings", 0.7),
    ("monitoring", "fastapi", "OBSERVES", "Monitoring observes FastAPI", 0.7),
    ("partitioning", "microservices", "ALIGNS_WITH", "Data partitioning aligns with microservices", 0.6),
]

def login() -> str:
    """Login and return JWT token."""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data="username=frank@neurograph.ai&password=Password@123"
    )
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code} {response.text}")
        return ""
    
    token = response.json()["access_token"]
    print(f"✅ Login successful")
    return token

def create_entities(token: str) -> Dict[str, str]:
    """Create graph entities and return entity_id mapping."""
    print(f"\n🎯 Creating {len(ENTITIES)} graph entities...")
    entity_id_map = {}
    
    for entity_key, entity_data in ENTITIES.items():
        response = requests.post(
            f"{BASE_URL}/api/v1/graph/entities",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "name": entity_data["name"],
                "entity_type": entity_data["type"],
                "properties": {**entity_data["properties"], "domain": entity_data["domain"]},
                "layer": "personal"
            }
        )
        
        if response.status_code in [200, 201]:
            entity_response = response.json()
            entity_id = entity_response["id"]
            entity_id_map[entity_key] = entity_id
            print(f"   [{len(entity_id_map)}/{len(ENTITIES)}] Created: {entity_data['name']} ({entity_id})")
        else:
            print(f"   ❌ Failed to create {entity_data['name']}: {response.status_code} {response.text}")
        
        time.sleep(0.3)
    
    print(f"✅ Created {len(entity_id_map)} entities")
    return entity_id_map

def create_relationships(token: str, entity_id_map: Dict[str, str]) -> int:
    """Create relationships between entities."""
    print(f"\n🔗 Creating {len(RELATIONSHIPS)} relationships...")
    relationship_count = 0
    
    for source_key, target_key, rel_type, reason, confidence in RELATIONSHIPS:
        if source_key in entity_id_map and target_key in entity_id_map:
            response = requests.post(
                f"{BASE_URL}/api/v1/graph/relationships",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={
                    "source_id": entity_id_map[source_key],
                    "target_id": entity_id_map[target_key],
                    "relationship_type": rel_type,
                    "reason": reason,
                    "confidence": confidence,
                    "properties": {"strength": confidence, "type": rel_type}
                }
            )
            
            if response.status_code in [200, 201]:
                relationship_count += 1
                print(f"   [{relationship_count}/{len(RELATIONSHIPS)}] {source_key} -[{rel_type}]-> {target_key}")
            else:
                print(f"   ❌ Failed relationship {source_key}->{target_key}: {response.status_code}")
            
            time.sleep(0.2)
        else:
            print(f"   ⚠️  Skipping {source_key}->{target_key}: entities not found")
    
    print(f"✅ Created {relationship_count} relationships")
    return relationship_count

def test_graph_visualization(token: str) -> bool:
    """Test graph visualization and path finding."""
    print(f"\n📊 Testing graph visualization...")
    
    # Test visualization
    response = requests.get(
        f"{BASE_URL}/api/v1/graph/visualize?depth=3",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        graph_data = response.json()
        entities = graph_data.get("entities", [])
        relationships = graph_data.get("relationships", [])
        print(f"✅ Visualization: {len(entities)} entities, {len(relationships)} relationships")
        
        # Show domain distribution
        domains = {}
        for entity in entities:
            domain = entity.get("properties", {}).get("domain", "unknown")
            domains[domain] = domains.get(domain, 0) + 1
        
        print(f"   📊 Domain distribution: {domains}")
        return True
    else:
        print(f"❌ Visualization failed: {response.status_code}")
        return False

def test_path_finding(token: str, entity_id_map: Dict[str, str]) -> bool:
    """Test path finding between entities."""
    print(f"\n🛤️ Testing path finding...")
    
    # Test some interesting paths
    test_paths = [
        ("python", "user_experience", "Python to UX"),
        ("llm", "scalability", "LLM to Scalability"),
        ("oauth", "performance", "OAuth to Performance"),
    ]
    
    for source_key, target_key, description in test_paths:
        if source_key in entity_id_map and target_key in entity_id_map:
            source_id = entity_id_map[source_key]
            target_id = entity_id_map[target_key]
            
            response = requests.get(
                f"{BASE_URL}/api/v1/graph/paths/{source_id}/{target_id}?max_depth=5",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                paths_data = response.json()
                paths = paths_data.get("paths", [])
                print(f"   ✅ {description}: {len(paths)} paths found")
                
                if paths:
                    # Show shortest path
                    shortest = min(paths, key=lambda p: len(p))
                    path_length = len(shortest) - 1
                    print(f"      Shortest path length: {path_length}")
            else:
                print(f"   ❌ {description}: Path finding failed {response.status_code}")
    
    return True

def main():
    """Create complex interconnected graph using /graph endpoints."""
    print("🎯 Complex Graph Creation via /graph API")
    print("=" * 50)
    
    # Login
    token = login()
    if not token:
        return
    
    # Create entities
    entity_id_map = create_entities(token)
    if not entity_id_map:
        print("❌ Failed to create entities")
        return
    
    # Create relationships
    relationship_count = create_relationships(token, entity_id_map)
    
    # Test visualization
    test_graph_visualization(token)
    
    # Test path finding
    test_path_finding(token, entity_id_map)
    
    print(f"\n🎉 Complex Graph Creation Complete!")
    print(f"📊 Summary:")
    print(f"   Entities Created: {len(entity_id_map)}")
    print(f"   Relationships: {relationship_count}")
    print(f"   Domains: Technology, AI, Architecture, Security, Business, Data")
    print(f"   Graph Structure: Multi-hop traversal enabled")
    print(f"\n🔗 Graph Capabilities:")
    print(f"   - Rich semantic relationships")
    print(f"   - Cross-domain connections")
    print(f"   - Path finding between concepts")
    print(f"   - Visual graph exploration")
    print(f"   - Entity type classification")

if __name__ == "__main__":
    main()