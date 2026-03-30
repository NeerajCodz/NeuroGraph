"""
Comprehensive End-to-End Test Suite for NeuroGraph
===================================================

Tests the full user journey through the API:
1. User registration and authentication
2. Tenant creation and membership
3. Memory storage (personal, tenant, global)
4. Memory recall with semantic search
5. Chat with context
6. Graph operations

Uses the real API with live databases.
"""

import asyncio
import httpx
import json
from datetime import datetime
from uuid import uuid4
from dataclasses import dataclass, field
from typing import Any

BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"


@dataclass
class TestResult:
    """Single test result."""
    name: str
    passed: bool
    duration_ms: float
    error: str = ""
    details: dict = field(default_factory=dict)


@dataclass 
class TestReport:
    """Full test report."""
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    results: list[TestResult] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: datetime | None = None
    
    def add(self, result: TestResult):
        self.results.append(result)
        self.total += 1
        if result.passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def success_rate(self) -> float:
        if self.total == 0:
            return 0
        return (self.passed / self.total) * 100
    
    def to_markdown(self) -> str:
        """Generate markdown report."""
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time else 0
        
        lines = [
            "# NeuroGraph E2E Test Report",
            "",
            f"**Generated:** {datetime.utcnow().isoformat()}Z",
            f"**Duration:** {duration:.2f}s",
            "",
            "## Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Tests | {self.total} |",
            f"| Passed | {self.passed} ✅ |",
            f"| Failed | {self.failed} ❌ |",
            f"| Success Rate | {self.success_rate():.1f}% |",
            "",
            "## Test Results",
            "",
        ]
        
        # Group by category
        categories: dict[str, list[TestResult]] = {}
        for r in self.results:
            cat = r.name.split(":")[0] if ":" in r.name else "Other"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(r)
        
        for cat, tests in categories.items():
            lines.append(f"### {cat}")
            lines.append("")
            lines.append("| Test | Status | Duration | Details |")
            lines.append("|------|--------|----------|---------|")
            
            for t in tests:
                status = "✅ Pass" if t.passed else "❌ Fail"
                details = t.error if t.error else json.dumps(t.details) if t.details else ""
                details = details[:100] + "..." if len(details) > 100 else details
                name = t.name.split(":", 1)[1] if ":" in t.name else t.name
                lines.append(f"| {name} | {status} | {t.duration_ms:.0f}ms | {details} |")
            
            lines.append("")
        
        # Failed tests detail
        failed = [r for r in self.results if not r.passed]
        if failed:
            lines.append("## Failed Test Details")
            lines.append("")
            for f in failed:
                lines.append(f"### ❌ {f.name}")
                lines.append(f"- **Error:** {f.error}")
                if f.details:
                    lines.append(f"- **Details:** ```json\n{json.dumps(f.details, indent=2)}\n```")
                lines.append("")
        
        return "\n".join(lines)


