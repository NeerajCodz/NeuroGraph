"""Unit tests for context assembly module."""

import pytest
from unittest.mock import MagicMock


class TestContextAssembler:
    """Tests for ContextAssembler class."""

    @pytest.fixture
    def assembler(self, mock_settings):
        """Create ContextAssembler instance."""
        from src.rag.context_assembly import ContextAssembler
        return ContextAssembler()

    def test_init(self, assembler):
        """Test assembler initialization."""
        assert assembler.total_budget == 4000
        assert assembler.graph_budget == 2000
        assert assembler.asset_budget == 800
        assert assembler.integration_budget == 600
        assert assembler.web_budget == 400

    def test_build_memory_section(self, assembler, sample_scored_nodes):
        """Test building memory section."""
        section = assembler._build_memory_section(sample_scored_nodes)
        
        assert "## Memory" in section
        assert "Test Node 1" in section
        assert "Test Node 2" in section

    def test_build_memory_section_with_warnings(self, assembler):
        """Test memory section includes warnings for low confidence."""
        from src.memory.scoring import ScoredNode
        
        nodes = [
            ScoredNode(
                node_id="1",
                name="Low Confidence Node",
                content="Content",
                layer="personal",
                semantic_score=0.5,
                hop_score=0.5,
                centrality_score=0.5,
                temporal_score=0.5,
                confidence=0.3,  # Low confidence
                hops=2,
                age_days=45,  # Old
                edge_count=1,
            ),
        ]
        
        section = assembler._build_memory_section(nodes)
        
        assert "⚠️" in section or "low confidence" in section.lower()

    def test_build_reasoning_section(self, assembler):
        """Test building reasoning path section."""
        paths = [
            "Alice → leads → Fraud Team",
            "Bob → reported → Device X",
        ]
        
        section = assembler._build_reasoning_section(paths)
        
        assert "## Reasoning" in section
        assert "Alice" in section
        assert "Bob" in section

    def test_build_assets_section(self, assembler):
        """Test building assets section."""
        assets = [
            {"name": "report.pdf", "summary": "Financial report Q4"},
            {"name": "data.csv", "summary": "Transaction data"},
        ]
        
        section = assembler._build_assets_section(assets)
        
        assert "## Related" in section
        assert "report.pdf" in section
        assert "data.csv" in section

    def test_build_trust_section(self, assembler, sample_scored_nodes):
        """Test building trust signal section."""
        section = assembler._build_trust_section(sample_scored_nodes)
        
        assert "## Trust" in section or "confidence" in section.lower()

    def test_assemble_full_context(self, assembler, sample_scored_nodes):
        """Test assembling complete context."""
        context = assembler.assemble(
            scored_nodes=sample_scored_nodes,
            reasoning_paths=["A → B → C"],
            assets=[{"name": "file.txt", "summary": "Test file"}],
            integrations={"latest": "Slack: Hello"},
            web_context=None,
        )
        
        assert "## Memory" in context
        assert "## Reasoning" in context
        assert "## Trust" in context

    def test_assemble_respects_token_budget(self, assembler, mock_settings):
        """Test that assembly respects token budget."""
        from src.memory.scoring import ScoredNode
        
        # Create many nodes
        nodes = [
            ScoredNode(
                node_id=f"node_{i}",
                name=f"Node {i}",
                content=f"Content for node {i}",
                layer="personal",
                semantic_score=0.9 - i * 0.01,
                hop_score=1.0,
                centrality_score=0.5,
                temporal_score=0.8,
                confidence=0.9,
                hops=0,
                age_days=1,
                edge_count=5,
            )
            for i in range(100)  # Many nodes
        ]
        
        context = assembler.assemble(
            scored_nodes=nodes,
            reasoning_paths=[],
            assets=[],
            integrations=None,
            web_context=None,
        )
        
        # Context should not exceed token budget
        estimated_tokens = len(context.split()) * 1.3  # Rough estimate
        assert estimated_tokens < 5000  # Some buffer

    def test_web_context_included_when_low_confidence(self, assembler):
        """Test web context is included when graph confidence is low."""
        from src.memory.scoring import ScoredNode
        
        nodes = [
            ScoredNode(
                node_id="1",
                name="Node 1",
                content="Content",
                layer="personal",
                semantic_score=0.5,
                hop_score=0.5,
                centrality_score=0.5,
                temporal_score=0.5,
                confidence=0.4,  # Low confidence
                hops=0,
                age_days=1,
                edge_count=1,
            ),
        ]
        
        context = assembler.assemble(
            scored_nodes=nodes,
            reasoning_paths=[],
            assets=[],
            integrations=None,
            web_context={"summary": "External search results"},
        )
        
        assert "External" in context or "external" in context.lower()

    def test_empty_context(self, assembler):
        """Test assembly with no data."""
        context = assembler.assemble(
            scored_nodes=[],
            reasoning_paths=[],
            assets=[],
            integrations=None,
            web_context=None,
        )
        
        # Should still have structure
        assert context is not None
        assert len(context) > 0
