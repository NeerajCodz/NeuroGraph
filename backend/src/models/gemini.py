"""Gemini API client for main LLM operations and embeddings."""

import asyncio
from typing import Any

import numpy as np
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.core.config import get_settings
from src.core.exceptions import EmbeddingError, GeminiError, RateLimitError
from src.core.logging import get_logger

logger = get_logger(__name__)

# Rate limit: minimum delay between API calls (in seconds)
MIN_API_DELAY = 0.5


class GeminiClient:
    """Async client for Google Gemini API with rate limiting."""

    def __init__(self) -> None:
        self._settings = get_settings()
        configured_key = (
            self._settings.gemini_api_key.get_secret_value()
            if self._settings.gemini_api_key
            else None
        )
        self._client = genai.Client(api_key=configured_key) if configured_key else None
        self._last_call_time = 0.0

    def _build_client(self, api_key: str | None = None):
        """Get client instance, optionally with per-request API key override."""
        if api_key:
            return genai.Client(api_key=api_key)
        return self._client

    async def _rate_limit_delay(self) -> None:
        """Ensure minimum delay between API calls."""
        import time
        now = time.time()
        elapsed = now - self._last_call_time
        if elapsed < MIN_API_DELAY:
            await asyncio.sleep(MIN_API_DELAY - elapsed)
        self._last_call_time = time.time()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type(RateLimitError),
    )
    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
        api_key: str | None = None,
    ) -> str:
        """Generate text completion using Gemini.
        
        Args:
            prompt: User prompt
            system_instruction: System instruction for the model
            model: Model to use (defaults to flash)
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            json_mode: Whether to expect JSON output
            
        Returns:
            Generated text response
        """
        model_name = model or self._settings.gemini_model_flash
        client = self._build_client(api_key)
        if client is None:
            raise GeminiError("Gemini API not configured. Set GEMINI_API_KEY.")
        
        try:
            # Apply rate limiting
            await self._rate_limit_delay()
            
            config = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                system_instruction=system_instruction,
            )
            
            if json_mode:
                config.response_mime_type = "application/json"
            
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
            
            if not response.text:
                raise GeminiError("Empty response from Gemini")
            
            logger.debug(
                "gemini_generate",
                model=model_name,
                prompt_length=len(prompt),
                response_length=len(response.text),
            )
            
            return response.text
            
        except Exception as e:
            error_str = str(e).lower()
            if "rate" in error_str or "quota" in error_str:
                raise RateLimitError(f"Gemini rate limit: {e}") from e
            raise GeminiError(f"Gemini generation failed: {e}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def generate_with_context(
        self,
        query: str,
        context: str,
        system_instruction: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
    ) -> str:
        """Generate response with provided context.
        
        Args:
            query: User query
            context: Context from memory/RAG
            system_instruction: System instruction
            model: Model to use
            
        Returns:
            Generated response
        """
        default_system = """You are NeuroGraph, an AI with structured memory.
Use ONLY the context below to answer.
If confidence is low, say so explicitly.
Cite which memory nodes led to your conclusion."""
        
        full_prompt = f"""Context:
{context}

---

User question: {query}

Answer with reasoning. Cite which memory nodes led to your conclusion."""
        
        return await self.generate(
            prompt=full_prompt,
            system_instruction=system_instruction or default_system,
            model=model or self._settings.gemini_model_flash,
            api_key=api_key,
        )

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type(RateLimitError),
    )
    async def embed(
        self,
        text: str | list[str],
        model: str | None = None,
        output_dimensionality: int = 768,
        task_type: str = "RETRIEVAL_DOCUMENT",
        api_key: str | None = None,
    ) -> np.ndarray:
        """Generate embeddings for text.
        
        Args:
            text: Text or list of texts to embed
            model: Embedding model to use
            output_dimensionality: Output embedding dimension (768, 1536, or 3072). Default 768.
            task_type: Task type for embedding ("RETRIEVAL_DOCUMENT" or "RETRIEVAL_QUERY")
            
        Returns:
            Numpy array of embeddings
        """
        from google.genai import types
        
        model_name = model or self._settings.gemini_model_embedding
        client = self._build_client(api_key)
        if client is None:
            raise EmbeddingError("Gemini API not configured. Set GEMINI_API_KEY.")
        
        if isinstance(text, str):
            texts = [text]
        else:
            texts = text
        
        try:
            # Apply rate limiting
            await self._rate_limit_delay()
            
            response = await client.aio.models.embed_content(
                model=model_name,
                contents=texts,
                config=types.EmbedContentConfig(
                    output_dimensionality=output_dimensionality,
                    task_type=task_type,
                ),
            )
            
            # Extract embeddings from response
            embeddings = [e.values for e in response.embeddings]
            
            logger.debug(
                "gemini_embed",
                model=model_name,
                text_count=len(texts),
                dimension=len(embeddings[0]) if embeddings else 0,
            )
            
            return np.array(embeddings)
            
        except Exception as e:
            error_str = str(e).lower()
            if "rate" in error_str or "quota" in error_str:
                raise RateLimitError(f"Gemini embedding rate limit: {e}") from e
            raise EmbeddingError(f"Embedding generation failed: {e}") from e

    async def extract_entities(
        self,
        text: str,
    ) -> list[dict[str, Any]]:
        """Extract entities and relationships from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of extracted entities with relationships
        """
        prompt = f"""Analyze the following text and extract entities and relationships.

Text: {text}

Return a JSON object with:
{{
  "entities": [
    {{"name": "...", "type": "Person|Project|Organization|Document|Event|Concept", "properties": {{}}}}
  ],
  "relationships": [
    {{"source": "entity_name", "target": "entity_name", "type": "WORKS_ON|MANAGES|RELATED_TO|etc", "reason": "why this relationship exists"}}
  ]
}}"""
        
        response = await self.generate(
            prompt=prompt,
            json_mode=True,
            temperature=0.3,
        )
        
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("entity_extraction_parse_failed", response=response[:200])
            return {"entities": [], "relationships": []}

    async def summarize(
        self,
        text: str,
        max_length: int = 200,
    ) -> str:
        """Summarize text.
        
        Args:
            text: Text to summarize
            max_length: Maximum summary length in words
            
        Returns:
            Summary text
        """
        prompt = f"""Summarize the following text in {max_length} words or less:

{text}

Summary:"""
        
        return await self.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=max_length * 2,
        )


# Global client instance
_gemini_client: GeminiClient | None = None


def get_gemini_client() -> GeminiClient:
    """Get the global Gemini client instance."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