class E2ETestRunner:
    """End-to-end test runner."""
    
    def __init__(self):
        self.report = TestReport()
        self.client: httpx.AsyncClient | None = None
        self.token: str | None = None
        self.user_id: str | None = None
        self.tenant_id: str | None = None
        
    async def setup(self):
        """Setup test client."""
        self.client = httpx.AsyncClient(timeout=60.0)
        
    async def teardown(self):
        """Cleanup."""
        if self.client:
            await self.client.aclose()
    
    def auth_headers(self) -> dict:
        """Get auth headers."""
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}
    
    async def run_test(self, name: str, test_func) -> TestResult:
        """Run a single test and record result."""
        start = datetime.utcnow()
        try:
            result = await test_func()
            duration = (datetime.utcnow() - start).total_seconds() * 1000
            
            if isinstance(result, dict):
                passed = result.get("passed", True)
                error = result.get("error", "")
                details = result.get("details", {})
            else:
                passed = bool(result)
                error = "" if passed else "Test returned falsy value"
                details = {}
            
            return TestResult(
                name=name,
                passed=passed,
                duration_ms=duration,
                error=error,
                details=details,
            )
        except Exception as e:
            duration = (datetime.utcnow() - start).total_seconds() * 1000
            return TestResult(
                name=name,
                passed=False,
                duration_ms=duration,
                error=str(e),
            )
    
    # ===================
    # Health Tests
    # ===================
    
    async def test_health_endpoint(self):
        """Test /health endpoint."""
        r = await self.client.get(f"{BASE_URL}/health")
        return {"passed": r.status_code == 200, "details": r.json()}
    
    async def test_ready_endpoint(self):
        """Test /ready endpoint."""
        r = await self.client.get(f"{BASE_URL}/ready")
        data = r.json()
        all_ready = all([
            data.get("neo4j") == True,
            data.get("postgres") == True,
            data.get("redis") == True,
        ])
        return {"passed": r.status_code == 200 and all_ready, "details": data}
    
    # ===================
    # Auth Tests
    # ===================
    
    async def test_login_with_seeded_user(self):
        """Test login with seeded Alice user."""
        r = await self.client.post(
            f"{API_V1}/auth/login",
            data={"username": "alice@example.com", "password": "password123"},
        )
        if r.status_code == 200:
            data = r.json()
            self.token = data.get("access_token")
            return {"passed": bool(self.token), "details": {"token_prefix": self.token[:20] if self.token else None}}
        return {"passed": False, "error": r.text}
    
    async def test_get_current_user(self):
        """Test /auth/me endpoint."""
        r = await self.client.get(f"{API_V1}/auth/me", headers=self.auth_headers())
        if r.status_code == 200:
            data = r.json()
            self.user_id = data.get("id")
            return {"passed": "email" in data, "details": {"email": data.get("email"), "id": self.user_id}}
        return {"passed": False, "error": r.text}
    
    async def test_register_new_user(self):
        """Test user registration."""
        email = f"test_{uuid4().hex[:8]}@example.com"
        r = await self.client.post(
            f"{API_V1}/auth/register",
            json={
                "email": email,
                "password": "TestPassword123!",
                "full_name": "Test User",
            },
        )
        # 201 for created or 409 if exists
        return {"passed": r.status_code in [201, 409, 200], "details": {"email": email, "status": r.status_code}}
    
    async def test_invalid_login(self):
        """Test login with wrong credentials."""
        r = await self.client.post(
            f"{API_V1}/auth/login",
            data={"username": "wrong@example.com", "password": "wrongpass"},
        )
        # Should return 401 Unauthorized or 403 Forbidden
        return {"passed": r.status_code in [401, 403], "details": {"status": r.status_code}}
    
    # ===================
    # Memory Tests
    # ===================
    
    async def test_remember_personal_memory(self):
        """Test storing personal memory."""
        r = await self.client.post(
            f"{API_V1}/memory/remember",
            headers=self.auth_headers(),
            json={
                "content": "I prefer working on AI projects using Python and FastAPI. My focus is on NLP and graph databases.",
                "layer": "personal",
            },
        )
        if r.status_code == 200:
            data = r.json()
            return {
                "passed": "id" in data and "entities_extracted" in data,
                "details": {
                    "memory_id": data.get("id"),
                    "entities": data.get("entities_extracted", [])[:5],
                },
            }
        return {"passed": False, "error": r.text}
    
    async def test_remember_tenant_memory(self):
        """Test storing tenant memory."""
        r = await self.client.post(
            f"{API_V1}/memory/remember",
            headers=self.auth_headers(),
            json={
                "content": "Our Q2 OKRs include launching the new fraud detection feature and improving system latency by 40%.",
                "layer": "tenant",
                "tenant_id": "550e8400-e29b-41d4-a716-446655440010",
            },
        )
        return {"passed": r.status_code == 200, "details": r.json() if r.status_code == 200 else {"error": r.text}}
    
    async def test_remember_global_memory(self):
        """Test storing global memory."""
        r = await self.client.post(
            f"{API_V1}/memory/remember",
            headers=self.auth_headers(),
            json={
                "content": "NeuroGraph uses a hybrid search approach combining vector similarity with graph traversal for explainable AI.",
                "layer": "global",
            },
        )
        return {"passed": r.status_code == 200, "details": r.json() if r.status_code == 200 else {"error": r.text}}
    
    async def test_recall_personal_memory(self):
        """Test recalling personal memory."""
        r = await self.client.post(
            f"{API_V1}/memory/recall",
            headers=self.auth_headers(),
            json={
                "query": "What are my AI project preferences?",
                "layers": ["personal"],
                "max_results": 5,
            },
        )
        data = r.json() if r.status_code == 200 else []
        return {
            "passed": r.status_code == 200,
            "details": {"results_count": len(data), "top_result": data[0] if data else None},
        }
    
    async def test_recall_all_layers(self):
        """Test recalling from all memory layers."""
        r = await self.client.post(
            f"{API_V1}/memory/recall",
            headers=self.auth_headers(),
            json={
                "query": "fraud detection and AI systems",
                "layers": ["personal", "tenant", "global"],
                "max_results": 10,
            },
        )
        data = r.json() if r.status_code == 200 else []
        return {
            "passed": r.status_code == 200,
            "details": {"results_count": len(data)},
        }
    
    async def test_memory_search(self):
        """Test GET memory search endpoint."""
        r = await self.client.get(
            f"{API_V1}/memory/search",
            headers=self.auth_headers(),
            params={"q": "Python programming", "limit": 5},
        )
        return {"passed": r.status_code == 200, "details": {"status": r.status_code}}
    
    # ===================
    # Chat Tests
    # ===================
    
    async def test_chat_message(self):
        """Test chat message endpoint."""
        r = await self.client.post(
            f"{API_V1}/chat/message",
            headers=self.auth_headers(),
            json={
                "content": "What do you know about fraud detection systems?",
                "layer": "personal",
                "include_global": True,
            },
        )
        if r.status_code == 200:
            data = r.json()
            return {
                "passed": "content" in data and "confidence" in data,
                "details": {
                    "response_length": len(data.get("content", "")),
                    "confidence": data.get("confidence"),
                    "has_reasoning": bool(data.get("reasoning_path")),
                },
            }
        return {"passed": False, "error": r.text}
    
    async def test_chat_conversation_history(self):
        """Test getting conversation history."""
        r = await self.client.get(
            f"{API_V1}/chat/conversations",
            headers=self.auth_headers(),
            params={"limit": 10},
        )
        return {"passed": r.status_code == 200, "details": {"status": r.status_code}}
    
    # ===================
    # Graph Tests  
    # ===================
    
    async def test_graph_nodes(self):
        """Test getting graph entities/nodes."""
        r = await self.client.get(
            f"{API_V1}/graph/entities",
            headers=self.auth_headers(),
            params={"limit": 10},
        )
        return {"passed": r.status_code == 200, "details": {"status": r.status_code}}
    
    async def test_graph_relationships(self):
        """Test getting graph relationships."""
        r = await self.client.get(
            f"{API_V1}/graph/visualize",
            headers=self.auth_headers(),
            params={"depth": 2, "max_nodes": 50},
        )
        return {"passed": r.status_code == 200, "details": {"status": r.status_code}}
    
    # ===================
    # Additional Tests
    # ===================
    
    async def test_api_docs(self):
        """Test OpenAPI docs endpoint."""
        r = await self.client.get(f"{BASE_URL}/docs")
        return {"passed": r.status_code == 200, "details": {"status": r.status_code}}
    
    # ===================
    # Run All Tests
    # ===================
    
    async def run_all(self):
        """Run all tests."""
        await self.setup()
        
        try:
            tests = [
                # Health
                ("Health: Basic health check", self.test_health_endpoint),
                ("Health: Readiness check (all DBs)", self.test_ready_endpoint),
                
                # Auth
                ("Auth: Login with seeded user", self.test_login_with_seeded_user),
                ("Auth: Get current user", self.test_get_current_user),
                ("Auth: Register new user", self.test_register_new_user),
                ("Auth: Invalid login rejected", self.test_invalid_login),
                
                # Memory
                ("Memory: Store personal memory", self.test_remember_personal_memory),
                ("Memory: Store tenant memory", self.test_remember_tenant_memory),
                ("Memory: Store global memory", self.test_remember_global_memory),
                ("Memory: Recall personal", self.test_recall_personal_memory),
                ("Memory: Recall all layers", self.test_recall_all_layers),
                ("Memory: Search endpoint", self.test_memory_search),
                
                # Chat
                ("Chat: Send message", self.test_chat_message),
                ("Chat: Get history", self.test_chat_conversation_history),
                
                # Graph
                ("Graph: List entities", self.test_graph_nodes),
                ("Graph: Visualize graph", self.test_graph_relationships),
                
                # Other
                ("Docs: OpenAPI docs available", self.test_api_docs),
            ]
            
            print("\n" + "="*70)
            print("NeuroGraph E2E Test Suite")
            print("="*70 + "\n")
            
            for name, test_func in tests:
                result = await self.run_test(name, test_func)
                self.report.add(result)
                
                status = "✅" if result.passed else "❌"
                print(f"{status} {name} ({result.duration_ms:.0f}ms)")
                if not result.passed and result.error:
                    print(f"   └─ Error: {result.error[:100]}")
            
            self.report.end_time = datetime.utcnow()
            
            print("\n" + "="*70)
            print(f"Results: {self.report.passed}/{self.report.total} passed ({self.report.success_rate():.1f}%)")
            print("="*70 + "\n")
            
        finally:
            await self.teardown()
        
        return self.report


async def main():
    """Run E2E tests and generate report."""
    runner = E2ETestRunner()
    report = await runner.run_all()
    
    # Write markdown report
    report_path = "../docs/TEST_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report.to_markdown())
    
    print(f"📄 Report saved to: {report_path}")
    
    return 0 if report.failed == 0 else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
