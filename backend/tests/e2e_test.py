"""End-to-end test of NeuroGraph backend."""

import asyncio
import sys
from uuid import UUID

import httpx


BASE_URL = "http://localhost:8000"


class TestRunner:
    """E2E test runner."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.token = None
    
    def test(self, name: str, condition: bool, error: str = ""):
        """Record test result."""
        if condition:
            print(f"✅ {name}")
            self.passed += 1
        else:
            print(f"❌ {name}: {error}")
            self.failed += 1
    
    def summary(self):
        """Print summary."""
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Total: {total} | Passed: {self.passed} | Failed: {self.failed}")
        print(f"Success rate: {self.passed/total*100:.1f}%" if total > 0 else "No tests run")
        return self.failed == 0


async def test_health_endpoints(runner: TestRunner):
    """Test health check endpoints."""
    print("\n🔍 Testing Health Endpoints...")
    
    async with httpx.AsyncClient() as client:
        # Test /health
        resp = await client.get(f"{BASE_URL}/health")
        runner.test(
            "GET /health returns 200",
            resp.status_code == 200,
            f"Status: {resp.status_code}"
        )
        runner.test(
            "/health returns healthy status",
            resp.json().get("status") == "healthy",
            f"Response: {resp.json()}"
        )
        
        # Test /ready
        resp = await client.get(f"{BASE_URL}/ready")
        runner.test(
            "GET /ready returns 200",
            resp.status_code == 200,
            f"Status: {resp.status_code}"
        )
        data = resp.json()
        runner.test(
            "/ready shows neo4j is ready",
            data.get("neo4j") is True,
            f"neo4j: {data.get('neo4j')}"
        )
        runner.test(
            "/ready shows postgres is ready",
            data.get("postgres") is True,
            f"postgres: {data.get('postgres')}"
        )
        runner.test(
            "/ready shows redis is ready",
            data.get("redis") is True,
            f"redis: {data.get('redis')}"
        )


async def test_auth_flow(runner: TestRunner):
    """Test authentication flow."""
    print("\n🔐 Testing Authentication...")
    
    async with httpx.AsyncClient() as client:
        # Test login with seeded user
        form_data = {
            "username": "alice@example.com",
            "password": "password123"
        }
        
        resp = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        runner.test(
            "POST /auth/login returns 200",
            resp.status_code == 200,
            f"Status: {resp.status_code}"
        )
        
        data = resp.json()
        runner.test(
            "/auth/login returns access_token",
            "access_token" in data,
            f"Keys: {list(data.keys())}"
        )
        runner.test(
            "/auth/login returns refresh_token",
            "refresh_token" in data,
            f"Keys: {list(data.keys())}"
        )
        
        if "access_token" in data:
            runner.token = data["access_token"]
            
            # Test /auth/me
            headers = {"Authorization": f"Bearer {runner.token}"}
            resp = await client.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
            
            runner.test(
                "GET /auth/me returns 200",
                resp.status_code == 200,
                f"Status: {resp.status_code}"
            )
            
            me_data = resp.json()
            runner.test(
                "/auth/me returns user email",
                me_data.get("email") == "alice@example.com",
                f"Email: {me_data.get('email')}"
            )


async def test_memory_endpoints(runner: TestRunner):
    """Test memory endpoints."""
    print("\n💾 Testing Memory Endpoints...")
    
    if not runner.token:
        print("⚠️ Skipping memory tests - no auth token")
        return
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {
            "Authorization": f"Bearer {runner.token}",
            "Content-Type": "application/json"
        }
        
        # Test remember (store memory)
        memory_data = {
            "content": "Alice is investigating Device X for potential fraud",
            "layer": "personal"
        }
        
        resp = await client.post(
            f"{BASE_URL}/api/v1/memory/remember",
            json=memory_data,
            headers=headers
        )
        
        runner.test(
            "POST /memory/remember returns 200",
            resp.status_code == 200,
            f"Status: {resp.status_code}, Body: {resp.text[:200]}"
        )
        
        if resp.status_code == 200:
            data = resp.json()
            runner.test(
                "/memory/remember returns memory ID",
                "id" in data,
                f"Response: {data}"
            )
            runner.test(
                "/memory/remember returns content",
                data.get("content") == memory_data["content"],
                f"Content: {data.get('content')}"
            )
        
        # Test recall (search memory)
        search_data = {
            "query": "fraud detection",
            "layers": ["personal", "tenant", "global"],
            "max_results": 10
        }
        
        try:
            resp = await client.post(
                f"{BASE_URL}/api/v1/memory/recall",
                json=search_data,
                headers=headers
            )
            
            runner.test(
                "POST /memory/recall returns 200",
                resp.status_code == 200,
                f"Status: {resp.status_code}"
            )
            
            if resp.status_code == 200:
                results = resp.json()
                runner.test(
                    "/memory/recall returns list",
                    isinstance(results, list),
                    f"Type: {type(results)}"
                )
        except Exception as e:
            runner.test(
                "POST /memory/recall succeeds",
                False,
                f"Error: {str(e)}"
            )


async def test_chat_endpoints(runner: TestRunner):
    """Test chat endpoints."""
    print("\n💬 Testing Chat Endpoints...")
    
    if not runner.token:
        print("⚠️ Skipping chat tests - no auth token")
        return
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {
            "Authorization": f"Bearer {runner.token}",
            "Content-Type": "application/json"
        }
        
        # Test chat message
        chat_data = {
            "content": "Who should I contact about fraud detection?",
            "layer": "personal"
        }
        
        try:
            resp = await client.post(
                f"{BASE_URL}/api/v1/chat/message",
                json=chat_data,
                headers=headers
            )
            
            runner.test(
                "POST /chat/message returns 200",
                resp.status_code == 200,
                f"Status: {resp.status_code}"
            )
            
            if resp.status_code == 200:
                data = resp.json()
                runner.test(
                    "/chat/message returns content",
                    "content" in data,
                    f"Keys: {list(data.keys())}"
                )
                runner.test(
                    "/chat/message returns conversation_id",
                    "conversation_id" in data,
                    f"Keys: {list(data.keys())}"
                )
        except Exception as e:
            runner.test(
                "POST /chat/message succeeds",
                False,
                f"Error: {str(e)}"
            )


async def test_graph_endpoints(runner: TestRunner):
    """Test graph visualization endpoints."""
    print("\n📊 Testing Graph Endpoints...")
    
    if not runner.token:
        print("⚠️ Skipping graph tests - no auth token")
        return
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {"Authorization": f"Bearer {runner.token}"}
        
        try:
            # Test subgraph query
            resp = await client.get(
                f"{BASE_URL}/api/v1/graph/subgraph?entity=Alice&max_hops=2",
                headers=headers
            )
            
            runner.test(
                "GET /graph/subgraph returns 200",
                resp.status_code == 200,
                f"Status: {resp.status_code}"
            )
        except Exception as e:
            runner.test(
                "GET /graph/subgraph succeeds",
                False,
                f"Error: {str(e)}"
            )


async def main():
    """Run all E2E tests."""
    print("=" * 60)
    print("NeuroGraph Backend - End-to-End Tests")
    print("=" * 60)
    
    runner = TestRunner()
    
    try:
        await test_health_endpoints(runner)
        await test_auth_flow(runner)
        await test_memory_endpoints(runner)
        await test_chat_endpoints(runner)
        await test_graph_endpoints(runner)
        
        success = runner.summary()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
