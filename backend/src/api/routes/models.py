"""Models API endpoints for provider and model management."""

from fastapi import APIRouter, Depends

from src.api.dependencies import get_current_user
from src.models.unified_llm import get_unified_llm, AVAILABLE_MODELS, LLMProvider
from src.core.config import get_settings
from src.models.nvidia import get_available_nvidia_models, NVIDIA_MODELS, is_nvidia_sdk_available
from src.core.logging import get_logger
from src.db.postgres import get_postgres_driver

logger = get_logger(__name__)

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/providers")
async def list_providers(current_user = Depends(get_current_user)):
    """List all configured LLM providers.
    
    Returns providers with their available models.
    """
    llm = get_unified_llm()
    settings = get_settings()
    providers = llm.get_available_providers()
    
    return {
        "providers": providers,
        "default_provider": settings.default_llm_provider,
        "default_model": settings.default_llm_model,
    }


@router.get("/all")
async def list_all_models(current_user = Depends(get_current_user)):
    """List all available models across all providers."""
    llm = get_unified_llm()
    models = llm.get_available_models()
    
    return {
        "models": models,
        "total": len(models),
    }


@router.get("/provider/{provider_id}")
async def list_provider_models(
    provider_id: str,
    current_user = Depends(get_current_user),
):
    """List models for a specific provider."""
    llm = get_unified_llm()
    models = llm.get_available_models(provider_id)
    
    if not models:
        return {
            "provider": provider_id,
            "models": [],
            "error": f"Provider '{provider_id}' not found or not configured",
        }
    
    return {
        "provider": provider_id,
        "models": models,
    }


@router.get("/gemini")
async def list_gemini_models(current_user = Depends(get_current_user)):
    """List available Gemini models."""
    return {
        "provider": "gemini",
        "models": AVAILABLE_MODELS[LLMProvider.GEMINI],
        "embedding_model": "models/gemini-embedding-2-preview",  # Fixed embedding model
        "note": "Embedding model is fixed and cannot be changed",
    }


@router.get("/nvidia")
async def list_nvidia_models(current_user = Depends(get_current_user)):
    """List available NVIDIA models from build.nvidia.com."""
    # Extract reasoning models (models with is_reasoning_agent=True)
    reasoning_models = [
        {
            "key": key,
            "id": config["id"],
            "max_tokens": config.get("max_tokens", 4096),
            "supports_thinking": "extra_body" in config and "chat_template_kwargs" in config.get("extra_body", {}),
        }
        for key, config in NVIDIA_MODELS.items()
        if config.get("is_reasoning_agent", False)
    ]
    
    return {
        "provider": "nvidia",
        "models": get_available_nvidia_models(),
        "base_url": "https://integrate.api.nvidia.com/v1",
        "sdk_available": is_nvidia_sdk_available(),
        "reasoning_models": reasoning_models,
        "code_models": ["devstral-2-123b"],
    }


@router.get("/reasoning")
async def list_reasoning_models(current_user = Depends(get_current_user)):
    """List available reasoning models for the reasoning agent step."""
    reasoning_models = [
        {
            "key": key,
            "id": config["id"],
            "max_tokens": config.get("max_tokens", 4096),
            "temperature": config.get("temperature", 0.6),
            "supports_thinking": "extra_body" in config and "chat_template_kwargs" in config.get("extra_body", {}),
            "provider": "nvidia",
        }
        for key, config in NVIDIA_MODELS.items()
        if config.get("is_reasoning_agent", False)
    ]
    
    # Sort by key for consistent ordering
    reasoning_models.sort(key=lambda x: x["key"])
    
    return {
        "reasoning_models": reasoning_models,
        "default": "qwen3-32b",
        "recommended": [
            {"key": "qwen3-32b", "reason": "Balanced performance and speed"},
            {"key": "qwq-32b", "reason": "Strong logical reasoning"},
            {"key": "deepseek-r1", "reason": "Deep chain-of-thought reasoning"},
        ],
    }


