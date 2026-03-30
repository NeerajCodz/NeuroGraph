"""Groq API client for orchestrator LLM."""

from typing import Any

from groq import AsyncGroq
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import get_settings
from src.core.exceptions import GroqError, RateLimitError
from src.core.logging import get_logger

logger = get_logger(__name__)


class GroqClient:
    """Async client for Groq API (fast inference for orchestration)."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client = AsyncGroq(
            api_key=self._settings.groq_api_key.get_secret_value()
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> str:
        """Generate text completion using Groq.
        
        Args:
            prompt: User prompt
            system_instruction: System instruction
            model: Model to use (defaults to Llama 3.3)
            temperature: Sampling temperature (lower for more deterministic)
            max_tokens: Maximum output tokens
            json_mode: Whether to expect JSON output
            
        Returns:
            Generated text response
        """
        model_name = model or self._settings.groq_model
        
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        
        try:
            kwargs: dict[str, Any] = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            
            response = await self._client.chat.completions.create(**kwargs)
            
            content = response.choices[0].message.content
            if not content:
                raise GroqError("Empty response from Groq")
            
            logger.debug(
                "groq_generate",
                model=model_name,
                prompt_length=len(prompt),
                response_length=len(content),
            )
            
            return content
            
        except Exception as e:
            error_str = str(e).lower()
            if "rate" in error_str or "quota" in error_str:
                raise RateLimitError(f"Groq rate limit: {e}") from e
            raise GroqError(f"Groq generation failed: {e}") from e

    async def classify_intent(
        self,
        message: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Classify user intent for orchestration.
        
        Args:
            message: User message to classify
            conversation_history: Previous messages for context
            
        Returns:
            Intent classification with agent recommendations
        """
        history_context = ""
        if conversation_history:
            history_lines = [
                f"{m['role']}: {m['content'][:200]}..."
                for m in conversation_history[-5:]
            ]
            history_context = f"\n\nConversation history:\n" + "\n".join(history_lines)
        
        prompt = f"""Analyze the user message and classify the intent.

Message: {message}
{history_context}

Classify into one of:
- write: User wants to store/remember information
- read: User wants to retrieve specific information
- search: User wants to discover/explore information
- graph: User wants to analyze relationships/connections
- mixed: Multiple operations required

Respond with JSON:
{{
  "intent": "intent_name",
  "entities": ["entity1", "entity2"],
  "confidence": 0.95,
  "parallel_execution": true,
  "sub_tasks": [
    {{"agent": "read", "query": "..."}},
    {{"agent": "graph", "params": {{...}}}}
  ],
  "reasoning": "brief explanation of classification"
}}"""
        
        system = "You are an intent classifier for a knowledge graph memory system. Be precise and concise."
        
        response = await self.generate(
            prompt=prompt,
            system_instruction=system,
            json_mode=True,
            temperature=0.1,
        )
        
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("intent_classification_parse_failed", response=response[:200])
            return {
                "intent": "read",
                "entities": [],
                "confidence": 0.5,
                "parallel_execution": False,
                "sub_tasks": [],
                "reasoning": "Failed to parse, defaulting to read",
            }

    async def plan_agents(
        self,
        intent: dict[str, Any],
        available_agents: list[str],
    ) -> list[dict[str, Any]]:
        """Plan which agents to spawn based on intent.
        
        Args:
            intent: Classified intent from classify_intent
            available_agents: List of available agent types
            
        Returns:
            List of agent execution plans
        """
        prompt = f"""Given the classified intent, plan which agents to spawn.

Intent: {intent}

Available agents: {available_agents}

Agent capabilities:
- memory_manager: Read/write/search memories
- context_builder: Build context from graph and vectors
- web_surfer: Search external web sources
- import_agent: Process and import data from integrations
- conflict_resolver: Resolve conflicting information
- reminder_agent: Schedule reminders

Return a JSON array of agent plans:
[
  {{
    "agent": "agent_name",
    "operation": "specific_operation",
    "params": {{}},
    "depends_on": [],
    "priority": 1
  }}
]

Order by priority (1 = highest). Identify dependencies between agents."""
        
        response = await self.generate(
            prompt=prompt,
            json_mode=True,
            temperature=0.2,
        )
        
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("agent_planning_parse_failed", response=response[:200])
            return []


# Global client instance
_groq_client: GroqClient | None = None


def get_groq_client() -> GroqClient:
    """Get the global Groq client instance."""
    global _groq_client
    if _groq_client is None:
        _groq_client = GroqClient()
    return _groq_client
