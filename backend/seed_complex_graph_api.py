#!/usr/bin/env python3
"""
Complex graph seeding via admin API endpoint.
Creates rich interconnected memory structure through the production API.
"""

import json
import requests
import time
from typing import Dict, List

BASE_URL = "https://neuro-graph-be.vercel.app"

# Comprehensive memory concepts with domains
MEMORY_CONCEPTS = [
    # Technology Stack
    {"content": "Python is a versatile programming language", "domain": "technology"},
    {"content": "FastAPI is a modern Python web framework", "domain": "technology"},  
    {"content": "Neo4j is a graph database for connected data", "domain": "technology"},
    {"content": "PostgreSQL is a powerful relational database", "domain": "technology"},
    {"content": "Redis provides fast in-memory caching", "domain": "technology"},
    {"content": "Docker enables application containerization", "domain": "technology"},
    {"content": "Kubernetes orchestrates container deployments", "domain": "technology"},
    {"content": "Vercel provides serverless deployment platform", "domain": "technology"},
    
    # AI/ML Domain
    {"content": "Large Language Models understand natural language", "domain": "ai"},
    {"content": "Embeddings convert text to vector representations", "domain": "ai"},
    {"content": "Retrieval Augmented Generation improves AI responses", "domain": "ai"},
    {"content": "Vector search finds semantically similar content", "domain": "ai"},
    {"content": "Transformers power modern language models", "domain": "ai"},
    {"content": "Attention mechanisms focus on relevant information", "domain": "ai"},
    {"content": "Fine-tuning adapts models to specific tasks", "domain": "ai"},
    {"content": "Prompt engineering optimizes AI interactions", "domain": "ai"},
    
    # Architecture Patterns
    {"content": "Microservices decompose applications into small services", "domain": "architecture"},
    {"content": "Event-driven architecture uses events for communication", "domain": "architecture"},
    {"content": "Caching strategies improve application performance", "domain": "architecture"},
    {"content": "Load balancing distributes traffic across servers", "domain": "architecture"},
    {"content": "API gateways provide unified service access", "domain": "architecture"},
    {"content": "Service mesh manages microservice communication", "domain": "architecture"},
    {"content": "Circuit breakers prevent cascade failures", "domain": "architecture"},
    
    # Security Domain
    {"content": "OAuth provides secure authorization framework", "domain": "security"},
    {"content": "JWT tokens enable stateless authentication", "domain": "security"},
    {"content": "Encryption protects data confidentiality", "domain": "security"},
    {"content": "Rate limiting prevents API abuse attacks", "domain": "security"},
    {"content": "CORS controls cross-origin resource sharing", "domain": "security"},
    {"content": "OWASP guidelines ensure security best practices", "domain": "security"},
    {"content": "Zero-trust architecture never trusts by default", "domain": "security"},
    
    # Business Domain
    {"content": "User experience determines product adoption", "domain": "business"},
    {"content": "Scalability enables handling increased demand", "domain": "business"},
    {"content": "Performance optimization improves satisfaction", "domain": "business"},
    {"content": "Reliability ensures consistent service availability", "domain": "business"},
    {"content": "Monitoring provides system observability", "domain": "business"},
    {"content": "Cost optimization maximizes resource efficiency", "domain": "business"},
    
    # Data Domain  
    {"content": "Database indexing accelerates query performance", "domain": "data"},
    {"content": "Data partitioning improves large dataset handling", "domain": "data"},
    {"content": "Replication ensures data availability and backup", "domain": "data"},
    {"content": "Data consistency maintains accuracy across systems", "domain": "data"},
    {"content": "ETL pipelines transform and load data", "domain": "data"},
    {"content": "Data lakes store structured and unstructured data", "domain": "data"},
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

def create_memories(token: str) -> List[Dict]:
    """Create memory concepts via API."""
    print(f"\n🧠 Creating {len(MEMORY_CONCEPTS)} memory concepts...")
    created_memories = []
    
    for i, concept in enumerate(MEMORY_CONCEPTS):
        response = requests.post(
            f"{BASE_URL}/api/v1/memory/remember",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "content": concept["content"],
                "layer": "personal",
                "metadata": {"domain": concept["domain"]}
            }
        )
        
        if response.status_code in [200, 201]:
            memory_data = response.json()
            created_memories.append(memory_data)
            print(f"   [{i+1}/{len(MEMORY_CONCEPTS)}] Created: {memory_data['id']}")
        else:
            print(f"   ❌ Failed to create memory: {response.status_code} {response.text}")
        
        # Small delay to avoid overwhelming the API
        time.sleep(0.5)
    
    print(f"✅ Created {len(created_memories)} memories")
    return created_memories

