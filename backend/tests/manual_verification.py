"""
Manual Verification Script for NeuroGraph
==========================================

Tests the system as a real user would, verifying:
1. Authentication flow
2. Memory storage and retrieval
3. Confidence scoring
4. RAG pipeline (vector + graph)
5. Context building
6. Agent results
7. Chat orchestration
"""

import asyncio
import httpx
import json
from datetime import datetime
from uuid import uuid4

BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"

# Test data
TEST_MEMORIES = [
    {
        "content": "Alice is the team lead for the fraud detection project. She has 10 years of experience in cybersecurity and holds a CISSP certification.",
        "layer": "personal",
        "expected_entities": ["Alice", "fraud detection", "cybersecurity", "CISSP"],
    },
    {
        "content": "Device X (MAC: AA:BB:CC:DD:EE:FF) was flagged in 3 separate fraud investigations this month. It's linked to suspicious transactions totaling $50,000.",
        "layer": "tenant",
        "tenant_id": "941e88be-466e-481b-8863-a3003dca5128",
        "expected_entities": ["Device X", "fraud", "transactions"],
    },
    {
        "content": "The new ML model for anomaly detection has a 94% accuracy rate. It uses a combination of LSTM networks and attention mechanisms.",
        "layer": "global",
        "expected_entities": ["ML model", "anomaly detection", "LSTM", "attention"],
    },
]

TEST_QUERIES = [
    {
        "query": "Who is responsible for fraud detection?",
        "expected_context": ["Alice", "fraud detection", "team lead"],
    },
    {
        "query": "What do we know about Device X?",
        "expected_context": ["Device X", "fraud", "flagged", "suspicious"],
    },
    {
        "query": "How accurate is our ML model?",
        "expected_context": ["94%", "ML model", "accuracy"],
    },
]


