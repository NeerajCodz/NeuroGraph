"""Central memory manager coordinating layers, scoring, and retrieval."""

from typing import Any
from uuid import UUID

from src.core.config import get_settings
from src.core.exceptions import LayerError, MemoryAccessDeniedError
from src.core.logging import get_logger
from src.memory.decay import TemporalDecay
from src.memory.layers import GlobalLayer, PersonalLayer, TenantLayer
from src.memory.layers.base import MemoryLayer
from src.memory.scoring import HybridScorer, ScoredNode

logger = get_logger(__name__)


class MemoryManager:
    """Central coordinator for the memory system.
    
    Manages:
    - Layer access (personal, tenant, global)
    - Hybrid search across layers
    - Scoring and ranking
    - Memory operations (store, retrieve, delete)
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._layers: dict[str, MemoryLayer] = {
            "personal": PersonalLayer(),
            "tenant": TenantLayer(),
            "global": GlobalLayer(),
        }
        self._scorer = HybridScorer()
        self._decay = TemporalDecay()

    def get_layer(self, name: str) -> MemoryLayer:
        """Get a specific memory layer."""
        if name not in self._layers:
            raise LayerError(f"Unknown layer: {name}")
        return self._layers[name]

    async def remember(
        self,
        content: str,
        user_id: UUID,
        layer: str = "personal",
        tenant_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
        confidence: float = 1.0,
    ) -> dict[str, Any]:
        """Store information in memory.
        
        Args:
            content: Information to store
            user_id: User performing the operation
            layer: Target layer (personal, tenant, global)
            tenant_id: Tenant context (required for tenant layer)
            metadata: Additional metadata
            confidence: Confidence score (global layer requires >= 0.85)
            
        Returns:
            Stored memory data with extracted entities
        """
        memory_layer = self.get_layer(layer)
        
        if not await memory_layer.can_write(user_id, tenant_id):
            raise MemoryAccessDeniedError(f"No write access to {layer} layer")
        
        logger.info(
            "memory_remember",
            user_id=str(user_id),
            layer=layer,
            content_length=len(content),
        )
        
        return await memory_layer.store(
            content=content,
            user_id=user_id,
            tenant_id=tenant_id,
            metadata=metadata,
            confidence=confidence,
        )

    async def recall(
        self,
        query: str,
        user_id: UUID,
        layers: list[str] | None = None,
        tenant_id: UUID | None = None,
        include_global: bool = True,
        limit: int = 20,
        min_confidence: float = 0.5,
    ) -> list[ScoredNode]:
        """Recall information from memory with hybrid search.
        
        Args:
            query: Search query
            user_id: User performing search
            layers: Layers to search (defaults to accessible layers)
            tenant_id: Tenant context
            include_global: Include global layer in search
            limit: Maximum results
            min_confidence: Minimum confidence threshold
            
        Returns:
            Ranked list of scored nodes
        """
        # Determine which layers to search
        if layers is None:
            layers = ["personal"]
            if tenant_id:
                layers.append("tenant")
            if include_global:
                layers.append("global")
        
        logger.info(
            "memory_recall",
            user_id=str(user_id),
            layers=layers,
            query_length=len(query),
        )
        
        # Collect results from all layers
        all_results: list[dict[str, Any]] = []
        
        for layer_name in layers:
            layer = self.get_layer(layer_name)
            
            if not await layer.can_read(user_id, tenant_id):
                logger.debug(f"Skipping layer {layer_name} - no access")
                continue
            
            results = await layer.retrieve(
                query=query,
                user_id=user_id,
                tenant_id=tenant_id,
                limit=limit,
                min_confidence=min_confidence,
            )
            
            all_results.extend(results)
        
        # Apply temporal decay
        decayed_results = self._decay.apply_to_results(all_results)
        
        # Score and rank
        # TODO: Integrate graph data from Neo4j for full hybrid scoring
        graph_data: dict[str, dict[str, Any]] = {}
        
        scored = self._scorer.score_results(
            vector_results=decayed_results,
            graph_data=graph_data,
        )
        
        # Limit results
        return scored[:limit]

    async def forget(
        self,
        memory_id: str,
        user_id: UUID,
        layer: str = "personal",
        tenant_id: UUID | None = None,
    ) -> bool:
        """Delete a memory.
        
        Args:
            memory_id: Memory to delete
            user_id: User requesting deletion
            layer: Layer containing the memory
            tenant_id: Tenant context
            
        Returns:
            True if deleted successfully
        """
        memory_layer = self.get_layer(layer)
        
        logger.info(
            "memory_forget",
            user_id=str(user_id),
            layer=layer,
            memory_id=memory_id,
        )
        
        return await memory_layer.delete(
            memory_id=memory_id,
            user_id=user_id,
            tenant_id=tenant_id,
        )

    async def search(
        self,
        query: str,
        user_id: UUID,
        search_type: str = "hybrid",
        layers: list[str] | None = None,
        tenant_id: UUID | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 20,
    ) -> list[ScoredNode]:
        """Search memory with different search strategies.
        
        Args:
            query: Search query
            user_id: User performing search
            search_type: "vector", "graph", or "hybrid"
            layers: Layers to search
            tenant_id: Tenant context
            filters: Additional filters (entity types, date range, etc.)
            limit: Maximum results
            
        Returns:
            Ranked search results
        """
        if search_type == "vector":
            # Vector-only search
            return await self.recall(
                query=query,
                user_id=user_id,
                layers=layers,
                tenant_id=tenant_id,
                limit=limit,
            )
        
        elif search_type == "graph":
            # Graph-only search (requires entity starting point)
            # TODO: Implement graph-only search
            pass
        
        else:
            # Hybrid search (default)
            return await self.recall(
                query=query,
                user_id=user_id,
                layers=layers,
                tenant_id=tenant_id,
                limit=limit,
            )
        
        return []

    async def get_status(self, user_id: UUID, tenant_id: UUID | None = None) -> dict[str, Any]:
        """Get memory statistics for user/tenant.
        
        Args:
            user_id: User ID
            tenant_id: Optional tenant context
            
        Returns:
            Memory statistics
        """
        # TODO: Implement statistics queries
        return {
            "user_id": str(user_id),
            "tenant_id": str(tenant_id) if tenant_id else None,
            "total_memories": 0,
            "by_layer": {
                "personal": 0,
                "tenant": 0,
                "global": 0,
            },
            "entity_count": 0,
            "relationship_count": 0,
            "avg_confidence": 0.0,
            "decay_settings": {
                "rate": self._decay.decay_rate,
                "half_life_days": self._decay.estimate_half_life(),
            },
        }


# Global instance
_memory_manager: MemoryManager | None = None


def get_memory_manager() -> MemoryManager:
    """Get the global memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
