"""Unified LLM provider that supports multiple backends (Gemini, NVIDIA, Groq)."""

from typing import Any
from enum import Enum

from src.core.config import get_settings
from src.core.exceptions import LLMError
from src.core.logging import get_logger
from src.models.nvidia import is_nvidia_sdk_available

logger = get_logger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    GEMINI = "gemini"
    NVIDIA = "nvidia"
    GROQ = "groq"


# Available models per provider
AVAILABLE_MODELS = {
    LLMProvider.GEMINI: [
        {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "type": "fast"},
        {"id": "gemini-2.0-flash-lite", "name": "Gemini 2.0 Flash Lite", "type": "fast"},
        {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "type": "premium"},
        {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "type": "fast"},
        {"id": "gemini-3-flash-preview", "name": "Gemini 3 Flash Preview", "type": "fast"},
        {"id": "gemini-3.1-flash-lite-preview", "name": "Gemini 3.1 Flash Lite", "type": "fast"},
    ],
    LLMProvider.NVIDIA: [
        {"id": "step-3.5-flash", "name": "Step 3.5 Flash (Reasoning)", "type": "reasoning"},
        {"id": "glm4.7", "name": "GLM 4.7 (Reasoning)", "type": "reasoning"},
        {"id": "deepseek-v3.2", "name": "DeepSeek V3.2 (Reasoning)", "type": "reasoning"},
        {"id": "devstral-2-123b", "name": "Devstral 2 123B (Code)", "type": "code"},
        {"id": "llama-3.3-70b", "name": "Llama 3.3 70B", "type": "general"},
        {"id": "nemotron-70b", "name": "Nemotron 70B", "type": "general"},
    ],
    LLMProvider.GROQ: [
        {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B Versatile", "type": "fast"},
        {"id": "llama-3.1-70b-versatile", "name": "Llama 3.1 70B Versatile", "type": "fast"},
        {"id": "llama-3.2-90b-vision-preview", "name": "Llama 3.2 90B Vision", "type": "vision"},
        {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B", "type": "fast"},
        {"id": "gemma2-9b-it", "name": "Gemma 2 9B", "type": "fast"},
    ],
}


class UnifiedLLM:
    """Unified interface for LLM operations across multiple providers."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._gemini_client = None
        self._nvidia_client = None
        self._groq_client = None

    def _get_gemini(self):
        """Lazy load Gemini client."""
        if self._gemini_client is None:
            from src.models.gemini import get_gemini_client
            self._gemini_client = get_gemini_client()
        return self._gemini_client

    def _get_nvidia(self):
        """Lazy load NVIDIA client."""
        if self._nvidia_client is None:
            from src.models.nvidia import get_nvidia_client
            self._nvidia_client = get_nvidia_client()
        return self._nvidia_client

    def _get_groq(self):
        """Lazy load Groq client."""
        if self._groq_client is None:
            from src.models.groq import get_groq_client
            self._groq_client = get_groq_client()
        return self._groq_client

    def get_available_providers(self) -> list[dict]:
        """Get list of configured providers."""
        providers = []
        
        # Gemini is available if key is set
        providers.append({
            "id": "gemini",
            "name": "Google Gemini",
            "models": AVAILABLE_MODELS[LLMProvider.GEMINI],
            "is_available": bool(self._settings.gemini_api_key),
        })
        
        # NVIDIA 
        providers.append({
            "id": "nvidia",
            "name": "NVIDIA AI",
            "models": AVAILABLE_MODELS[LLMProvider.NVIDIA],
            "is_available": bool(self._settings.nvidia_api_key) and is_nvidia_sdk_available(),
        })
        
        # Groq
        providers.append({
            "id": "groq",
            "name": "Groq",
            "models": AVAILABLE_MODELS[LLMProvider.GROQ],
            "is_available": bool(self._settings.groq_api_key),
        })
        
        return providers

    def get_available_models(self, provider: str | None = None) -> list[dict]:
        """Get all available models, optionally filtered by provider."""
        if provider:
            try:
                provider_enum = LLMProvider(provider)
                return AVAILABLE_MODELS.get(provider_enum, [])
            except ValueError:
                return []
        
        # Return all models with provider info
        all_models = []
        for prov, models in AVAILABLE_MODELS.items():
            for model in models:
                all_models.append({
                    **model,
                    "provider": prov.value,
                })
        return all_models

    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> str:
        """Generate text using the specified provider and model.
        
        Args:
            prompt: User prompt
            system_instruction: System instruction
            provider: LLM provider (gemini, nvidia, groq). Defaults to config default.
            model: Model ID. Defaults to provider's default.
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            json_mode: Whether to expect JSON output (Gemini only)
            
        Returns:
            Generated text response
        """
        provider = provider or self._settings.default_llm_provider
        
        try:
            provider_enum = LLMProvider(provider)
        except ValueError:
            raise LLMError(f"Unknown provider: {provider}. Available: {[p.value for p in LLMProvider]}")
        
        if provider_enum == LLMProvider.GEMINI:
            client = self._get_gemini()
            return await client.generate(
                prompt=prompt,
                system_instruction=system_instruction,
                model=model or self._settings.gemini_model_flash,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=json_mode,
            )
        
        elif provider_enum == LLMProvider.NVIDIA:
            client = self._get_nvidia()
            if not client.is_available:
                raise LLMError("NVIDIA API not configured. Set NVIDIA_API_KEY.")
            return await client.generate(
                prompt=prompt,
                system_instruction=system_instruction,
                model=model or "devstral-2-123b",
                temperature=temperature,
                max_tokens=max_tokens,
            )
        
        elif provider_enum == LLMProvider.GROQ:
            client = self._get_groq()
            return await client.generate(
                prompt=prompt,
                system_instruction=system_instruction,
                model=model or self._settings.groq_model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        
        raise LLMError(f"Unsupported provider: {provider}")

    async def generate_with_context(
        self,
        query: str,
        context: str,
        system_instruction: str | None = None,
        provider: str | None = None,
        model: str | None = None,
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
            provider=provider,
            model=model,
        )


# Global instance
_unified_llm: UnifiedLLM | None = None


def get_unified_llm() -> UnifiedLLM:
    """Get the global unified LLM instance."""
    global _unified_llm
    if _unified_llm is None:
        _unified_llm = UnifiedLLM()
    return _unified_llm