def create_edges(token: str, memories: List[Dict]) -> int:
    """Create edges between related memories."""
    print(f"\n🔗 Creating connections between memories...")
    
    # Group memories by domain
    domains = {}
    for memory in memories:
        domain = memory.get('metadata', {}).get('domain', 'unknown')
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(memory)
    
    edge_count = 0
    
    # Create intra-domain connections (within same domain)
    for domain, domain_memories in domains.items():
        print(f"   Creating {domain} domain connections...")
        for i, memory1 in enumerate(domain_memories):
            for memory2 in domain_memories[i+1:]:
                try:
                    response = requests.post(
                        f"{BASE_URL}/api/v1/memory/edges",
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "source_memory_id": memory1["id"],
                            "target_memory_id": memory2["id"],
                            "reason": f"Related {domain} concepts",
                            "confidence": 0.7
                        }
                    )
                    
                    if response.status_code == 201:
                        edge_count += 1
                    
                    time.sleep(0.3)
                except Exception as e:
                    print(f"   Warning: Failed to create edge: {e}")
    
    # Create inter-domain connections (cross-domain relationships)
    tech_memories = domains.get('technology', [])
    ai_memories = domains.get('ai', [])
    arch_memories = domains.get('architecture', [])
    sec_memories = domains.get('security', [])
    biz_memories = domains.get('business', [])
    data_memories = domains.get('data', [])
    
    # Key cross-domain relationships
    cross_domain_patterns = [
        (tech_memories, ai_memories, "Technology enables AI"),
        (ai_memories, biz_memories, "AI enhances business value"),
        (arch_memories, biz_memories, "Architecture supports business goals"),
        (sec_memories, tech_memories, "Security protects technology"),
        (data_memories, ai_memories, "Data powers AI systems"),
        (arch_memories, tech_memories, "Architecture guides technology choices"),
    ]
    
    print(f"   Creating cross-domain connections...")
    for source_domain, target_domain, reason in cross_domain_patterns:
        # Create a few connections between domains
        for source_memory in source_domain[:3]:  # Limit to first 3 to avoid too many connections
            for target_memory in target_domain[:2]:  # Connect to first 2 in target domain
                try:
                    response = requests.post(
                        f"{BASE_URL}/api/v1/memory/edges",
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "source_memory_id": source_memory["id"],
                            "target_memory_id": target_memory["id"],
                            "reason": reason,
                            "confidence": 0.6
                        }
                    )
                    
                    if response.status_code == 201:
                        edge_count += 1
                    
                    time.sleep(0.3)
                except Exception as e:
                    print(f"   Warning: Failed to create cross-domain edge: {e}")
    
    print(f"✅ Created {edge_count} memory connections")
    return edge_count

def sync_to_neo4j(token: str) -> bool:
    """Sync the enriched memory graph to Neo4j."""
    print(f"\n🔄 Syncing enriched graph to Neo4j...")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/admin/sync-neo4j",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={"confirm": "SYNC_NEO4J"}
    )
    
    if response.status_code != 200:
        print(f"❌ Neo4j sync failed: {response.status_code} {response.text}")
        return False
    
    result = response.json()
    memories_created = result["data"]["memories_created"]
    print(f"✅ Neo4j sync complete: {memories_created} memories synced")
    return True

def test_graph_query(token: str) -> bool:
    """Test the enriched graph with a complex query."""
    print(f"\n🧠 Testing enriched graph memory...")
    
    test_queries = [
        "How do AI and technology work together?",
        "What security measures protect our systems?", 
        "How does architecture support business goals?",
        "What technologies enable scalable AI systems?"
    ]
    
    for query in test_queries:
        print(f"\n❓ Query: {query}")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/message",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={"content": query},
            timeout=120
        )
        
        if response.status_code == 200:
            chat_response = response.json()
            sources = chat_response.get("sources", [])
            print(f"✅ Response generated with {len(sources)} sources")
            
            # Show sources from different domains
            domains_used = set()
            for source in sources[:3]:  # Show top 3 sources
                content = source['content'][:60]
                score = source['score']
                print(f"   [{score:.3f}] {content}...")
                # Try to extract domain from content
                if 'AI' in source['content'] or 'language' in source['content'].lower():
                    domains_used.add('AI')
                elif 'security' in source['content'].lower() or 'OAuth' in source['content']:
                    domains_used.add('Security') 
                elif 'architecture' in source['content'].lower() or 'microservice' in source['content'].lower():
                    domains_used.add('Architecture')
                elif 'business' in source['content'].lower() or 'performance' in source['content'].lower():
                    domains_used.add('Business')
            
            if domains_used:
                print(f"   🌐 Domains: {', '.join(domains_used)}")
        else:
            print(f"❌ Query failed: {response.status_code}")
        
        time.sleep(2)  # Brief pause between queries
    
    return True

def main():
    """Create complex interconnected graph memory."""
    print("🔄 Complex Graph Memory Seeding")
    print("=" * 50)
    
    # Login
    token = login()
    if not token:
        return
    
    # Create rich memory concepts
    memories = create_memories(token)
    if not memories:
        print("❌ Failed to create memories")
        return
    
    # Create connections between memories
    edge_count = create_edges(token, memories)
    
    # Sync to Neo4j
    if not sync_to_neo4j(token):
        print("❌ Failed to sync to Neo4j")
        return
    
    # Test the enriched graph
    test_graph_query(token)
    
    print(f"\n🎉 Complex Graph Memory Creation Complete!")
    print(f"📊 Summary:")
    print(f"   Memories Created: {len(memories)}")
    print(f"   Connections: {edge_count}")
    print(f"   Domains: Technology, AI, Architecture, Security, Business, Data")
    print(f"   Neo4j: Synced successfully")
    print(f"\n🔗 Graph Structure:")
    print(f"   - Intra-domain connections (same domain concepts)")
    print(f"   - Inter-domain relationships (cross-domain)")
    print(f"   - Multi-hop traversal enabled")
    print(f"   - Rich semantic relationships")

if __name__ == "__main__":
    main()