"""Unit tests for scoring module."""

import pytest
import math
from unittest.mock import MagicMock


class TestHybridScorer:
    """Tests for HybridScorer class."""

    def test_init(self, mock_settings):
        """Test scorer initialization."""
        from src.memory.scoring import HybridScorer
        
        scorer = HybridScorer()
        
        assert scorer.semantic_weight == 0.35
        assert scorer.hop_weight == 0.25
        assert scorer.centrality_weight == 0.20
        assert scorer.temporal_weight == 0.20

    def test_compute_hop_score_zero_hops(self, mock_settings):
        """Test hop score with zero hops."""
        from src.memory.scoring import HybridScorer
        
        scorer = HybridScorer()
        score = scorer._compute_hop_score(0)
        
        assert score == 1.0

    def test_compute_hop_score_one_hop(self, mock_settings):
        """Test hop score with one hop."""
        from src.memory.scoring import HybridScorer
        
        scorer = HybridScorer()
        score = scorer._compute_hop_score(1)
        
        assert score == 0.5

    def test_compute_hop_score_two_hops(self, mock_settings):
        """Test hop score with two hops."""
        from src.memory.scoring import HybridScorer
        
        scorer = HybridScorer()
        score = scorer._compute_hop_score(2)
        
        assert abs(score - 0.333) < 0.01

    def test_compute_centrality_score(self, mock_settings):
        """Test centrality score computation."""
        from src.memory.scoring import HybridScorer
        
        scorer = HybridScorer()
        
        # 5 edges out of 10 max = 0.5
        score = scorer._compute_centrality_score(5, 10)
        assert score == 0.5
        
        # 10 edges out of 10 max = 1.0
        score = scorer._compute_centrality_score(10, 10)
        assert score == 1.0

    def test_compute_centrality_score_zero_max(self, mock_settings):
        """Test centrality score with zero max edges."""
        from src.memory.scoring import HybridScorer
        
        scorer = HybridScorer()
        score = scorer._compute_centrality_score(5, 0)
        
        assert score == 0.0

    def test_score_single_node(self, mock_settings):
        """Test scoring a single node."""
        from src.memory.scoring import HybridScorer, ScoredNode
        
        scorer = HybridScorer()
        
        result = scorer.score(
            semantic_score=0.9,
            hops=1,
            edge_count=5,
            max_edges=10,
            age_days=10,
            confidence=0.8,
        )
        
        assert 0 <= result["final_score"] <= 1
        assert result["semantic_score"] == 0.9
        assert result["hops"] == 1

    def test_score_nodes_batch(self, mock_settings, sample_scored_nodes):
        """Test batch scoring of nodes."""
        from src.memory.scoring import HybridScorer
        
        scorer = HybridScorer()
        
        nodes = [
            {
                "node_id": "1",
                "name": "Test 1",
                "content": "Content 1",
                "layer": "personal",
                "semantic_score": 0.9,
                "hops": 0,
                "edge_count": 5,
                "age_days": 2,
                "confidence": 0.95,
            },
            {
                "node_id": "2",
                "name": "Test 2",
                "content": "Content 2",
                "layer": "personal",
                "semantic_score": 0.7,
                "hops": 1,
                "edge_count": 3,
                "age_days": 10,
                "confidence": 0.8,
            },
        ]
        
        scored = scorer.score_nodes(nodes, max_edges=10)
        
        assert len(scored) == 2
        # First node should have higher score (closer, more recent)
        assert scored[0].final_score > scored[1].final_score


class TestScoredNode:
    """Tests for ScoredNode dataclass."""

    def test_scored_node_creation(self, mock_settings):
        """Test ScoredNode creation."""
        from src.memory.scoring import ScoredNode
        
        node = ScoredNode(
            node_id="test_id",
            name="Test Node",
            content="Test content",
            layer="personal",
            semantic_score=0.9,
            hop_score=1.0,
            centrality_score=0.5,
            temporal_score=0.8,
            confidence=0.95,
            hops=0,
            age_days=2,
            edge_count=5,
        )
        
        assert node.node_id == "test_id"
        assert node.name == "Test Node"
        assert node.final_score == 0.9 * 0.35 + 1.0 * 0.25 + 0.5 * 0.20 + 0.8 * 0.20

    def test_scored_node_to_dict(self, mock_settings):
        """Test ScoredNode serialization."""
        from src.memory.scoring import ScoredNode
        
        node = ScoredNode(
            node_id="test_id",
            name="Test Node",
            content="Test content",
            layer="personal",
            semantic_score=0.9,
            hop_score=1.0,
            centrality_score=0.5,
            temporal_score=0.8,
            confidence=0.95,
            hops=0,
            age_days=2,
            edge_count=5,
        )
        
        result = node.to_dict()
        
        assert result["node_id"] == "test_id"
        assert result["name"] == "Test Node"
        assert "final_score" in result
