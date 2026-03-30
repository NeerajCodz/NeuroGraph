"""Hybrid search combining vector and graph retrieval."""

from typing import Any
from uuid import UUID

from src.core.config import get_settings
from src.core.logging import get_logger
from src.db.neo4j import get_neo4j_driver
from src.db.neo4j.operations import Neo4jOperations
from src.db.postgres import get_postgres_driver
from src.db.postgres.operations import PostgresOperations
from src.memory.scoring import HybridScorer, ScoredNode
from src.rag.embeddings import EmbeddingsService

logger = get_logger(__name__)


class HybridSearch:
    """Combines vector similarity and graph traversal for retrieval."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._embeddings = EmbeddingsService()
        self._scorer = HybridScorer()

    async def search(
        self,
        query: str,
        user_id: UUID,
        tenant_id: UUID | None = None,
        layers: list[str] | None = None,
        max_vector_results: int = 50,
        max_graph_hops: int = 3,
        limit: int = 20,
        min_confidence: float = 0.5,
    ) -> list[ScoredNode]:
        """Perform hybrid search.
        
        Pipeline:
        1. Generate query embedding
        2. Vector search in PostgreSQL (semantic similarity)
        3. Extract seed entities from top results
        4. Graph traversal from seeds in Neo4j (structural relationships)
        5. Hybrid scoring combining both signals
        6. Return ranked results
        
        Args:
            query: Search query
            user_id: User context
            tenant_id: Tenant context
            layers: Memory layers to search
            max_vector_results: Max results from vector search
            max_graph_hops: Max graph traversal depth
            limit: Final result limit
            min_confidence: Minimum confidence threshold
            
        Returns:
            Ranked list of ScoredNode objects
        """
        layers = layers or ["personal"]
        
        logger.info(
            "hybrid_search_start",
            query_length=len(query),
            layers=layers,
            user_id=str(user_id),
        )
        
        # Step 1: Generate query embedding
        query_embedding = await self._embeddings.embed_text(query)
        
        # Step 2: Vector search in PostgreSQL
        postgres = get_postgres_driver()
        pg_ops = PostgresOperations(postgres)
        
        vector_results = await pg_ops.similarity_search(
            query_embedding=query_embedding,
            layers=layers,
            user_id=user_id,
            tenant_id=tenant_id,
            min_confidence=min_confidence,
            limit=max_vector_results,
            threshold=self._settings.rag_similarity_threshold,
        )
        
        logger.debug(
            "vector_search_complete",
            results_count=len(vector_results),
        )
        
        if not vector_results:
            return []
        
        # Step 3: Extract seed nodes for graph traversal
        seed_nodes = [r["node_id"] for r in vector_results[:10]]
        
        # Step 4: Graph traversal from seeds
        neo4j = get_neo4j_driver()
        neo_ops = Neo4jOperations(neo4j)
        
        graph_paths = await neo_ops.traverse(
            seed_nodes=seed_nodes,
            max_hops=max_graph_hops,
        )
        
        # Get centrality data
        all_node_ids = set(seed_nodes)
        for path in graph_paths:
            for node in path.get("nodes", []):
                if "id" in node:
                    all_node_ids.add(node["id"])
        
        centrality = await neo_ops.get_centrality(list(all_node_ids))
        
        # Build graph data for scoring
        graph_data: dict[str, dict[str, Any]] = {}
        
        for node_id in all_node_ids:
            # Find minimum hops from seeds
            min_hops = 0
            if node_id not in seed_nodes:
                for path in graph_paths:
                    path_nodes = [n.get("id") for n in path.get("nodes", [])]
                    if node_id in path_nodes:
                        hops = path.get("hops", 1)
                        if min_hops == 0 or hops < min_hops:
                            min_hops = hops
            
            graph_data[node_id] = {
                "edge_count": centrality.get(node_id, 0),
                "min_hops": min_hops,
            }
        
        logger.debug(
            "graph_traversal_complete",
            paths_count=len(graph_paths),
            nodes_found=len(all_node_ids),
        )
        
        # Step 5: Hybrid scoring
        scored_results = self._scorer.score_results(
            vector_results=vector_results,
            graph_data=graph_data,
            query_embedding=query_embedding.tolist(),
        )
        
        # Step 6: Return top results
        final_results = scored_results[:limit]
        
        logger.info(
            "hybrid_search_complete",
            total_scored=len(scored_results),
            returned=len(final_results),
            top_score=final_results[0].final_score if final_results else 0,
        )
        
        return final_results

    async def search_by_entity(
        self,
        entity_name: str,
        user_id: UUID,
        tenant_id: UUID | None = None,
        max_hops: int = 2,
        limit: int = 20,
    ) -> list[ScoredNode]:
        """Search starting from a known entity.
        
        Args:
            entity_name: Entity to start from
            user_id: User context
            tenant_id: Tenant context
            max_hops: Maximum graph depth
            limit: Result limit
            
        Returns:
            Connected nodes scored by relationship strength
        """
        neo4j = get_neo4j_driver()
        neo_ops = Neo4jOperations(neo4j)
        
        # Find the entity
        entities = await neo_ops.search_entities(
            name_pattern=entity_name,
            user_id=str(user_id),
            tenant_id=str(tenant_id) if tenant_id else None,
            limit=1,
        )
        
        if not entities:
            return []
        
        entity_id = entities[0].get("id", "")
        
        # Traverse from entity
        paths = await neo_ops.traverse(
            seed_nodes=[entity_id],
            max_hops=max_hops,
        )
        
        # Build results from paths
        graph_results = []
        seen = set()
        
        for path in paths:
            for node in path.get("nodes", []):
                node_id = node.get("id")
                if node_id and node_id not in seen:
                    seen.add(node_id)
                    graph_results.append({
                        "id": node_id,
                        "name": node.get("name", ""),
                        "type": node.get("type", ""),
                        "hops": path.get("hops", 1),
                        "confidence": 1.0,
                    })
        
        # Score graph-only results
        scored = self._scorer.merge_with_graph_only(
            graph_results=graph_results,
            seed_nodes=[entity_id],
        )
        
        return scored[:limit]
