"""Embeddings service using Gemini API with Redis caching."""

import hashlib
import json
from typing import Any

import numpy as np

from src.core.logging import get_logger
from src.db.redis import get_redis_driver
from src.models.gemini import get_gemini_client

logger = get_logger(__name__)

# Cache TTL for embeddings (7 days)
EMBEDDING_CACHE_TTL = 60 * 60 * 24 * 7


def _hash_text(text: str) -> str:
    """Create a hash of text for cache key."""
    return hashlib.sha256(text.encode()).hexdigest()[:32]


class EmbeddingsService:
    """Service for generating and managing embeddings with caching."""

    def __init__(self) -> None:
        self._gemini = get_gemini_client()
        self._redis = get_redis_driver()

    async def _get_cached_embedding(self, text: str) -> np.ndarray | None:
        """Get cached embedding from Redis."""
        try:
            cache_key = f"embed:{_hash_text(text)}"
            cached = await self._redis.get(cache_key)
            if cached:
                embedding_list = json.loads(cached)
                logger.debug("embedding_cache_hit", text_len=len(text))
                return np.array(embedding_list)
        except Exception as e:
            logger.warning("embedding_cache_get_failed", error=str(e))
        return None

    async def _set_cached_embedding(self, text: str, embedding: np.ndarray) -> None:
        """Cache embedding in Redis."""
        try:
            cache_key = f"embed:{_hash_text(text)}"
            await self._redis.set(
                cache_key, 
                json.dumps(embedding.tolist()),
                ex=EMBEDDING_CACHE_TTL
            )
            logger.debug("embedding_cached", text_len=len(text))
        except Exception as e:
            logger.warning("embedding_cache_set_failed", error=str(e))

    async def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text with caching.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        # Check cache first
        cached = await self._get_cached_embedding(text)
        if cached is not None:
            return cached
        
        # Generate new embedding
        embedding = await self._gemini.embed(text)
        result = embedding[0]
        
        # Cache for future use
        await self._set_cached_embedding(text, result)
        
        return result

    async def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            2D numpy array of embeddings
        """
        if not texts:
            return np.array([])
        
        # Batch in chunks of 100
        batch_size = 100
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = await self._gemini.embed(batch)
            all_embeddings.append(embeddings)
        
        return np.vstack(all_embeddings)

    async def embed_with_metadata(
        self,
        items: list[dict[str, Any]],
        text_key: str = "content",
    ) -> list[dict[str, Any]]:
        """Generate embeddings for items and add to metadata.
        
        Args:
            items: List of items with text content
            text_key: Key containing text to embed
            
        Returns:
            Items with added embedding key
        """
        texts = [item[text_key] for item in items if text_key in item]
        embeddings = await self.embed_batch(texts)
        
        result = []
        for item, embedding in zip(items, embeddings):
            item = item.copy()
            item["embedding"] = embedding.tolist()
            result.append(item)
        
        return result
