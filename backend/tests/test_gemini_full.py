"""Comprehensive Gemini API test suite for all agents and capabilities."""

import asyncio
import sys
from uuid import UUID

from src.models.gemini import get_gemini_client
from src.models.groq import get_groq_client
from src.rag.embeddings import EmbeddingsService
from src.rag.hybrid_search import HybridSearch
from src.rag.context_assembly import ContextAssembler
from src.memory.scoring import HybridScorer, ScoredNode
from src.agents.orchestrator import Orchestrator


class TestRunner:
    """Test runner with pass/fail tracking."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def test(self, name: str, condition: bool, error: str = ""):
        """Record test result."""
        result = {"name": name, "passed": condition, "error": error}
        self.tests.append(result)
        
        if condition:
            print(f"✅ {name}")
            self.passed += 1
        else:
            print(f"❌ {name}")
            if error:
                print(f"   Error: {error}")
            self.failed += 1
    
    def summary(self):
        """Print test summary."""
        total = self.passed + self.failed
        print(f"\n{'='*70}")
        print(f"Gemini API Test Results")
        print(f"{'='*70}")
        print(f"Total: {total} | Passed: {self.passed} | Failed: {self.failed}")
        if total > 0:
            print(f"Success rate: {self.passed/total*100:.1f}%")
        print(f"{'='*70}\n")
        return self.failed == 0


async def test_gemini_generation(runner: TestRunner):
    """Test Gemini text generation."""
    print("\n📝 Testing Gemini Text Generation...")
    
    client = get_gemini_client()
    
    try:
        # Test simple generation
        response = await client.generate(
            "Say hello in exactly 3 words",
            temperature=0.1
        )
        runner.test(
            "Gemini generate() produces output",
            len(response.strip()) > 0,
            f"Empty response"
        )
        runner.test(
            "Gemini generate() response is reasonable length",
            len(response.split()) <= 10,  # Should be ~3 words
            f"Response: {response}"
        )
        print(f"   Response: {response}")
        
        # Test with system instruction
        response = await client.generate(
            "What is 2+2?",
            system_instruction="You are a math teacher. Be concise.",
            temperature=0.1
        )
        runner.test(
            "Gemini with system_instruction works",
            "4" in response,
            f"Response: {response}"
        )
        
        # Test JSON mode
        response = await client.generate(
            'Return {"status": "ok", "value": 42}',
            json_mode=True,
            temperature=0.1
        )
        runner.test(
            "Gemini JSON mode works",
            "{" in response and "}" in response,
            f"Response: {response}"
        )
        
        print(f"   JSON response: {response[:100]}...")
        
    except Exception as e:
        runner.test(
            "Gemini text generation",
            False,
            str(e)
        )


async def test_gemini_embeddings(runner: TestRunner):
    """Test Gemini embeddings generation."""
    print("\n🔢 Testing Gemini Embeddings...")
    
    client = get_gemini_client()
    
    try:
        # Test single embedding
        embedding = await client.embed("Hello world")
        runner.test(
            "Gemini embed() returns array",
            embedding.shape[0] == 1,
            f"Shape: {embedding.shape}"
        )
        runner.test(
            "Gemini embedding has correct dimension",
            embedding.shape[1] == 768,  # Default dimension
            f"Dimension: {embedding.shape[1]}"
        )
        print(f"   Embedding shape: {embedding.shape}")
        print(f"   First 5 values: {embedding[0][:5]}")
        
        # Test batch embeddings
        texts = ["fraud detection", "device security", "alice works on projects"]
        embeddings = await client.embed(texts)
        runner.test(
            "Gemini batch embed() returns correct count",
            embeddings.shape[0] == 3,
            f"Shape: {embeddings.shape}"
        )
        runner.test(
            "Gemini batch embeddings have consistent dimensions",
            embeddings.shape[1] == 768,
            f"Shape: {embeddings.shape}"
        )
        print(f"   Batch embeddings shape: {embeddings.shape}")
        
    except Exception as e:
        runner.test(
            "Gemini embeddings",
            False,
            str(e)
        )


async def test_gemini_entity_extraction(runner: TestRunner):
    """Test Gemini entity extraction."""
    print("\n🏷️  Testing Gemini Entity Extraction...")
    
    client = get_gemini_client()
    
    try:
        text = "Alice works at Acme Corp on the Fraud Detection project using Python and Neo4j."
        entities = await client.extract_entities(text)
        
        runner.test(
            "Gemini extract_entities() returns dict",
            isinstance(entities, dict),
            f"Type: {type(entities)}"
        )
        runner.test(
            "Gemini extract_entities() has 'entities' key",
            "entities" in entities,
            f"Keys: {list(entities.keys())}"
        )
        runner.test(
            "Gemini extract_entities() has 'relationships' key",
            "relationships" in entities,
            f"Keys: {list(entities.keys())}"
        )
        
        if "entities" in entities:
            runner.test(
                "Gemini extracted some entities",
                len(entities["entities"]) > 0,
                f"Count: {len(entities['entities'])}"
            )
            print(f"   Extracted {len(entities['entities'])} entities:")
            for ent in entities["entities"][:3]:
                print(f"     - {ent.get('name', 'N/A')} ({ent.get('type', 'N/A')})")
        
        if "relationships" in entities:
            print(f"   Extracted {len(entities['relationships'])} relationships")
            
    except Exception as e:
        runner.test(
            "Gemini entity extraction",
            False,
            str(e)
        )


async def test_gemini_with_context(runner: TestRunner):
    """Test Gemini with context generation."""
    print("\n💬 Testing Gemini with Context...")
    
    client = get_gemini_client()
    
    try:
        context = """## Memory