@router.get("/groq")
async def list_groq_models(current_user = Depends(get_current_user)):
    """List available Groq models."""
    return {
        "provider": "groq",
        "models": AVAILABLE_MODELS[LLMProvider.GROQ],
        "note": "Groq provides fast inference with lower latency",
    }


@router.post("/test/{provider_id}/{model_id}")
async def test_model(
    provider_id: str,
    model_id: str,
    current_user = Depends(get_current_user),
):
    """Test a specific model with a simple prompt.
    
    Useful for verifying API keys and model availability.
    """
    llm = get_unified_llm()
    postgres = get_postgres_driver()
    custom_keys: dict[str, str] = {}

    async with postgres.connection() as conn:
        pref = await conn.fetchrow(
            """
            SELECT settings
            FROM chat.user_preferences
            WHERE user_id = $1
            """,
            current_user["id"],
        )
    if pref and isinstance(pref["settings"], dict):
        raw_keys = pref["settings"].get("custom_provider_keys")
        if isinstance(raw_keys, dict):
            custom_keys = {
                str(k).lower(): str(v)
                for k, v in raw_keys.items()
                if isinstance(v, str) and v
            }

    provider = provider_id.lower()
    key_override = custom_keys.get(provider)
    
    try:
        if provider == "gemini":
            response = await llm._get_gemini().generate(
                prompt="Say 'Hello from NeuroGraph' in exactly those words.",
                model=model_id,
                temperature=0.1,
                max_tokens=50,
                api_key=key_override,
            )
        elif provider == "groq":
            response = await llm._get_groq().generate(
                prompt="Say 'Hello from NeuroGraph' in exactly those words.",
                model=model_id,
                temperature=0.1,
                max_tokens=50,
                api_key=key_override,
            )
        elif provider == "nvidia":
            response = await llm._get_nvidia().generate(
                prompt="Say 'Hello from NeuroGraph' in exactly those words.",
                model=model_id,
                temperature=0.1,
                max_tokens=50,
                api_key=key_override,
            )
        else:
            response = await llm.generate(
                prompt="Say 'Hello from NeuroGraph' in exactly those words.",
                provider=provider_id,
                model=model_id,
                temperature=0.1,
                max_tokens=50,
            )
        
        return {
            "success": True,
            "provider": provider_id,
            "model": model_id,
            "response": response,
            "used_custom_key": bool(key_override),
        }
    except Exception as e:
        logger.error("model_test_failed", provider=provider_id, model=model_id, error=str(e))
        return {
            "success": False,
            "provider": provider_id,
            "model": model_id,
            "error": str(e),
        }


@router.get("/recommendations")
async def get_model_recommendations(current_user = Depends(get_current_user)):
    """Get recommended models for different use cases."""
    return {
        "recommendations": {
            "chat": {
                "fast": {"provider": "gemini", "model": "gemini-2.0-flash"},
                "quality": {"provider": "nvidia", "model": "deepseek-v3.2"},
            },
            "reasoning": {
                "fast": {"provider": "nvidia", "model": "step-3.5-flash"},
                "deep": {"provider": "nvidia", "model": "deepseek-v3.2"},
            },
            "code": {
                "primary": {"provider": "nvidia", "model": "devstral-2-123b"},
                "alternative": {"provider": "groq", "model": "llama-3.3-70b-versatile"},
            },
            "orchestration": {
                "primary": {"provider": "groq", "model": "llama-3.3-70b-versatile"},
                "fallback": {"provider": "gemini", "model": "gemini-2.0-flash-lite"},
            },
            "embeddings": {
                "note": "Always uses Gemini gemini-embedding-2-preview (768 dimensions)",
                "provider": "gemini",
                "model": "models/gemini-embedding-2-preview",
                "dimensions": 768,
            },
        },
    }
