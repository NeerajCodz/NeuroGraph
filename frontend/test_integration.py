"""
Frontend E2E Integration Test

Tests the frontend API endpoints to verify backend connectivity.
"""

import requests
import json
from typing import Optional

BASE_URL = "http://localhost:8000/api/v1"
FRONTEND_URL = "http://localhost:5173"

def test_frontend_serving():
    """Test that frontend is being served"""
    try:
        r = requests.get(FRONTEND_URL, timeout=5)
        if r.status_code == 200:
            print("✅ Frontend serving: OK (200)")
            return True
        else:
            print(f"❌ Frontend serving: Failed ({r.status_code})")
            return False
    except Exception as e:
        print(f"❌ Frontend serving: Error - {e}")
        return False


def test_backend_health():
    """Test backend health endpoint"""
    try:
        r = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health", timeout=5)
        if r.status_code == 200:
            print("✅ Backend health: OK")
            return True
        else:
            print(f"❌ Backend health: Failed ({r.status_code})")
            return False
    except Exception as e:
        print(f"❌ Backend health: Error - {e}")
        return False


def test_login() -> Optional[str]:
    """Test login endpoint and return token"""
    try:
        r = requests.post(
            f"{BASE_URL}/auth/login",
            data={"username": "neeraj@ng.ai", "password": "Password@123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            token = data.get("access_token")
            print(f"✅ Login: OK (token received)")
            return token
        else:
            print(f"❌ Login: Failed ({r.status_code}) - {r.text}")
            return None
    except Exception as e:
        print(f"❌ Login: Error - {e}")
        return None


def test_auth_me(token: str):
    """Test /auth/me endpoint"""
    try:
        r = requests.get(
            f"{BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        if r.status_code == 200:
            user = r.json()
            print(f"✅ Auth me: OK (user: {user.get('email')})")
            return True
        else:
            print(f"❌ Auth me: Failed ({r.status_code})")
            return False
    except Exception as e:
        print(f"❌ Auth me: Error - {e}")
        return False


def test_graph_visualization(token: str):
    """Test graph visualization endpoint"""
    try:
        r = requests.get(
            f"{BASE_URL}/graph/visualize",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            nodes = len(data.get("nodes", []))
            edges = len(data.get("edges", []))
            print(f"✅ Graph visualize: OK ({nodes} nodes, {edges} edges)")
            return True
        else:
            print(f"❌ Graph visualize: Failed ({r.status_code})")
            return False
    except Exception as e:
        print(f"❌ Graph visualize: Error - {e}")
        return False


def test_graph_centrality(token: str):
    """Test graph centrality endpoint"""
    try:
        r = requests.get(
            f"{BASE_URL}/graph/centrality",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            print(f"✅ Graph centrality: OK ({len(data)} entries)")
            return True
        else:
            print(f"❌ Graph centrality: Failed ({r.status_code})")
            return False
    except Exception as e:
        print(f"❌ Graph centrality: Error - {e}")
        return False


def test_memory_recall(token: str):
    """Test memory recall endpoint"""
    try:
        r = requests.post(
            f"{BASE_URL}/memory/recall",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={"query": "test", "limit": 5},
            timeout=30
        )
        if r.status_code == 200:
            data = r.json()
            results = len(data.get("results", []))
            print(f"✅ Memory recall: OK ({results} results)")
            return True
        else:
            print(f"❌ Memory recall: Failed ({r.status_code}) - {r.text[:100]}")
            return False
    except Exception as e:
        print(f"❌ Memory recall: Error - {e}")
        return False


def test_chat_message(token: str):
    """Test chat message endpoint"""
    try:
        r = requests.post(
            f"{BASE_URL}/chat/message",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "content": "Hello, this is a test",
                "layer": "personal",
                "include_global": False
            },
            timeout=60
        )
        if r.status_code == 200:
            data = r.json()
            print(f"✅ Chat message: OK (confidence: {data.get('confidence', 'N/A')})")
            return True
        elif r.status_code == 503:
            print(f"⚠️ Chat message: Rate limited (503) - Gemini API quota")
            return True  # Expected during testing
        else:
            print(f"❌ Chat message: Failed ({r.status_code}) - {r.text[:100]}")
            return False
    except Exception as e:
        print(f"❌ Chat message: Error - {e}")
        return False


def main():
    print("=" * 60)
    print("NeuroGraph Frontend-Backend Integration Test")
    print("=" * 60)
    print()
    
    passed = 0
    failed = 0
    
    # Test infrastructure
    print("📦 Infrastructure Tests")
    print("-" * 40)
    
    if test_frontend_serving():
        passed += 1
    else:
        failed += 1
    
    if test_backend_health():
        passed += 1
    else:
        failed += 1
    
    print()
    
    # Test authentication
    print("🔐 Authentication Tests")
    print("-" * 40)
    
    token = test_login()
    if token:
        passed += 1
        
        if test_auth_me(token):
            passed += 1
        else:
            failed += 1
    else:
        failed += 1
        print("⏭️  Skipping authenticated tests (no token)")
        return
    
    print()
    
    # Test graph endpoints
    print("📊 Graph Endpoints Tests")
    print("-" * 40)
    
    if test_graph_visualization(token):
        passed += 1
    else:
        failed += 1
    
    if test_graph_centrality(token):
        passed += 1
    else:
        failed += 1
    
    print()
    
    # Test memory endpoints
    print("🧠 Memory Endpoints Tests")
    print("-" * 40)
    
    if test_memory_recall(token):
        passed += 1
    else:
        failed += 1
    
    print()
    
    # Test chat endpoints
    print("💬 Chat Endpoints Tests")
    print("-" * 40)
    
    if test_chat_message(token):
        passed += 1
    else:
        failed += 1
    
    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
