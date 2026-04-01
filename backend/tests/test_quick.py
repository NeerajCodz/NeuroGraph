#!/usr/bin/env python
"""Quick E2E test for NeuroGraph - tests all endpoints."""
import requests
import sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'http://localhost:8000/api/v1'

def test_all():
    results = []
    
    # 1. Auth
    print("=" * 60)
    print("TESTING NEUROGRAPH BACKEND")
    print("=" * 60)
    
    print("\n[1] Authentication...")
    r = requests.post(f'{BASE}/auth/login', data={'username':'neeraj@ng.ai','password':'Password@123'}, timeout=10)
    if r.status_code == 200:
        token = r.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        print("    OK - Login successful")
        results.append(("Auth Login", "PASS"))
        
        r = requests.get(f'{BASE}/auth/me', headers=headers, timeout=10)
        if r.status_code == 200:
            user = r.json()
            print(f"    OK - User: {user['full_name']} ({user['email']})")
            results.append(("Auth Me", "PASS"))
        else:
            print(f"    FAIL - Get user: {r.status_code}")
            results.append(("Auth Me", "FAIL"))
    else:
        print(f"    FAIL - Login: {r.status_code}")
        results.append(("Auth Login", "FAIL"))
        return results
    
    # 2. Memory Recall (no storage - use existing memories)
    print("\n[2] Memory Recall...")
    queries = [
        ("Python programming", "What programming language"),
        ("NeuroGraph project", "What is NeuroGraph"),
        ("databases used", "What databases")
    ]
    
    for query, desc in queries:
        try:
            r = requests.post(f'{BASE}/memory/recall', headers=headers, 
                json={'query': query, 'limit': 3}, timeout=30)
            if r.status_code == 200:
                memories = r.json()
                if memories:
                    top_score = memories[0].get('score', 0)
                    print(f"    OK - '{desc}': {len(memories)} results, top score: {top_score:.2f}")
                    results.append((f"Recall: {desc}", "PASS"))
                else:
                    print(f"    WARN - '{desc}': No results")
                    results.append((f"Recall: {desc}", "WARN"))
            else:
                print(f"    FAIL - '{desc}': {r.status_code}")
                results.append((f"Recall: {desc}", "FAIL"))
        except Exception as e:
            print(f"    FAIL - '{desc}': {e}")
            results.append((f"Recall: {desc}", "FAIL"))
    
    # 3. Graph Endpoints
    print("\n[3] Graph Endpoints...")
    
    # Entities
    try:
        r = requests.get(f'{BASE}/graph/entities', headers=headers, timeout=30)
        if r.status_code == 200:
            entities = r.json()
            print(f"    OK - Entities: {len(entities)} found")
            results.append(("Graph Entities", "PASS"))
        else:
            print(f"    FAIL - Entities: {r.status_code}")
            results.append(("Graph Entities", "FAIL"))
    except Exception as e:
        print(f"    FAIL - Entities: {e}")
        results.append(("Graph Entities", "FAIL"))
    
    # Visualize
    try:
        r = requests.get(f'{BASE}/graph/visualize', headers=headers, timeout=30)
        if r.status_code == 200:
            data = r.json()
            print(f"    OK - Visualize: {len(data['nodes'])} nodes, {len(data['edges'])} edges")
            results.append(("Graph Visualize", "PASS"))
        else:
            print(f"    FAIL - Visualize: {r.status_code}")
            results.append(("Graph Visualize", "FAIL"))
    except Exception as e:
        print(f"    FAIL - Visualize: {e}")
        results.append(("Graph Visualize", "FAIL"))
    
    # Centrality
    try:
        r = requests.get(f'{BASE}/graph/centrality', headers=headers, timeout=30)
        if r.status_code == 200:
            centrality = r.json()
            print(f"    OK - Centrality: {len(centrality)} entities scored")
            results.append(("Graph Centrality", "PASS"))
        else:
            print(f"    FAIL - Centrality: {r.status_code}")
            results.append(("Graph Centrality", "FAIL"))
    except Exception as e:
        print(f"    FAIL - Centrality: {e}")
        results.append(("Graph Centrality", "FAIL"))
    
    # Relationships
    try:
        r = requests.get(f'{BASE}/graph/relationships/Alice', headers=headers, timeout=30)
        if r.status_code == 200:
            rels = r.json()
            print(f"    OK - Relationships: {len(rels)} for Alice")
            results.append(("Graph Relationships", "PASS"))
        else:
            print(f"    FAIL - Relationships: {r.status_code}")
            results.append(("Graph Relationships", "FAIL"))
    except Exception as e:
        print(f"    FAIL - Relationships: {e}")
        results.append(("Graph Relationships", "FAIL"))
    
    # 4. Chat (with timeout handling)
    print("\n[4] Chat with Memory Context...")
    
    try:
        r = requests.post(f'{BASE}/chat/message', headers=headers,
            json={'content': 'What project am I working on?'}, timeout=120)
        if r.status_code == 200:
            data = r.json()
            content = data.get('content', '')[:100]
            confidence = data.get('confidence', 0)
            sources = len(data.get('sources', []))
            print(f"    OK - Chat response received")
            print(f"         Response: {content}...")
            print(f"         Confidence: {confidence:.0%}, Sources: {sources}")
            results.append(("Chat Message", "PASS"))
        else:
            print(f"    FAIL - Chat: {r.status_code} - {r.text[:100]}")
            results.append(("Chat Message", "FAIL"))
    except requests.exceptions.Timeout:
        print("    WARN - Chat timed out (Gemini API may be rate limited)")
        results.append(("Chat Message", "TIMEOUT"))
    except Exception as e:
        print(f"    FAIL - Chat: {e}")
        results.append(("Chat Message", "FAIL"))
    
    return results

if __name__ == "__main__":
    results = test_all()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, status in results if status == "PASS")
    failed = sum(1 for _, status in results if status == "FAIL")
    warnings = sum(1 for _, status in results if status in ["WARN", "TIMEOUT"])
    
    for name, status in results:
        icon = "PASS" if status == "PASS" else ("WARN" if status in ["WARN", "TIMEOUT"] else "FAIL")
        print(f"  [{icon}] {name}")
    
    print(f"\nTotal: {passed} passed, {failed} failed, {warnings} warnings")
    print("=" * 60)