class ManualVerifier:
    """Manual verification testing class."""
    
    def __init__(self):
        self.client: httpx.AsyncClient = None
        self.token: str = None
        self.user_id: str = None
        self.results = []
        
    async def setup(self):
        """Initialize HTTP client."""
        self.client = httpx.AsyncClient(timeout=120.0)
        
    async def teardown(self):
        """Cleanup."""
        if self.client:
            await self.client.aclose()
    
    def log(self, category: str, message: str, data: dict = None, success: bool = True):
        """Log a test result."""
        icon = "✅" if success else "❌"
        print(f"\n{icon} [{category}] {message}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2, default=str)[:500]}")
        self.results.append({
            "category": category,
            "message": message,
            "success": success,
            "data": data,
        })
    
    def auth_headers(self) -> dict:
        """Get auth headers."""
        return {"Authorization": f"Bearer {self.token}"}
    
    async def test_auth_flow(self):
        """Test complete authentication flow."""
        print("\n" + "="*60)
        print("TESTING: Authentication Flow")
        print("="*60)
        
        # 1. Login
        r = await self.client.post(
            f"{API_V1}/auth/login",
            data={"username": "alice@example.com", "password": "password123"},
        )
        if r.status_code == 200:
            data = r.json()
            self.token = data["access_token"]
            self.log("Auth", "Login successful", {"token_prefix": self.token[:50]})
        else:
            self.log("Auth", "Login failed", {"status": r.status_code, "error": r.text}, False)
            return False
        
        # 2. Get user info
        r = await self.client.get(f"{API_V1}/auth/me", headers=self.auth_headers())
        if r.status_code == 200:
            user = r.json()
            self.user_id = user["id"]
            self.log("Auth", "Get user info", {
                "id": user["id"],
                "email": user["email"],
                "full_name": user.get("full_name"),
            })
            # Verify email is correct
            if user["email"] == "alice@example.com":
                self.log("Auth", "Email correct in response")
            else:
                self.log("Auth", f"Email mismatch: expected alice@example.com, got {user['email']}", success=False)
        else:
            self.log("Auth", "Get user info failed", {"error": r.text}, False)
            return False
        
        return True
    
    async def test_memory_storage(self):
        """Test storing memories with entity extraction."""
        print("\n" + "="*60)
        print("TESTING: Memory Storage & Entity Extraction")
        print("="*60)
        
        stored_memories = []
        
        for i, mem in enumerate(TEST_MEMORIES):
            print(f"\n--- Memory {i+1}: {mem['layer'].upper()} layer ---")
            
            # Add delay for rate limiting
            await asyncio.sleep(3)
            
            body = {
                "content": mem["content"],
                "layer": mem["layer"],
            }
            if "tenant_id" in mem:
                body["tenant_id"] = mem["tenant_id"]
            
            r = await self.client.post(
                f"{API_V1}/memory/remember",
                headers=self.auth_headers(),
                json=body,
            )
            
            if r.status_code == 200:
                data = r.json()
                stored_memories.append(data)
                
                # Verify entities were extracted
                extracted = data.get("entities_extracted", [])
                expected = mem["expected_entities"]
                
                found_entities = []
                for exp in expected:
                    found = any(exp.lower() in e.lower() for e in extracted)
                    if found:
                        found_entities.append(exp)
                
                self.log("Memory", f"Stored {mem['layer']} memory", {
                    "id": data.get("id"),
                    "confidence": data.get("confidence"),
                    "entities_found": found_entities,
                    "entities_total": len(extracted),
                })
                
                if len(found_entities) >= len(expected) // 2:
                    self.log("Memory", f"Entity extraction quality: {len(found_entities)}/{len(expected)} expected found")
                else:
                    self.log("Memory", f"Entity extraction poor: only {len(found_entities)}/{len(expected)} expected found", success=False)
            else:
                self.log("Memory", f"Failed to store {mem['layer']} memory", {"error": r.text}, False)
        
        return stored_memories
    
    async def test_memory_recall(self):
        """Test memory recall with semantic search."""
        print("\n" + "="*60)
        print("TESTING: Memory Recall & Semantic Search")
        print("="*60)
        
        for query_test in TEST_QUERIES:
            print(f"\n--- Query: {query_test['query'][:50]}... ---")
            
            # Add delay
            await asyncio.sleep(2)
            
            r = await self.client.post(
                f"{API_V1}/memory/recall",
                headers=self.auth_headers(),
                json={
                    "query": query_test["query"],
                    "layers": ["personal", "tenant", "global"],
                    "max_results": 10,
                    "min_confidence": 0.3,
                },
            )
            
            if r.status_code == 200:
                results = r.json()
                
                if results:
                    # Check if expected context is found
                    all_content = " ".join([r.get("content", "") for r in results])
                    found_expected = [e for e in query_test["expected_context"] if e.lower() in all_content.lower()]
                    
                    self.log("Recall", f"Query returned {len(results)} results", {
                        "query": query_test["query"][:50],
                        "results_count": len(results),
                        "top_score": results[0].get("score") if results else 0,
                        "top_confidence": results[0].get("confidence") if results else 0,
                        "expected_found": found_expected,
                    })
                    
                    # Analyze confidence scores
                    confidences = [r.get("confidence", 0) for r in results]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                    
                    if avg_confidence >= 0.5:
                        self.log("Recall", f"Confidence scores healthy: avg={avg_confidence:.2f}")
                    else:
                        self.log("Recall", f"Low confidence scores: avg={avg_confidence:.2f}", success=False)
                else:
                    self.log("Recall", "No results returned - may need more memories", {
                        "query": query_test["query"]
                    }, success=False)
            else:
                self.log("Recall", "Recall failed", {"error": r.text}, False)
    
    async def test_chat_with_context(self):
        """Test chat endpoint with context building."""
        print("\n" + "="*60)
        print("TESTING: Chat with Context Building")
        print("="*60)
        
        test_messages = [
            "Who should I contact about the fraud detection project?",
            "Tell me about Device X and why it's suspicious.",
            "What's our ML model's accuracy?",
        ]
        
        for msg in test_messages:
            print(f"\n--- Chat: {msg[:50]}... ---")
            
            await asyncio.sleep(1)
            
            r = await self.client.post(
                f"{API_V1}/chat/message",
                headers=self.auth_headers(),
                json={
                    "content": msg,  # Use "content" not "message"
                },
            )
            
            if r.status_code == 200:
                data = r.json()
                
                # Note: response model uses "content" not "response"
                response_text = data.get("content", "")
                
                self.log("Chat", f"Got response", {
                    "message": msg[:40],
                    "response_length": len(response_text),
                    "confidence": data.get("confidence"),
                    "has_reasoning": bool(data.get("reasoning_path")),
                    "response_preview": response_text[:200],
                })
                
                # Check if response has actual content
                if len(response_text) > 20 and data.get("confidence", 0) > 0.5:
                    self.log("Chat", "Response quality OK")
                else:
                    self.log("Chat", "Response is placeholder (chat orchestration not implemented yet)", success=False)
            else:
                self.log("Chat", "Chat failed", {"error": r.text}, False)
    
    async def test_graph_operations(self):
        """Test graph database operations."""
        print("\n" + "="*60)
        print("TESTING: Graph Operations")
        print("="*60)
        
        # 1. List entities
        r = await self.client.get(
            f"{API_V1}/graph/entities",
            headers=self.auth_headers(),
            params={"limit": 20},
        )
        
        if r.status_code == 200:
            entities = r.json()
            self.log("Graph", f"Found {len(entities)} entities", {
                "sample": [e.get("name") for e in entities[:5]] if entities else [],
            })
        else:
            self.log("Graph", "List entities failed", {"error": r.text}, False)
        
        # 2. Get visualization data
        r = await self.client.get(
            f"{API_V1}/graph/visualize",
            headers=self.auth_headers(),
        )
        
        if r.status_code == 200:
            viz = r.json()
            self.log("Graph", "Visualization data retrieved", {
                "nodes_count": len(viz.get("nodes", [])),
                "edges_count": len(viz.get("edges", [])),
            })
        else:
            self.log("Graph", "Visualization failed", {"error": r.text}, False)
    
    async def test_search_endpoint(self):
        """Test the search endpoint directly."""
        print("\n" + "="*60)
        print("TESTING: Search Endpoint")
        print("="*60)
        
        r = await self.client.get(
            f"{API_V1}/memory/search",
            headers=self.auth_headers(),
            params={
                "q": "fraud detection team lead",
                "layers": ["personal", "tenant", "global"],
                "limit": 10,
            },
        )
        
        if r.status_code == 200:
            results = r.json()
            self.log("Search", f"Search returned {len(results)} results", {
                "scores": [r.get("score", 0) for r in results[:5]] if results else [],
            })
        else:
            self.log("Search", "Search failed", {"error": r.text}, False)
    
    def generate_report(self) -> str:
        """Generate verification report."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["success"])
        failed = total - passed
        
        lines = [
            "# NeuroGraph Manual Verification Report",
            "",
            f"**Generated:** {datetime.utcnow().isoformat()}Z",
            "",
            "## Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Checks | {total} |",
            f"| Passed | {passed} ✅ |",
            f"| Failed | {failed} ❌ |",
            f"| Success Rate | {(passed/total*100):.1f}% |" if total > 0 else "| Success Rate | N/A |",
            "",
            "## Detailed Results",
            "",
        ]
        
        # Group by category
        categories = {}
        for r in self.results:
            cat = r["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(r)
        
        for cat, checks in categories.items():
            lines.append(f"### {cat}")
            lines.append("")
            for c in checks:
                icon = "✅" if c["success"] else "❌"
                lines.append(f"- {icon} {c['message']}")
                if c.get("data") and not c["success"]:
                    lines.append(f"  - Details: `{json.dumps(c['data'], default=str)[:200]}`")
            lines.append("")
        
        # Issues summary
        issues = [r for r in self.results if not r["success"]]
        if issues:
            lines.append("## Issues Found")
            lines.append("")
            for i, issue in enumerate(issues, 1):
                lines.append(f"{i}. **{issue['category']}**: {issue['message']}")
            lines.append("")
        
        return "\n".join(lines)
    
    async def run_all(self):
        """Run all verification tests."""
        print("\n" + "="*70)
        print("  NEUROGRAPH MANUAL VERIFICATION TEST SUITE")
        print("="*70)
        
        await self.setup()
        
        try:
            # Run tests in order
            auth_ok = await self.test_auth_flow()
            if not auth_ok:
                print("\n❌ Auth failed - cannot continue")
                return
            
            await self.test_memory_storage()
            await self.test_memory_recall()
            await self.test_chat_with_context()
            await self.test_graph_operations()
            await self.test_search_endpoint()
            
        finally:
            await self.teardown()
        
        # Print summary
        print("\n" + "="*70)
        print("  VERIFICATION COMPLETE")
        print("="*70)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r["success"])
        print(f"\nTotal Checks: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {total - passed} ❌")
        print(f"Success Rate: {(passed/total*100):.1f}%" if total > 0 else "N/A")
        
        # Save report with UTF-8 encoding
        report = self.generate_report()
        with open("../docs/VERIFICATION_REPORT.md", "w", encoding="utf-8") as f:
            f.write(report)
        print("\n📄 Report saved to: docs/VERIFICATION_REPORT.md")
        
        return passed == total


async def main():
    verifier = ManualVerifier()
    success = await verifier.run_all()
    return 0 if success else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
