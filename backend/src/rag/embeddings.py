"""Embeddings service using Gemini API."""

from typing import Any

import numpy as np

from src.core.logging import get_logger
from src.models.gemini import get_gemini_client

logger = get_logger(__name__)


class EmbeddingsService:
    """Service for generating and managing embeddings."""

    def __init__(self) -> None:
        self._gemini = get_gemini_client()

    async def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        embedding = await self._gemini.embed(text)
        return embedding[0]

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
