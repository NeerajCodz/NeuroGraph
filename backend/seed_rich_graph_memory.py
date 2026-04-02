#!/usr/bin/env python3
"""
Rich Graph Memory Seeding Script

Creates 30+ interconnected memories with complex relationships
via the production /memory API endpoints.
"""

import requests
import json
import time
from typing import Dict, List, Any

# Production API
BASE_URL = "https://neuro-graph-be.vercel.app/api/v1"

def login() -> str:
    """Login and return access token"""
    print("🔐 Authenticating...")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data="username=alice@neurograph.ai&password=Password@123"
    )
    
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.status_code} - {response.text}")
    
    token = response.json()["access_token"]
    print("✅ Login successful")
    return token

def create_memory(token: str, content: str, layer: str = "personal", tags: List[str] = None) -> Dict:
    """Create a memory via /memory/remember"""
    payload = {
        "content": content,
        "layer": layer,
        "metadata": {
            "source": "graph_seeding",
            "tags": tags or []
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/memory/remember",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=payload
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to create memory: {response.status_code} - {response.text}")
    
    return response.json()

def create_canvas_edge(token: str, source_id: str, target_id: str, reason: str, layer: str = "personal") -> Dict:
    """Create a canvas edge between memories"""
    payload = {
        "source_id": source_id,
        "target_id": target_id,
        "reason": reason,
        "layer": layer
    }
    
    response = requests.post(
        f"{BASE_URL}/memory/edges",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=payload
    )
    
    if response.status_code != 200:
        print(f"⚠️  Edge creation failed: {response.status_code} - {response.text}")
        return None
    
    return response.json()

def main():
    print("🎯 Rich Graph Memory Seeding")
    print("=" * 50)
    
    # Authenticate
    token = login()
    
    # Define rich memory content with interconnected themes
    memories_data = [
        # Core AI/ML Concepts (Technology Foundation)
        {
            "content": "Neural networks are computational models inspired by biological neural networks. They consist of interconnected nodes (neurons) organized in layers that process and transform input data through weighted connections.",
            "tags": ["neural-networks", "ai", "technology", "foundation"]
        },
        {
            "content": "Transformer architecture revolutionized natural language processing by introducing self-attention mechanisms. This allows models to weigh the importance of different parts of input sequences when making predictions.",
            "tags": ["transformers", "nlp", "attention", "architecture"]
        },
        {
            "content": "Large Language Models (LLMs) like GPT and Claude are built on transformer architectures trained on vast amounts of text data. They demonstrate emergent capabilities like reasoning, coding, and creative writing.",
            "tags": ["llm", "gpt", "claude", "emergent-abilities"]
        },
        {
            "content": "Retrieval Augmented Generation (RAG) combines pre-trained language models with external knowledge retrieval. This enables models to access up-to-date information without retraining.",
            "tags": ["rag", "retrieval", "knowledge", "hybrid-systems"]
        },
        {
            "content": "Vector embeddings transform text, images, and other data into high-dimensional numerical representations that capture semantic meaning. This enables similarity search and clustering.",
            "tags": ["embeddings", "vectors", "semantic-search", "representation"]
        },
        
        # Software Architecture (System Design)
        {
            "content": "Microservices architecture breaks monolithic applications into small, independent services that communicate via APIs. This improves scalability, maintainability, and team autonomy.",
            "tags": ["microservices", "architecture", "scalability", "apis"]
        },
        {
            "content": "Event-driven architecture enables loose coupling between components through asynchronous message passing. Services react to events without direct dependencies on event producers.",
            "tags": ["event-driven", "async", "messaging", "decoupling"]
        },
        {
            "content": "API Gateway serves as a single entry point for multiple microservices, handling authentication, rate limiting, request routing, and response aggregation.",
            "tags": ["api-gateway", "routing", "authentication", "rate-limiting"]
        },
        {
            "content": "Container orchestration with Kubernetes automates deployment, scaling, and management of containerized applications across clusters of machines.",
            "tags": ["kubernetes", "containers", "orchestration", "deployment"]
        },
        {
            "content": "Load balancing distributes incoming requests across multiple server instances to prevent overload and ensure high availability and performance.",
            "tags": ["load-balancing", "availability", "performance", "distribution"]
        },
        
        # Database & Storage (Data Layer)
        {
            "content": "PostgreSQL is an advanced relational database with support for JSON, arrays, and custom data types. Its ACID compliance ensures data integrity in complex transactions.",
            "tags": ["postgresql", "relational", "acid", "json"]
        },
        {
            "content": "Neo4j is a graph database optimized for storing and querying highly connected data. It uses Cypher query language to traverse relationships efficiently.",
            "tags": ["neo4j", "graph-database", "cypher", "relationships"]
        },
        {
            "content": "Redis provides in-memory data structure storage used as database, cache, and message broker. Its sub-millisecond latency makes it ideal for real-time applications.",
            "tags": ["redis", "cache", "in-memory", "real-time"]
        },
        {
            "content": "Database indexing creates additional data structures to speed up query performance. B-tree indexes are most common, while hash indexes optimize equality lookups.",
            "tags": ["indexing", "b-tree", "performance", "optimization"]
        },
        {
            "content": "Data partitioning splits large datasets across multiple storage systems. Horizontal partitioning (sharding) distributes rows, while vertical partitioning splits columns.",
            "tags": ["partitioning", "sharding", "distribution", "scaling"]
        },
        
        # Security (Protection Layer)
        {
            "content": "OAuth 2.0 is an authorization framework that enables applications to obtain limited access to user accounts. It separates authentication from authorization concerns.",
            "tags": ["oauth", "authorization", "security", "tokens"]
        },
        {
            "content": "JWT (JSON Web Tokens) are compact, URL-safe tokens for securely transmitting information between parties. They contain claims about user identity and permissions.",
            "tags": ["jwt", "tokens", "claims", "stateless"]
        },
        {
            "content": "Encryption protects sensitive data by transforming it into unreadable format. AES-256 provides strong symmetric encryption for data at rest and in transit.",
            "tags": ["encryption", "aes", "security", "data-protection"]
        },
        {
            "content": "Rate limiting prevents abuse by controlling request frequency from clients. Token bucket and sliding window algorithms are common implementation strategies.",
            "tags": ["rate-limiting", "token-bucket", "protection", "throttling"]
        },
        {
            "content": "CORS (Cross-Origin Resource Sharing) controls which web domains can access API resources. Proper configuration prevents unauthorized cross-origin requests.",
            "tags": ["cors", "cross-origin", "web-security", "browser"]
        },
        
        # DevOps & Deployment (Operations)
        {
            "content": "Docker containerization packages applications with their dependencies into portable, lightweight containers that run consistently across different environments.",
            "tags": ["docker", "containerization", "portability", "consistency"]
        },
        {
            "content": "CI/CD pipelines automate code integration, testing, and deployment. This reduces manual errors and enables rapid, reliable software delivery.",
            "tags": ["cicd", "automation", "testing", "deployment"]
        },
        {
            "content": "Infrastructure as Code (IaC) manages infrastructure through machine-readable definition files rather than manual processes. Terraform and CloudFormation are popular tools.",
            "tags": ["iac", "terraform", "automation", "infrastructure"]
        },
        {
            "content": "Monitoring and observability provide insights into system behavior through metrics, logs, and traces. This enables proactive issue detection and resolution.",
            "tags": ["monitoring", "observability", "metrics", "debugging"]
        },
        {
            "content": "Blue-green deployment reduces downtime by running two identical production environments. Traffic switches between them during deployments.",
            "tags": ["blue-green", "deployment", "zero-downtime", "reliability"]
        },
        
        # Performance & Optimization
        {
            "content": "Caching strategies improve performance by storing frequently accessed data in fast storage. LRU, LFU, and time-based eviction policies manage cache capacity.",
            "tags": ["caching", "lru", "performance", "optimization"]
        },
        {
            "content": "Database connection pooling manages a cache of database connections to reduce connection overhead and improve application performance.",
            "tags": ["connection-pooling", "database", "performance", "resource-management"]
        },
        {
            "content": "Content Delivery Networks (CDNs) cache static assets geographically close to users, reducing latency and bandwidth costs for web applications.",
            "tags": ["cdn", "latency", "geographic", "static-assets"]
        },
        {
            "content": "Horizontal scaling adds more servers to handle increased load, while vertical scaling increases the power of existing servers. Each approach has trade-offs.",
            "tags": ["scaling", "horizontal", "vertical", "capacity"]
        },
        {
            "content": "Memory management in applications involves allocating, using, and freeing memory efficiently. Garbage collection automates memory cleanup in managed languages.",
            "tags": ["memory-management", "garbage-collection", "optimization", "resources"]
        },
        
        # Emerging Technologies
        {
            "content": "Edge computing brings computation and storage closer to data sources. This reduces latency and bandwidth usage for IoT and real-time applications.",
            "tags": ["edge-computing", "iot", "latency", "distributed"]
        },
        {
            "content": "Serverless computing allows developers to run code without managing servers. Functions execute on-demand and scale automatically based on workload.",
            "tags": ["serverless", "functions", "auto-scaling", "managed"]
        },
        {
            "content": "WebAssembly (WASM) enables high-performance applications to run in web browsers. It provides near-native execution speed for computationally intensive tasks.",
            "tags": ["webassembly", "browser", "performance", "native-speed"]
        }
    ]
    
    print(f"🎯 Creating {len(memories_data)} interconnected memories...")
    
    # Create memories
    created_memories = []
    for i, memory_data in enumerate(memories_data):
        try:
            memory = create_memory(
                token,
                memory_data["content"],
                tags=memory_data["tags"]
            )
            created_memories.append({
                "id": memory["id"],
                "content": memory_data["content"],
                "tags": memory_data["tags"]
            })
            print(f"   [{i+1}/{len(memories_data)}] Created memory with {len(memory_data['tags'])} tags")
            time.sleep(0.5)  # Rate limiting
        except Exception as e:
            print(f"   ❌ Failed to create memory {i+1}: {e}")
    
    print(f"✅ Created {len(created_memories)} memories")
    
    # Create rich interconnections based on shared themes
    print(f"🔗 Creating thematic connections...")
    
    connections_created = 0
    
    # Connect related concepts
    connection_rules = [
        # AI/ML Foundation Chain
        {"from_tags": ["neural-networks"], "to_tags": ["transformers"], "reason": "Transformers are built on neural network foundations"},
        {"from_tags": ["transformers"], "to_tags": ["llm"], "reason": "LLMs use transformer architectures"},
        {"from_tags": ["llm"], "to_tags": ["rag"], "reason": "RAG enhances LLM capabilities with external knowledge"},
        {"from_tags": ["rag"], "to_tags": ["embeddings"], "reason": "RAG relies on vector embeddings for semantic search"},
        
        # Architecture & Scaling
        {"from_tags": ["microservices"], "to_tags": ["event-driven"], "reason": "Event-driven patterns complement microservices architecture"},
        {"from_tags": ["microservices"], "to_tags": ["api-gateway"], "reason": "API gateways manage microservice communication"},
        {"from_tags": ["microservices"], "to_tags": ["kubernetes"], "reason": "Kubernetes orchestrates microservice deployments"},
        {"from_tags": ["load-balancing"], "to_tags": ["scaling"], "reason": "Load balancing enables horizontal scaling"},
        
        # Database Ecosystem
        {"from_tags": ["postgresql"], "to_tags": ["indexing"], "reason": "PostgreSQL uses indexing for query optimization"},
        {"from_tags": ["indexing"], "to_tags": ["performance"], "reason": "Indexing directly impacts database performance"},
        {"from_tags": ["partitioning"], "to_tags": ["scaling"], "reason": "Partitioning enables database scaling strategies"},
        {"from_tags": ["redis"], "to_tags": ["caching"], "reason": "Redis is commonly used for caching implementations"},
        
        # Security Chain
        {"from_tags": ["oauth"], "to_tags": ["jwt"], "reason": "OAuth often uses JWT tokens for authorization"},
        {"from_tags": ["jwt"], "to_tags": ["api-gateway"], "reason": "API gateways validate JWT tokens"},
        {"from_tags": ["encryption"], "to_tags": ["security"], "reason": "Encryption is fundamental to data security"},
        {"from_tags": ["rate-limiting"], "to_tags": ["protection"], "reason": "Rate limiting provides API protection"},
        
        # DevOps Pipeline
        {"from_tags": ["docker"], "to_tags": ["kubernetes"], "reason": "Kubernetes orchestrates Docker containers"},
        {"from_tags": ["cicd"], "to_tags": ["docker"], "reason": "CI/CD pipelines often build Docker images"},
        {"from_tags": ["cicd"], "to_tags": ["blue-green"], "reason": "CI/CD enables blue-green deployment strategies"},
        {"from_tags": ["monitoring"], "to_tags": ["observability"], "reason": "Monitoring is a key component of observability"},
        
        # Performance Optimization
        {"from_tags": ["caching"], "to_tags": ["performance"], "reason": "Caching directly improves system performance"},
        {"from_tags": ["cdn"], "to_tags": ["performance"], "reason": "CDNs optimize content delivery performance"},
        {"from_tags": ["connection-pooling"], "to_tags": ["optimization"], "reason": "Connection pooling optimizes database resource usage"},
        {"from_tags": ["memory-management"], "to_tags": ["performance"], "reason": "Efficient memory management improves performance"},
        
        # Cross-cutting Technology Connections
        {"from_tags": ["embeddings"], "to_tags": ["neo4j"], "reason": "Graph databases can store vector embeddings as node properties"},
        {"from_tags": ["real-time"], "to_tags": ["edge-computing"], "reason": "Edge computing enables real-time processing"},
        {"from_tags": ["serverless"], "to_tags": ["auto-scaling"], "reason": "Serverless platforms provide automatic scaling"},
        {"from_tags": ["webassembly"], "to_tags": ["performance"], "reason": "WebAssembly delivers high-performance web applications"},
    ]
    
    # Create connections based on rules
    for rule in connection_rules:
        from_memories = [m for m in created_memories if any(tag in rule["from_tags"] for tag in m["tags"])]
        to_memories = [m for m in created_memories if any(tag in rule["to_tags"] for tag in m["tags"])]
        
        for from_mem in from_memories:
            for to_mem in to_memories:
                if from_mem["id"] != to_mem["id"]:  # No self-connections
                    try:
                        edge = create_canvas_edge(
                            token,
                            from_mem["id"],
                            to_mem["id"],
                            rule["reason"]
                        )
                        if edge:
                            connections_created += 1
                            print(f"   🔗 Connected: {from_mem['tags'][0]} → {to_mem['tags'][0]}")
                            time.sleep(0.3)  # Rate limiting
                    except Exception as e:
                        print(f"   ⚠️  Connection failed: {e}")
    
    print(f"✅ Created {connections_created} thematic connections")
    
    # Test graph visualization
    print("📊 Testing graph visualization...")
    try:
        response = requests.get(
            f"{BASE_URL}/graph/visualize?max_nodes=50",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            viz_data = response.json()
            print(f"✅ Visualization: {len(viz_data.get('nodes', []))} entities, {len(viz_data.get('edges', []))} relationships")
        else:
            print(f"❌ Visualization failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Visualization error: {e}")
    
    print("\n🎉 Rich Graph Memory Seeding Complete!")
    print(f"📊 Summary:")
    print(f"   Memories Created: {len(created_memories)}")
    print(f"   Thematic Connections: {connections_created}")
    print(f"   Knowledge Domains: AI/ML, Architecture, Database, Security, DevOps, Performance")
    print(f"   Graph Complexity: Multi-hop traversal with semantic relationships")
    
    print("\n🔗 Graph Features:")
    print("   - Rich semantic relationships between concepts")
    print("   - Cross-domain knowledge connections") 
    print("   - Thematic clustering by technology areas")
    print("   - Foundation → Application → Optimization chains")
    print("   - Real-world technology stack relationships")

if __name__ == "__main__":
    main()