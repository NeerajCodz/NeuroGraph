#!/usr/bin/env python
"""Full E2E test for neeraj@ng.ai"""
import requests
import json
import time
import sys

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'http://localhost:8000/api/v1'

# Login
print("=" * 60)
print("1. AUTHENTICATION")
print("=" * 60)
r = requests.post(f'{BASE}/auth/login', data={'username':'neeraj@ng.ai','password':'Password@123'})
print(f'Login: {r.status_code}')
if r.status_code != 200:
    print(r.text[:200])
    exit(1)

token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

me = requests.get(f'{BASE}/auth/me', headers=headers)
user = me.json()
print(f"User: {user.get('full_name')} ({user.get('email')})")
print(f"ID: {user.get('id')}")

# Store personal memories
print("\n" + "=" * 60)
print("2. STORING PERSONAL MEMORIES")
print("=" * 60)

memories = [
    "I am Neeraj, a software engineer working on AI projects. I prefer Python for backend development.",
    "My current project is NeuroGraph, an agentic context engine with explainable graph memory.",
    "I use Neo4j for graph database and PostgreSQL with pgvector for embeddings.",
    "My favorite coffee is cappuccino and I usually work late at night.",
    "I am learning about LangChain and AI agents for building autonomous systems."
]

for i, content in enumerate(memories, 1):
    r = requests.post(f'{BASE}/memory/remember', 
        headers=headers,
        json={'content': content, 'layer': 'personal'},
        timeout=60
    )
    status = 'OK' if r.status_code in [200, 201] else 'FAIL'
    print(f"{status} Memory {i}: {r.status_code}")
    time.sleep(0.5)  # Rate limiting

# Test memory recall
print("\n" + "=" * 60)
print("3. MEMORY RECALL (Vector Search)")
print("=" * 60)

queries = [
    "What programming language does Neeraj prefer?",
    "What is NeuroGraph?",
    "What databases are used?"
]

for query in queries:
    r = requests.post(f'{BASE}/memory/recall',
        headers=headers,
        json={'query': query, 'limit': 3}
    )
    if r.status_code == 200:
        memories = r.json()  # Returns list directly
        print(f"\nQuery: '{query}'")
        for mem in memories[:3]:
            score = mem.get('score', 0)
            content = mem.get('content', '')[:80]
            print(f"  [{score:.2f}] {content}...")
    else:
        print(f"FAIL Recall: {r.status_code}")

# Test graph endpoints
print("\n" + "=" * 60)
print("4. GRAPH ENDPOINTS")
print("=" * 60)

r = requests.get(f'{BASE}/graph/entities', headers=headers, timeout=30)
if r.status_code == 200:
    entities = r.json()
    print(f"OK Entities: {len(entities)} found")
    for e in entities[:5]:
        print(f"  - {e.get('name')} ({e.get('type')})")
else:
    print(f"FAIL Entities: {r.status_code}")

r = requests.get(f'{BASE}/graph/visualize', headers=headers, timeout=30)
if r.status_code == 200:
    data = r.json()
    print(f"OK Visualize: {len(data['nodes'])} nodes, {len(data['edges'])} edges")
else:
    print(f"FAIL Visualize: {r.status_code}")

r = requests.get(f'{BASE}/graph/centrality', headers=headers, timeout=30)
if r.status_code == 200:
    centrality = r.json()
    print(f"OK Centrality: {len(centrality)} entities scored")
else:
    print(f"FAIL Centrality: {r.status_code}")

# Test chat with memory context
print("\n" + "=" * 60)
print("5. CHAT WITH MEMORY CONTEXT")
print("=" * 60)

chat_queries = [
    "What do you know about me?",
    "What project am I working on?",
    "What technologies am I using?"
]

for q in chat_queries:
    print(f"\n>> {q}")
    r = requests.post(f'{BASE}/chat/message',
        headers=headers,
        json={'content': q},
        timeout=60
    )
    if r.status_code == 200:
        data = r.json()
        response = data.get('content', '')[:200]
        confidence = data.get('confidence', 0)
        sources = len(data.get('sources', []))
        print(f"<< {response}...")
        print(f"   [Confidence: {confidence:.0%}, Sources: {sources}]")
    else:
        print(f"FAIL Chat: {r.status_code} - {r.text[:100]}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
