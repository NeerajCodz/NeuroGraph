"""NVIDIA API client for LLM operations via build.nvidia.com."""

import asyncio
from typing import Any, AsyncIterator

try:
    from openai import AsyncOpenAI
except ImportError:  # pragma: no cover - optional dependency in some envs
    AsyncOpenAI = None  # type: ignore[assignment]
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
    # Nemotron reasoning models
    "nemotron-reasoning-4b": {
        "id": "nvidia/nemotron-content-safety-reasoning-4b",
        "max_tokens": 2048,
        "temperature": 0.0,
        "top_p": 1.0,
        "supports_reasoning": True,
        "is_reasoning_agent": True,
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
        if api_key and AsyncOpenAI is not None:
            self._client = AsyncOpenAI(
                base_url=self._settings.nvidia_base_url,
                api_key=api_key.get_secret_value(),
            )
        else:
            self._client = None
        self._last_call_time = 0.0

    def _build_client(self, api_key: str | None = None) -> Any:
        """Get client instance, optionally with a per-request API key override."""
        if api_key:
            if AsyncOpenAI is None:
                raise LLMError(
                    "NVIDIA provider requires 'openai' package. Install it in backend environment."
                )
            return AsyncOpenAI(
                base_url=self._settings.nvidia_base_url,
                api_key=api_key,
            )
        return self._client

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
        api_key: str | None = None,
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
        client = self._build_client(api_key)
        if client is None:
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
            
            response = await client.chat.completions.create(**kwargs)
            
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
        api_key: str | None = None,
    ) -> AsyncIterator[tuple[str | None, str | None]]:
        """Generate text completion with streaming.
        
        Yields:
            Tuples of (reasoning_content, content) - one may be None
        """
        client = self._build_client(api_key)
        if client is None:
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
            
            stream = await client.chat.completions.create(**kwargs)
            
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

    async def reason_over_nodes(
        self,
        query: str,
        memory_nodes: list[dict],
        graph_paths: list[dict],
        api_key: str | None = None,
        enable_thinking: bool = True,
    ) -> dict:
        """
        Use Nemotron reasoning model to analyze memory nodes and graph paths.
        
        Args:
            query: User's original query
            memory_nodes: List of memory nodes with content, score, layer
            graph_paths: List of graph paths with source, relationship, target, reason
            api_key: Optional API key override
            enable_thinking: Whether to use /think mode for explicit reasoning traces
            
        Returns:
            dict with 'reasoning', 'synthesized_context', 'confidence', 'cited_nodes'
        """
        client = self._build_client(api_key)
        if client is None:
            # Fallback to simple context assembly if NVIDIA not available
            logger.info("reasoning_agent_fallback", reason="NVIDIA API not configured")
            return self._fallback_reasoning(query, memory_nodes, graph_paths)
        
        # Build the reasoning prompt
        nodes_text = ""
        for i, node in enumerate(memory_nodes[:10]):
            score = node.get("score", node.get("similarity", 0.7))
            content = node.get("content", "")[:200]
            layer = node.get("layer", "unknown")
            nodes_text += f"[Node {i+1}] (score: {score:.2f}, layer: {layer})\n{content}\n\n"
        
        paths_text = ""
        for path in graph_paths[:10]:
            source = path.get("source", "?")
            rel = path.get("relationship", "CONNECTED_TO")
            target = path.get("target", "?")
            reason = path.get("reason", "")
            paths_text += f"  {source} → {rel} → {target}"
            if reason:
                paths_text += f" (reason: {reason})"
            paths_text += "\n"
        
        reasoning_prompt = f"""You are a reasoning agent that analyzes memory nodes and graph relationships to synthesize context for answering user queries.

USER QUERY: {query}

MEMORY NODES:
{nodes_text if nodes_text else "No memory nodes available"}

GRAPH RELATIONSHIPS:
{paths_text if paths_text else "No graph paths available"}

TASK:
1. Analyze which memory nodes are most relevant to the query
2. Trace the reasoning path through graph relationships
3. Synthesize a coherent context that explains HOW you arrived at the answer
4. Cite specific nodes by their scores (e.g., [0.85] Frank prefers...)
5. Rate overall confidence (0.0-1.0) based on node scores and path coherence

OUTPUT FORMAT:
<reasoning>
[Your step-by-step analysis of how nodes connect to answer the query]
</reasoning>

<synthesized_context>
[A clear, structured context ready for the main LLM to use]
</synthesized_context>

<cited_nodes>
[List of cited node scores and key content]
</cited_nodes>

<confidence>
[0.0-1.0 confidence score]
</confidence>

{"Use /think to enable reasoning traces." if enable_thinking else "Use /no_think for direct output."} {"/" + ("think" if enable_thinking else "no_think")}"""

        try:
            await self._rate_limit_delay()
            
            # Use Nemotron reasoning model or fallback to llama
            model_key = "nemotron-reasoning-4b"
            model_config = NVIDIA_MODELS.get(model_key)
            
            if not model_config:
                # Fallback to llama-3.3-70b if reasoning model not available
                model_key = "llama-3.3-70b"
                model_config = NVIDIA_MODELS.get(model_key, {
                    "id": "meta/llama-3.3-70b-instruct",
                    "max_tokens": 4096,
                    "temperature": 0.3,
                    "top_p": 0.9,
                })
            
            messages = [{"role": "user", "content": reasoning_prompt}]
            
            response = await client.chat.completions.create(
                model=model_config["id"],
                messages=messages,
                temperature=model_config.get("temperature", 0.0),
                top_p=model_config.get("top_p", 1.0),
                max_tokens=model_config.get("max_tokens", 2048),
            )
            
            result_text = response.choices[0].message.content or ""
            
            logger.info(
                "reasoning_agent_complete",
                model=model_key,
                input_nodes=len(memory_nodes),
                input_paths=len(graph_paths),
                output_length=len(result_text),
            )
            
            # Parse the response
            return self._parse_reasoning_response(result_text, memory_nodes)
            
        except Exception as e:
            logger.warning("reasoning_agent_error", error=str(e))
            return self._fallback_reasoning(query, memory_nodes, graph_paths)
    
    def _parse_reasoning_response(self, response: str, memory_nodes: list[dict]) -> dict:
        """Parse the structured reasoning response."""
        import re
        
        reasoning = ""
        synthesized_context = ""
        cited_nodes = []
        confidence = 0.7
        
        # Extract reasoning
        reasoning_match = re.search(r"<reasoning>(.*?)</reasoning>", response, re.DOTALL)
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()
        
        # Extract synthesized context
        context_match = re.search(r"<synthesized_context>(.*?)</synthesized_context>", response, re.DOTALL)
        if context_match:
            synthesized_context = context_match.group(1).strip()
        
        # Extract cited nodes
        cited_match = re.search(r"<cited_nodes>(.*?)</cited_nodes>", response, re.DOTALL)
        if cited_match:
            cited_text = cited_match.group(1).strip()
            # Parse [score] content format
            for match in re.finditer(r"\[(\d+\.?\d*)\]\s*(.+?)(?=\[|$)", cited_text, re.DOTALL):
                cited_nodes.append({
                    "score": float(match.group(1)),
                    "content": match.group(2).strip()[:100],
                })
        
        # Extract confidence
        conf_match = re.search(r"<confidence>\s*([\d.]+)", response)
        if conf_match:
            try:
                confidence = min(1.0, max(0.0, float(conf_match.group(1))))
            except ValueError:
                pass
        
        # If parsing failed, use the whole response as context
        if not synthesized_context:
            # Check for <think> tags (from reasoning mode)
            think_match = re.search(r"<think>(.*?)</think>", response, re.DOTALL)
            if think_match:
                reasoning = think_match.group(1).strip()
                # Use content after </think> as synthesized context
                after_think = response.split("</think>")[-1].strip()
                synthesized_context = after_think if after_think else response
            else:
                synthesized_context = response
        
        return {
            "reasoning": reasoning,
            "synthesized_context": synthesized_context,
            "confidence": confidence,
            "cited_nodes": cited_nodes,
        }
    
    def _fallback_reasoning(
        self,
        query: str,
        memory_nodes: list[dict],
        graph_paths: list[dict],
    ) -> dict:
        """Fallback reasoning when NVIDIA API is not available."""
        # Build simple context from nodes
        context_parts = []
        cited_nodes = []
        
        for node in memory_nodes[:5]:
            score = node.get("score", node.get("similarity", 0.7))
            content = node.get("content", "")
            context_parts.append(f"[{score:.2f}] {content}")
            cited_nodes.append({"score": score, "content": content[:100]})
        
        # Add graph paths to reasoning
        reasoning_parts = []
        for path in graph_paths[:5]:
            source = path.get("source", "?")
            rel = path.get("relationship", "→")
            target = path.get("target", "?")
            reason = path.get("reason", "")
            path_str = f"{source} → {rel} → {target}"
            if reason:
                path_str += f" ({reason})"
            reasoning_parts.append(path_str)
        
        avg_score = sum(n.get("score", n.get("similarity", 0.7)) for n in memory_nodes[:5]) / max(len(memory_nodes[:5]), 1)
        
        return {
            "reasoning": "\n".join(reasoning_parts) if reasoning_parts else "Direct memory retrieval (no graph paths)",
            "synthesized_context": "\n\n".join(context_parts),
            "confidence": avg_score,
            "cited_nodes": cited_nodes,
        }


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