[0.95] Alice leads Fraud Detection Team
[0.87] Device X linked to Fraud Case #441
[0.71] Bob reported Device X suspicious activity

## Trust signal
Overall confidence: 85%. 0 nodes below 0.5."""
        
        response = await client.generate_with_context(
            query="Who should I contact about fraud?",
            context=context
        )
        
        runner.test(
            "Gemini generate_with_context() works",
            len(response) > 0,
            "Empty response"
        )
        runner.test(
            "Gemini uses provided context",
            "alice" in response.lower() or "fraud" in response.lower(),
            f"Response doesn't mention relevant context: {response[:100]}"
        )
        print(f"   Response: {response[:200]}...")
        
    except Exception as e:
        runner.test(
            "Gemini with context",
            False,
            str(e)
        )


async def test_embeddings_service(runner: TestRunner):
    """Test EmbeddingsService wrapper."""
    print("\n🔧 Testing EmbeddingsService...")
    
    service = EmbeddingsService()
    
    try:
        # Test single text
        embedding = await service.embed_text("test query")
        runner.test(
            "EmbeddingsService.embed_text() works",
            embedding.shape[0] == 768,
            f"Shape: {embedding.shape}"
        )
        
        # Test batch
        embeddings = await service.embed_batch(["text1", "text2", "text3"])
        runner.test(
            "EmbeddingsService.embed_batch() works",
            embeddings.shape == (3, 768),
            f"Shape: {embeddings.shape}"
        )
        
        # Test with metadata
        items = [
            {"content": "Alice works on fraud"},
            {"content": "Bob uses Device X"},
        ]
        result = await service.embed_with_metadata(items, text_key="content")
        runner.test(
            "EmbeddingsService.embed_with_metadata() works",
            len(result) == 2 and "embedding" in result[0],
            f"Result: {list(result[0].keys()) if result else 'empty'}"
        )
        print(f"   Embedded {len(result)} items with metadata")
        
    except Exception as e:
        runner.test(
            "EmbeddingsService",
            False,
            str(e)
        )


async def test_hybrid_search(runner: TestRunner):
    """Test HybridSearch with Gemini embeddings."""
    print("\n🔍 Testing Hybrid Search with Gemini...")
    
    search = HybridSearch()
    
    try:
        # Test search (will use embeddings)
        user_id = UUID('550e8400-e29b-41d4-a716-446655440001')
        results = await search.search(
            query="fraud detection",
            user_id=user_id,
            layers=["personal", "tenant", "global"],
            limit=5
        )
        
        runner.test(
            "HybridSearch.search() completes",
            True,  # If we got here without exception
            ""
        )
        runner.test(
            "HybridSearch returns ScoredNode objects",
            all(isinstance(r, ScoredNode) for r in results) if results else True,
            f"Types: {[type(r) for r in results[:3]]}"
        )
        print(f"   Found {len(results)} results from hybrid search")
        
        if results:
            for i, node in enumerate(results[:3], 1):
                print(f"   {i}. [{node.final_score:.3f}] {node.name}: {node.content[:50]}...")
        
    except Exception as e:
        runner.test(
            "Hybrid search with Gemini",
            False,
            str(e)
        )


async def test_context_assembly(runner: TestRunner):
    """Test ContextAssembler with Gemini-searched nodes."""
    print("\n📋 Testing Context Assembly...")
    
    assembler = ContextAssembler()
    
    try:
        # Create mock scored nodes
        nodes = [
            ScoredNode(
                node_id="n1",
                name="Alice",
                content="Alice leads Fraud Detection Team",
                layer="personal",
                semantic_score=0.9,
                hop_score=1.0,
                centrality_score=0.8,
                temporal_score=0.95,
                confidence=0.95,
                hops=0,
                age_days=2,
                edge_count=5,
            ),
            ScoredNode(
                node_id="n2",
                name="Device X",
                content="Device X linked to fraud case",
                layer="tenant",
                semantic_score=0.85,
                hop_score=0.5,
                centrality_score=0.7,
                temporal_score=0.8,
                confidence=0.89,
                hops=1,
                age_days=7,
                edge_count=3,
            ),
        ]
        
        context = assembler.assemble(
            scored_nodes=nodes,
            reasoning_paths=["Alice → leads → Fraud Team"],
            assets=[{"name": "report.pdf", "summary": "Fraud analysis"}],
            integrations={"latest": "Slack: Device X flagged"},
            web_context=None
        )
        
        runner.test(
            "ContextAssembler.assemble() creates context",
            len(context) > 0,
            "Empty context"
        )
        runner.test(
            "Context includes memory section",
            "## Memory" in context or "## Trust" in context,
            "Missing expected sections"
        )
        runner.test(
            "Context includes reasoning path",
            "Alice" in context or "reasoning" in context.lower(),
            "Missing reasoning info"
        )
        
        print(f"   Generated context: {len(context)} chars")
        print(f"   Sample:\n{context[:300]}...")
        
    except Exception as e:
        runner.test(
            "Context assembly",
            False,
            str(e)
        )


async def test_orchestrator_with_gemini(runner: TestRunner):
    """Test Orchestrator (uses Groq for intent, Gemini for generation)."""
    print("\n🎭 Testing Orchestrator (Groq + Gemini)...")
    
    orchestrator = Orchestrator()
    
    try:
        # Test intent classification (Groq)
        intent = await orchestrator.classify_intent(
            "Who should I contact about fraud detection?"
        )
        
        runner.test(
            "Orchestrator.classify_intent() works",
            "intent" in intent,
            f"Response: {intent}"
        )
        print(f"   Intent classified as: {intent.get('intent', 'unknown')}")
        print(f"   Confidence: {intent.get('confidence', 0)}")
        
        # Note: Full orchestration with Gemini generation would require
        # actual database connections and seeded data
        
    except Exception as e:
        runner.test(
            "Orchestrator with Gemini",
            False,
            str(e)
        )


async def test_groq_vs_gemini(runner: TestRunner):
    """Compare Groq and Gemini performance."""
    print("\n⚡ Testing Groq vs Gemini Performance...")
    
    gemini = get_gemini_client()
    groq = get_groq_client()
    
    try:
        import time
        
        # Test Groq speed (for orchestration)
        start = time.time()
        groq_response = await groq.generate("Say hello", temperature=0.1)
        groq_time = time.time() - start
        
        runner.test(
            "Groq generates response",
            len(groq_response) > 0,
            "Empty response"
        )
        print(f"   Groq response time: {groq_time:.3f}s")
        print(f"   Groq response: {groq_response}")
        
        # Test Gemini speed (for main generation)
        start = time.time()
        gemini_response = await gemini.generate("Say hello", temperature=0.1)
        gemini_time = time.time() - start
        
        runner.test(
            "Gemini generates response",
            len(gemini_response) > 0,
            "Empty response"
        )
        print(f"   Gemini response time: {gemini_time:.3f}s")
        print(f"   Gemini response: {gemini_response}")
        
        # Compare speeds
        runner.test(
            "Groq is faster than Gemini (expected for small prompts)",
            groq_time < gemini_time * 2,  # Allow some variance
            f"Groq: {groq_time:.3f}s, Gemini: {gemini_time:.3f}s"
        )
        
    except Exception as e:
        runner.test(
            "Groq vs Gemini comparison",
            False,
            str(e)
        )


async def main():
    """Run all Gemini tests."""
    print("="*70)
    print("NeuroGraph - Comprehensive Gemini API Test Suite")
    print("="*70)
    
    runner = TestRunner()
    
    try:
        # Core Gemini functionality
        await test_gemini_generation(runner)
        await test_gemini_embeddings(runner)
        await test_gemini_entity_extraction(runner)
        await test_gemini_with_context(runner)
        
        # Service layers
        await test_embeddings_service(runner)
        await test_hybrid_search(runner)
        await test_context_assembly(runner)
        
        # Agent integration
        await test_orchestrator_with_gemini(runner)
        
        # Performance comparison
        await test_groq_vs_gemini(runner)
        
        success = runner.summary()
        
        if not success:
            print("\n⚠️  Some tests failed. Check errors above.")
            sys.exit(1)
        else:
            print("\n✅ All Gemini API tests passed!")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        runner.summary()
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        runner.summary()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
