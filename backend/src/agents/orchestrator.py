"""Orchestrator agent using Groq for intent classification and agent planning."""

from typing import Any

from src.agents.base import AgentContext, AgentResult, BaseAgent
from src.core.logging import get_logger
from src.models.groq import get_groq_client

logger = get_logger(__name__)


class Orchestrator(BaseAgent):
    """Orchestrator agent for chat interface.
    
    Uses Groq (Llama 3.3) for fast intent classification and agent planning.
    Only used for chat interface - MCP tools bypass orchestration.
    """

    @property
    def name(self) -> str:
        return "orchestrator"

    @property
    def description(self) -> str:
        return "Classifies intent and plans agent execution for chat interface"

    @property
    def capabilities(self) -> list[str]:
        return ["classify_intent", "plan_agents", "process_message"]

    async def execute(
        self,
        operation: str,
        params: dict[str, Any],
        context: AgentContext,
    ) -> AgentResult:
        """Execute orchestration operation."""
        if operation == "classify_intent":
            return await self._classify_intent(params, context)
        elif operation == "plan_agents":
            return await self._plan_agents(params, context)
        elif operation == "process_message":
            return await self._process_message(params, context)
        else:
            return AgentResult(success=False, error=f"Unknown operation: {operation}")

    async def _classify_intent(
        self,
        params: dict[str, Any],
        context: AgentContext,
    ) -> AgentResult:
        """Classify user intent using Groq.
        
        Returns intent type and confidence for agent selection.
        """
        message = params.get("message", "")
        if not message:
            return AgentResult(success=False, error="Message required")
        
        groq = get_groq_client()
        
        intent = await groq.classify_intent(
            message=message,
            conversation_history=context.conversation_history,
        )
        
        logger.debug(
            "intent_classified",
            intent=intent.get("intent"),
            confidence=intent.get("confidence"),
        )
        
        return AgentResult(
            success=True,
            data=intent,
            metadata={"model": "groq/llama-3.3-70b"},
        )

    async def _plan_agents(
        self,
        params: dict[str, Any],
        context: AgentContext,
    ) -> AgentResult:
        """Plan which agents to spawn based on classified intent."""
        intent = params.get("intent", {})
        if not intent:
            return AgentResult(success=False, error="Intent required")
        
        available_agents = [
            "memory_manager",
            "context_builder",
            "web_surfer",
            "import_agent",
            "conflict_resolver",
            "reminder_agent",
        ]
        
        groq = get_groq_client()
        
        agent_plans = await groq.plan_agents(
            intent=intent,
            available_agents=available_agents,
        )
        
        logger.debug(
            "agents_planned",
            plans_count=len(agent_plans),
        )
        
        return AgentResult(
            success=True,
            data=agent_plans,
        )

    async def _process_message(
        self,
        params: dict[str, Any],
        context: AgentContext,
    ) -> AgentResult:
        """Full message processing pipeline.
        
        1. Classify intent
        2. Plan agents
        3. Execute agents (via spawner)
        4. Build context
        5. Generate response
        """
        message = params.get("message", "")
        if not message:
            return AgentResult(success=False, error="Message required")
        
        # Step 1: Classify intent
        intent_result = await self._classify_intent(
            {"message": message},
            context,
        )
        
        if not intent_result.success:
            return intent_result
        
        intent = intent_result.data
        
        # Step 2: Plan agents
        plan_result = await self._plan_agents(
            {"intent": intent},
            context,
        )
        
        if not plan_result.success:
            return plan_result
        
        agent_plans = plan_result.data
        
        # Step 3-5: Execute agents, build context, generate response
        # This will be handled by the AgentSpawner
        
        return AgentResult(
            success=True,
            data={
                "intent": intent,
                "agent_plans": agent_plans,
                "message": message,
            },
        )
