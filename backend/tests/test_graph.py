#!/usr/bin/env python
"""Test graph endpoints."""
import requests
import sys
sys.stdout.reconfigure(encoding='utf-8')

r = requests.post('http://localhost:8000/api/v1/auth/login', data={'username':'neeraj@ng.ai','password':'Password@123'}, timeout=10)
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

print("Testing Graph Endpoints")
print("=" * 40)

# Test entities
r = requests.get('http://localhost:8000/api/v1/graph/entities', headers=headers, timeout=30)
print(f"GET /entities: {r.status_code}")
if r.status_code == 200:
    entities = r.json()
    print(f"  Found {len(entities)} entities")
    for e in entities[:5]:
        print(f"    - {e['name']} ({e['type']})")
else:
    print(f"  Error: {r.text[:200]}")

# Test visualize
r = requests.get('http://localhost:8000/api/v1/graph/visualize', headers=headers, timeout=30)
print(f"\nGET /visualize: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"  Nodes: {len(data['nodes'])}, Edges: {len(data['edges'])}")
else:
    print(f"  Error: {r.text[:200]}")

# Test relationships
r = requests.get('http://localhost:8000/api/v1/graph/relationships/Alice', headers=headers, timeout=30)
print(f"\nGET /relationships/Alice: {r.status_code}")
if r.status_code == 200:
    rels = r.json()
    print(f"  Found {len(rels)} relationships")
    for rel in rels[:3]:
        print(f"    - {rel['source_id']} --{rel['type']}--> {rel['target_id']}")
else:
    print(f"  Error: {r.text[:200]}")

# Test centrality
r = requests.get('http://localhost:8000/api/v1/graph/centrality', headers=headers, timeout=30)
print(f"\nGET /centrality: {r.status_code}")
if r.status_code == 200:
    centrality = r.json()
    print(f"  Entities with centrality:")
    for name, degree in list(centrality.items())[:5]:
        print(f"    - {name}: {degree}")
else:
    print(f"  Error: {r.text[:200]}")

print("\n" + "=" * 40)
print("Done!")
