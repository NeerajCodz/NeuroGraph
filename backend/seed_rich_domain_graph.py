#!/usr/bin/env python3
"""
Direct Neo4j Rich Graph Seeding

Creates rich interconnected domain entities directly in Neo4j
via production /graph endpoints with proper node types.
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

def create_entity(token: str, name: str, entity_type: str, properties: Dict = None) -> Dict:
    """Create entity via /graph/entities"""
    payload = {
        "name": name,
        "entity_type": entity_type,
        "properties": properties or {},
        "layer": "personal"
    }
    
    response = requests.post(
        f"{BASE_URL}/graph/entities",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=payload
    )
    
    if response.status_code != 200:
        print(f"⚠️  Entity creation failed: {response.status_code} - {response.text}")
        return None
    
    return response.json()

def create_relationship(token: str, source_name: str, target_name: str, rel_type: str, properties: Dict = None) -> Dict:
    """Create relationship via /graph/relationships"""
    payload = {
        "source_name": source_name,
        "target_name": target_name,
        "relationship_type": rel_type,
        "properties": properties or {},
        "layer": "personal"
    }
    
    response = requests.post(
        f"{BASE_URL}/graph/relationships",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=payload
    )
    
    if response.status_code != 200:
        print(f"⚠️  Relationship creation failed: {response.status_code} - {response.text}")
        return None
    
    return response.json()

def main():
    print("🎯 Direct Neo4j Rich Graph Seeding")
    print("=" * 50)
    
    # Authenticate
    token = login()
    
    # Define rich domain entities with proper types that should show in visualization
    entities_data = [
        # AI/ML Domain
        {"name": "Neural Networks", "type": "Technology", "properties": {"domain": "AI", "complexity": "high", "description": "Computational models inspired by biological neural networks"}},
        {"name": "Deep Learning", "type": "Technology", "properties": {"domain": "AI", "complexity": "high", "description": "Machine learning using deep neural networks"}},
        {"name": "Transformer Models", "type": "Architecture", "properties": {"domain": "AI", "complexity": "high", "description": "Attention-based neural network architecture"}},
        {"name": "Large Language Models", "type": "Model", "properties": {"domain": "AI", "scale": "large", "description": "Large-scale language generation models"}},
        {"name": "GPT", "type": "Model", "properties": {"domain": "AI", "vendor": "OpenAI", "description": "Generative Pre-trained Transformer"}},
        {"name": "Claude", "type": "Model", "properties": {"domain": "AI", "vendor": "Anthropic", "description": "Constitutional AI assistant"}},
        
        # Backend Technologies  
        {"name": "Python", "type": "Language", "properties": {"domain": "Backend", "paradigm": "multi", "description": "High-level programming language"}},
        {"name": "FastAPI", "type": "Framework", "properties": {"domain": "Backend", "language": "Python", "description": "Modern web framework for building APIs"}},
        {"name": "PostgreSQL", "type": "Database", "properties": {"domain": "Backend", "type": "relational", "description": "Advanced relational database"}},
        {"name": "Neo4j", "type": "Database", "properties": {"domain": "Backend", "type": "graph", "description": "Graph database platform"}},
        {"name": "Redis", "type": "Database", "properties": {"domain": "Backend", "type": "cache", "description": "In-memory data structure store"}},
        
        # Infrastructure
        {"name": "Docker", "type": "Platform", "properties": {"domain": "Infrastructure", "category": "containerization", "description": "Application containerization platform"}},
        {"name": "Kubernetes", "type": "Platform", "properties": {"domain": "Infrastructure", "category": "orchestration", "description": "Container orchestration system"}},
        {"name": "Vercel", "type": "Platform", "properties": {"domain": "Infrastructure", "category": "deployment", "description": "Frontend deployment platform"}},
        {"name": "AWS", "type": "Platform", "properties": {"domain": "Infrastructure", "category": "cloud", "description": "Amazon Web Services cloud platform"}},
        
        # Architecture Patterns
        {"name": "Microservices", "type": "Pattern", "properties": {"domain": "Architecture", "style": "distributed", "description": "Distributed system architecture"}},
        {"name": "Event Driven", "type": "Pattern", "properties": {"domain": "Architecture", "style": "async", "description": "Event-driven architecture pattern"}},
        {"name": "API Gateway", "type": "Component", "properties": {"domain": "Architecture", "role": "gateway", "description": "Single entry point for APIs"}},
        {"name": "Load Balancer", "type": "Component", "properties": {"domain": "Architecture", "role": "distribution", "description": "Request distribution component"}},
        
        # Security
        {"name": "OAuth", "type": "Protocol", "properties": {"domain": "Security", "purpose": "authorization", "description": "Open authorization framework"}},
        {"name": "JWT", "type": "Standard", "properties": {"domain": "Security", "purpose": "tokens", "description": "JSON Web Tokens"}},
        {"name": "Encryption", "type": "Technique", "properties": {"domain": "Security", "purpose": "protection", "description": "Data protection through encoding"}},
        
        # Frontend
        {"name": "React", "type": "Framework", "properties": {"domain": "Frontend", "language": "JavaScript", "description": "UI library for building interfaces"}},
        {"name": "TypeScript", "type": "Language", "properties": {"domain": "Frontend", "base": "JavaScript", "description": "Typed superset of JavaScript"}},
        {"name": "D3js", "type": "Library", "properties": {"domain": "Frontend", "purpose": "visualization", "description": "Data visualization library"}},
        
        # Concepts
        {"name": "Scalability", "type": "Concept", "properties": {"domain": "Performance", "aspect": "growth", "description": "System's ability to handle increased load"}},
        {"name": "Performance", "type": "Concept", "properties": {"domain": "Performance", "aspect": "speed", "description": "System responsiveness and efficiency"}},
        {"name": "Reliability", "type": "Concept", "properties": {"domain": "Performance", "aspect": "stability", "description": "System dependability and uptime"}},
        {"name": "User Experience", "type": "Concept", "properties": {"domain": "Design", "aspect": "usability", "description": "User's interaction with the system"}},
        {"name": "Data Consistency", "type": "Concept", "properties": {"domain": "Database", "aspect": "integrity", "description": "Uniform data across system"}},
    ]
    
    print(f"🎯 Creating {len(entities_data)} domain entities...")
    
    # Create entities
    created_entities = []
    for i, entity_data in enumerate(entities_data):
        try:
            entity = create_entity(
                token,
                entity_data["name"],
                entity_data["type"],
                entity_data["properties"]
            )
            if entity:
                created_entities.append(entity_data)
                print(f"   [{i+1}/{len(entities_data)}] Created: {entity_data['name']} ({entity_data['type']})")
                time.sleep(0.3)  # Rate limiting
        except Exception as e:
            print(f"   ❌ Failed to create entity {i+1}: {e}")
    
    print(f"✅ Created {len(created_entities)} entities")
    
    # Create meaningful relationships
    relationships = [
        # AI/ML Chain
        ("Neural Networks", "Deep Learning", "ENABLES", {"reason": "Neural networks are the foundation of deep learning"}),
        ("Deep Learning", "Transformer Models", "IMPLEMENTS", {"reason": "Deep learning implements transformer architectures"}),
        ("Transformer Models", "Large Language Models", "POWERS", {"reason": "Transformers power modern LLMs"}),
        ("Large Language Models", "GPT", "INSTANTIATED_AS", {"reason": "GPT is a type of LLM"}),
        ("Large Language Models", "Claude", "INSTANTIATED_AS", {"reason": "Claude is a type of LLM"}),
        
        # Backend Stack
        ("Python", "FastAPI", "IMPLEMENTS", {"reason": "FastAPI is implemented in Python"}),
        ("FastAPI", "PostgreSQL", "CONNECTS_TO", {"reason": "FastAPI connects to PostgreSQL databases"}),
        ("FastAPI", "Redis", "USES", {"reason": "FastAPI uses Redis for caching"}),
        ("FastAPI", "Neo4j", "INTEGRATES_WITH", {"reason": "FastAPI integrates with Neo4j graph database"}),
        
        # Infrastructure
        ("Docker", "Kubernetes", "ORCHESTRATED_BY", {"reason": "Kubernetes orchestrates Docker containers"}),
        ("PostgreSQL", "Docker", "CONTAINERIZED_IN", {"reason": "PostgreSQL runs in Docker containers"}),
        ("Redis", "Docker", "CONTAINERIZED_IN", {"reason": "Redis runs in Docker containers"}),
        ("Vercel", "Docker", "SUPPORTS", {"reason": "Vercel supports Docker deployments"}),
        
        # Architecture
        ("Microservices", "Event Driven", "COMBINES_WITH", {"reason": "Microservices often use event-driven patterns"}),
        ("Microservices", "API Gateway", "MANAGED_BY", {"reason": "API Gateway manages microservice endpoints"}),
        ("Load Balancer", "API Gateway", "COMPONENT_OF", {"reason": "Load balancer is part of API gateway"}),
        ("Microservices", "Docker", "DEPLOYED_WITH", {"reason": "Microservices are deployed in Docker containers"}),
        
        # Security
        ("OAuth", "JWT", "USES", {"reason": "OAuth often uses JWT tokens"}),
        ("JWT", "FastAPI", "SECURES", {"reason": "JWT secures FastAPI endpoints"}),
        ("Encryption", "PostgreSQL", "PROTECTS", {"reason": "Encryption protects PostgreSQL data"}),
        ("OAuth", "API Gateway", "ENFORCED_BY", {"reason": "API Gateway enforces OAuth"}),
        
        # Frontend
        ("React", "TypeScript", "ENHANCED_BY", {"reason": "React is enhanced by TypeScript"}),
        ("React", "D3js", "INTEGRATES_WITH", {"reason": "React integrates with D3.js for visualization"}),
        ("D3js", "Neo4j", "VISUALIZES", {"reason": "D3.js visualizes Neo4j graph data"}),
        
        # Cross-domain relationships
        ("Large Language Models", "User Experience", "ENHANCES", {"reason": "LLMs enhance user experience"}),
        ("Performance", "User Experience", "AFFECTS", {"reason": "Performance directly affects UX"}),
        ("Scalability", "Microservices", "ACHIEVED_WITH", {"reason": "Scalability is achieved with microservices"}),
        ("Reliability", "Kubernetes", "ENSURED_BY", {"reason": "Kubernetes ensures system reliability"}),
        ("Data Consistency", "PostgreSQL", "MAINTAINED_BY", {"reason": "PostgreSQL maintains data consistency"}),
        ("Redis", "Performance", "IMPROVES", {"reason": "Redis improves system performance"}),
        
        # Technology stacks
        ("Python", "Neural Networks", "IMPLEMENTS", {"reason": "Python implements neural network frameworks"}),
        ("FastAPI", "Large Language Models", "SERVES", {"reason": "FastAPI serves LLM endpoints"}),
        ("Neo4j", "AI", "STORES", {"reason": "Neo4j stores AI knowledge graphs"}),
    ]
    
    print(f"🔗 Creating {len(relationships)} relationships...")
    
    relationships_created = 0
    for i, (source, target, rel_type, properties) in enumerate(relationships):
        try:
            relationship = create_relationship(token, source, target, rel_type, properties)
            if relationship:
                relationships_created += 1
                print(f"   [{i+1}/{len(relationships)}] {source} -[{rel_type}]-> {target}")
                time.sleep(0.3)
        except Exception as e:
            print(f"   ⚠️  Relationship {i+1} failed: {e}")
    
    print(f"✅ Created {relationships_created} relationships")
    
    # Test visualization
    print("📊 Testing graph visualization...")
    try:
        response = requests.get(
            f"{BASE_URL}/graph/visualize?max_nodes=100",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            viz_data = response.json()
            nodes = viz_data.get('nodes', [])
            edges = viz_data.get('edges', [])
            print(f"✅ Visualization: {len(nodes)} entities, {len(edges)} relationships")
            
            # Show domain distribution
            domains = {}
            for node in nodes:
                node_type = node.get('type', 'Unknown')
                domains[node_type] = domains.get(node_type, 0) + 1
            print(f"   📊 Node types: {domains}")
        else:
            print(f"❌ Visualization failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Visualization error: {e}")
    
    print("\n🎉 Direct Neo4j Graph Seeding Complete!")
    print(f"📊 Summary:")
    print(f"   Entities Created: {len(created_entities)}")
    print(f"   Relationships: {relationships_created}")
    print(f"   Domains: AI/ML, Backend, Infrastructure, Architecture, Security, Frontend")
    print(f"   Graph Structure: Rich semantic relationships with proper node types")
    
    print("\n🔗 Graph Features:")
    print("   - Proper entity types for visualization")
    print("   - Cross-domain technology relationships")
    print("   - AI/ML knowledge chains")
    print("   - Backend technology stacks")
    print("   - Infrastructure deployment paths")
    print("   - Security and performance connections")

if __name__ == "__main__":
    main()