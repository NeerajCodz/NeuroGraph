"""Models API endpoints for provider and model management."""

from fastapi import APIRouter, Depends

from src.api.dependencies import get_current_user
from src.models.unified_llm import get_unified_llm, AVAILABLE_MODELS, LLMProvider
from src.models.nvidia import get_available_nvidia_models, NVIDIA_MODELS
from src.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/providers")
async def list_providers(current_user = Depends(get_current_user)):
    """List all configured LLM providers.
    
    Returns providers with their available models.
    """
    llm = get_unified_llm()
    providers = llm.get_available_providers()
    
    return {
        "providers": providers,
        "default_provider": "gemini",
        "default_model": "gemini-2.0-flash",
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
        "embedding_model": "text-embedding-004",  # Fixed embedding model
        "note": "Embedding model is fixed and cannot be changed",
    }


@router.get("/nvidia")
async def list_nvidia_models(current_user = Depends(get_current_user)):
    """List available NVIDIA models from build.nvidia.com."""
    return {
        "provider": "nvidia",
        "models": get_available_nvidia_models(),
        "base_url": "https://integrate.api.nvidia.com/v1",
        "reasoning_models": ["step-3.5-flash", "glm4.7", "deepseek-v3.2"],
        "code_models": ["devstral-2-123b"],
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
    
    try:
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
                "note": "Always uses Gemini text-embedding-004 (768 dimensions)",
                "provider": "gemini",
                "model": "text-embedding-004",
                "dimensions": 768,
            },
        },
    }
