"""Hybrid scoring for combining vector and graph search results."""

import math
from dataclasses import dataclass, asdict
from typing import Any

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ScoredNode:
    """A node with its scoring components."""
    node_id: str
    name: str
    content: str
    layer: str
    
    # Scoring components
    semantic_score: float = 0.0
    hop_score: float = 0.0
    centrality_score: float = 0.0
    temporal_score: float = 0.0
    confidence: float = 1.0
    
    # Metadata
    hops: int = 0
    age_days: float = 0.0
    edge_count: int = 0
    
    @property
    def final_score(self) -> float:
        """Calculate final weighted score."""
        settings = get_settings()
        
        return (
            settings.scoring_semantic_weight * self.semantic_score +
            settings.scoring_hop_weight * self.hop_score +
            settings.scoring_centrality_weight * self.centrality_score +
            settings.scoring_temporal_weight * self.temporal_score
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result["final_score"] = self.final_score
        return result


class HybridScorer:
    """Combines vector and graph search results with weighted scoring."""

    def __init__(self) -> None:
        self._settings = get_settings()
        # Expose weights as properties for testing
        self.semantic_weight = self._settings.scoring_semantic_weight
        self.hop_weight = self._settings.scoring_hop_weight
        self.centrality_weight = self._settings.scoring_centrality_weight
        self.temporal_weight = self._settings.scoring_temporal_weight

    def _compute_hop_score(self, hops: int) -> float:
        """Calculate hop-based score (closer = higher).
        
        Formula: 1 / (1 + hops)
        - 0 hops -> 1.0
        - 1 hop -> 0.5
        - 2 hops -> 0.33
        - 3 hops -> 0.25
        """
        return 1.0 / (1.0 + hops)

    def calculate_hop_score(self, hops: int) -> float:
        """Public alias for _compute_hop_score."""
        return self._compute_hop_score(hops)

    def _compute_centrality_score(self, edge_count: int, max_edges: int) -> float:
        """Calculate centrality score based on edge count.
        
        Normalized by maximum edges in the result set.
        """
        if max_edges == 0:
            return 0.0
        return edge_count / max_edges

    def calculate_centrality_score(self, edge_count: int, max_edges: int) -> float:
        """Public alias for _compute_centrality_score."""
        return self._compute_centrality_score(edge_count, max_edges)

    def _compute_temporal_score(self, age_days: float, confidence: float) -> float:
        """Calculate temporal score with decay.
        
        Formula: decay * confidence
        Where decay = e^(-decay_rate * age_days)
        """
        decay_rate = self._settings.memory_decay_rate
        decay = math.exp(-decay_rate * age_days)
        return decay * confidence

    def calculate_temporal_score(self, age_days: float, confidence: float) -> float:
        """Public alias for _compute_temporal_score."""
        return self._compute_temporal_score(age_days, confidence)

    def score(
        self,
        semantic_score: float,
        hops: int,
        edge_count: int,
        max_edges: int,
        age_days: float,
        confidence: float,
    ) -> dict[str, Any]:
        """Score a single node and return component scores."""
        hop_score = self._compute_hop_score(hops)
        centrality_score = self._compute_centrality_score(edge_count, max_edges)
        temporal_score = self._compute_temporal_score(age_days, confidence)
        
        final_score = (
            self.semantic_weight * semantic_score +
            self.hop_weight * hop_score +
            self.centrality_weight * centrality_score +
            self.temporal_weight * temporal_score
        )
        
        return {
            "semantic_score": semantic_score,
            "hop_score": hop_score,
            "centrality_score": centrality_score,
            "temporal_score": temporal_score,
            "final_score": final_score,
            "hops": hops,
            "edge_count": edge_count,
            "age_days": age_days,
            "confidence": confidence,
        }

    def score_nodes(
        self,
        nodes: list[dict[str, Any]],
        max_edges: int | None = None,
    ) -> list[ScoredNode]:
        """Score multiple nodes and return sorted list."""
        if max_edges is None:
            max_edges = max(n.get("edge_count", 0) for n in nodes) if nodes else 1
        
        scored_nodes: list[ScoredNode] = []
        
        for node in nodes:
            hop_score = self._compute_hop_score(node.get("hops", 0))
            centrality_score = self._compute_centrality_score(
                node.get("edge_count", 0), max_edges
            )
            temporal_score = self._compute_temporal_score(
                node.get("age_days", 0), node.get("confidence", 1.0)
            )
            
            scored_node = ScoredNode(
                node_id=node.get("node_id", ""),
                name=node.get("name", ""),
                content=node.get("content", ""),
                layer=node.get("layer", "personal"),
                semantic_score=node.get("semantic_score", 0.0),
                hop_score=hop_score,
                centrality_score=centrality_score,
                temporal_score=temporal_score,
                confidence=node.get("confidence", 1.0),
                hops=node.get("hops", 0),
                age_days=node.get("age_days", 0.0),
                edge_count=node.get("edge_count", 0),
            )
            scored_nodes.append(scored_node)
        
        scored_nodes.sort(key=lambda n: n.final_score, reverse=True)
        return scored_nodes

    def score_results(
        self,
        vector_results: list[dict[str, Any]],
        graph_data: dict[str, dict[str, Any]],
        query_embedding: list[float] | None = None,
    ) -> list[ScoredNode]:
        """Score and rank results from vector and graph search.
        
        Args:
            vector_results: Results from PostgreSQL vector search
            graph_data: Graph traversal data from Neo4j
                        {node_id: {edge_count, min_hops, ...}}
            query_embedding: Original query embedding (for re-scoring if needed)
            
        Returns:
            Sorted list of ScoredNode objects
        """
        scored_nodes: list[ScoredNode] = []
        
        # Find max edges for normalization
        max_edges = 1
        if graph_data:
            max_edges = max(d.get("edge_count", 0) for d in graph_data.values()) or 1
        
        for result in vector_results:
            node_id = result.get("node_id", "")
            
            # Get graph data if available
            gdata = graph_data.get(node_id, {})
            
            # Calculate scoring components
            semantic_score = result.get("similarity", 0.0)
            hops = gdata.get("min_hops", 0)
            hop_score = self.calculate_hop_score(hops)
            edge_count = gdata.get("edge_count", 0)
            centrality_score = self.calculate_centrality_score(edge_count, max_edges)
            
            # Calculate temporal decay
            from datetime import datetime
            created_at = result.get("created_at")
            age_days = 0.0
            if created_at:
                if isinstance(created_at, datetime):
                    age_days = (datetime.utcnow() - created_at).days
            
            confidence = result.get("confidence", 1.0)
            temporal_score = self.calculate_temporal_score(age_days, confidence)
            
            node = ScoredNode(
                node_id=node_id,
                name=result.get("name", node_id),
                content=result.get("content", ""),
                layer=result.get("layer", "personal"),
                semantic_score=semantic_score,
                hop_score=hop_score,
                centrality_score=centrality_score,
                temporal_score=temporal_score,
                confidence=confidence,
                hops=hops,
                age_days=age_days,
                edge_count=edge_count,
            )
            
            scored_nodes.append(node)
        
        # Sort by final score descending
        scored_nodes.sort(key=lambda n: n.final_score, reverse=True)
        
        logger.debug(
            "scoring_complete",
            total_nodes=len(scored_nodes),
            top_score=scored_nodes[0].final_score if scored_nodes else 0,
        )
        
        return scored_nodes

    def merge_with_graph_only(
        self,
        graph_results: list[dict[str, Any]],
        seed_nodes: list[str],
    ) -> list[ScoredNode]:
        """Score graph-only results (when starting from known entities).
        
        Used when we have seed nodes from a previous vector search
        and want to score their graph neighbors.
        """
        scored_nodes: list[ScoredNode] = []
        
        # Find max edges for normalization
        max_edges = 1
        all_edges = [r.get("edge_count", 0) for r in graph_results]
        if all_edges:
            max_edges = max(all_edges) or 1
        
        for result in graph_results:
            node_id = result.get("id", result.get("node_id", ""))
            
            # Calculate scores
            hops = result.get("hops", 1)
            hop_score = self.calculate_hop_score(hops)
            
            edge_count = result.get("edge_count", 0)
            centrality_score = self.calculate_centrality_score(edge_count, max_edges)
            
            confidence = result.get("confidence", 1.0)
            temporal_score = self.calculate_temporal_score(0, confidence)  # No age info
            
            # Seed nodes get boost
            semantic_score = 1.0 if node_id in seed_nodes else 0.5
            
            node = ScoredNode(
                node_id=node_id,
                name=result.get("name", node_id),
                content=result.get("content", ""),
                layer=result.get("layer", "personal"),
                semantic_score=semantic_score,
                hop_score=hop_score,
                centrality_score=centrality_score,
                temporal_score=temporal_score,
                confidence=confidence,
                hops=hops,
                edge_count=edge_count,
            )
            
            scored_nodes.append(node)
        
        scored_nodes.sort(key=lambda n: n.final_score, reverse=True)
        
        return scored_nodes
