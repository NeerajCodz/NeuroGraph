"""NVIDIA API client for LLM operations via build.nvidia.com."""

import asyncio
from typing import AsyncIterator

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.core.config import get_settings
from src.core.exceptions import LLMError, RateLimitError
from src.core.logging import get_logger

logger = get_logger(__name__)

# Available NVIDIA models with their configurations
NVIDIA_MODELS = {
    # Reasoning models
    "step-3.5-flash": {
        "id": "stepfun-ai/step-3.5-flash",
        "max_tokens": 16384,
        "temperature": 1.0,
        "top_p": 0.9,
        "supports_reasoning": True,
    },
    "glm4.7": {
        "id": "z-ai/glm4.7",
        "max_tokens": 16384,
        "temperature": 1.0,
        "top_p": 1.0,
        "supports_reasoning": True,
        "extra_body": {"chat_template_kwargs": {"enable_thinking": True, "clear_thinking": False}},
    },
    "deepseek-v3.2": {
        "id": "deepseek-ai/deepseek-v3.2",
        "max_tokens": 8192,
        "temperature": 1.0,
        "top_p": 0.95,
        "supports_reasoning": True,
        "extra_body": {"chat_template_kwargs": {"thinking": True}},
    },
    # Code/instruction models
    "devstral-2-123b": {
        "id": "mistralai/devstral-2-123b-instruct-2512",
        "max_tokens": 8192,
        "temperature": 0.15,
        "top_p": 0.95,
        "supports_reasoning": False,
    },
    # General models
    "llama-3.3-70b": {
        "id": "meta/llama-3.3-70b-instruct",
        "max_tokens": 8192,
        "temperature": 0.7,
        "top_p": 0.9,
        "supports_reasoning": False,
    },
    "nemotron-70b": {
        "id": "nvidia/llama-3.1-nemotron-70b-instruct",
        "max_tokens": 4096,
        "temperature": 0.5,
        "top_p": 1.0,
        "supports_reasoning": False,
    },
}


class NvidiaClient:
    """Async client for NVIDIA API via OpenAI-compatible endpoint."""

    def __init__(self) -> None:
        self._settings = get_settings()
        api_key = self._settings.nvidia_api_key
        if api_key:
            self._client = AsyncOpenAI(
                base_url=self._settings.nvidia_base_url,
                api_key=api_key.get_secret_value(),
            )
        else:
            self._client = None
        self._last_call_time = 0.0

    @property
    def is_available(self) -> bool:
        """Check if NVIDIA API is configured."""
        return self._client is not None

    async def _rate_limit_delay(self) -> None:
        """Ensure minimum delay between API calls."""
        import time
        now = time.time()
        elapsed = now - self._last_call_time
        min_delay = 0.3
        if elapsed < min_delay:
            await asyncio.sleep(min_delay - elapsed)
        self._last_call_time = time.time()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        retry=retry_if_exception_type(RateLimitError),
    )
    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        model: str = "devstral-2-123b",
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Generate text completion using NVIDIA models.
        
        Args:
            prompt: User prompt
            system_instruction: System instruction for the model
            model: Model key from NVIDIA_MODELS
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            Generated text response
        """
        if not self.is_available:
            raise LLMError("NVIDIA API not configured. Set NVIDIA_API_KEY.")
        
        model_config = NVIDIA_MODELS.get(model)
        if not model_config:
            raise LLMError(f"Unknown NVIDIA model: {model}. Available: {list(NVIDIA_MODELS.keys())}")
        
        model_id = model_config["id"]
        temp = temperature if temperature is not None else model_config["temperature"]
        tokens = max_tokens if max_tokens is not None else model_config["max_tokens"]
        
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        
        try:
            await self._rate_limit_delay()
            
            kwargs = {
                "model": model_id,
                "messages": messages,
                "temperature": temp,
                "top_p": model_config["top_p"],
                "max_tokens": tokens,
            }
            
            # Add extra body for reasoning models
            if "extra_body" in model_config:
                kwargs["extra_body"] = model_config["extra_body"]
            
            response = await self._client.chat.completions.create(**kwargs)
            
            result = response.choices[0].message.content or ""
            
            logger.debug(
                "nvidia_generate",
                model=model_id,
                prompt_length=len(prompt),
                response_length=len(result),
            )
            
            return result
            
        except Exception as e:
            error_str = str(e).lower()
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(f"NVIDIA rate limit: {e}") from e
            raise LLMError(f"NVIDIA generation failed: {e}") from e

    async def generate_stream(
        self,
        prompt: str,
        system_instruction: str | None = None,
        model: str = "devstral-2-123b",
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[tuple[str | None, str | None]]:
        """Generate text completion with streaming.
        
        Yields:
            Tuples of (reasoning_content, content) - one may be None
        """
        if not self.is_available:
            raise LLMError("NVIDIA API not configured. Set NVIDIA_API_KEY.")
        
        model_config = NVIDIA_MODELS.get(model)
        if not model_config:
            raise LLMError(f"Unknown NVIDIA model: {model}")
        
        model_id = model_config["id"]
        temp = temperature if temperature is not None else model_config["temperature"]
        tokens = max_tokens if max_tokens is not None else model_config["max_tokens"]
        
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        
        try:
            await self._rate_limit_delay()
            
            kwargs = {
                "model": model_id,
                "messages": messages,
                "temperature": temp,
                "top_p": model_config["top_p"],
                "max_tokens": tokens,
                "stream": True,
            }
            
            if "extra_body" in model_config:
                kwargs["extra_body"] = model_config["extra_body"]
            
            stream = await self._client.chat.completions.create(**kwargs)
            
            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                reasoning = getattr(delta, "reasoning_content", None)
                content = getattr(delta, "content", None)
                if reasoning or content:
                    yield reasoning, content
                    
        except Exception as e:
            error_str = str(e).lower()
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(f"NVIDIA rate limit: {e}") from e
            raise LLMError(f"NVIDIA streaming failed: {e}") from e

    async def generate_with_context(
        self,
        query: str,
        context: str,
        system_instruction: str | None = None,
        model: str = "devstral-2-123b",
    ) -> str:
        """Generate response with provided context."""
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
            model=model,
        )


# Global client instance
_nvidia_client: NvidiaClient | None = None


def get_nvidia_client() -> NvidiaClient:
    """Get the global NVIDIA client instance."""
    global _nvidia_client
    if _nvidia_client is None:
        _nvidia_client = NvidiaClient()
    return _nvidia_client


def get_available_nvidia_models() -> list[dict]:
    """Get list of available NVIDIA models with their info."""
    return [
        {
            "key": key,
            "id": config["id"],
            "max_tokens": config["max_tokens"],
            "supports_reasoning": config.get("supports_reasoning", False),
        }
        for key, config in NVIDIA_MODELS.items()
    ]
