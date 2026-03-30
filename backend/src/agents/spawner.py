"""Agent spawner for dynamic agent creation and execution."""

import asyncio
from typing import Any, Type

from src.agents.base import AgentContext, AgentResult, BaseAgent
from src.agents.orchestrator import Orchestrator
from src.core.logging import get_logger

logger = get_logger(__name__)


# Agent registry
AGENT_REGISTRY: dict[str, Type[BaseAgent]] = {
    "orchestrator": Orchestrator,
    # More agents will be registered here
}


class AgentSpawner:
    """Spawns and manages agent execution.
    
    Responsibilities:
    - Create agent instances
    - Execute agents in parallel when possible
    - Handle dependencies between agents
    - Aggregate results
    """

    def __init__(self) -> None:
        self._registry = AGENT_REGISTRY.copy()

    def register(self, name: str, agent_class: Type[BaseAgent]) -> None:
        """Register a new agent type."""
        self._registry[name] = agent_class

    def spawn(self, agent_type: str) -> BaseAgent:
        """Spawn an agent instance.
        
        Args:
            agent_type: Type of agent to spawn
            
        Returns:
            Agent instance
            
        Raises:
            ValueError: If agent type is not registered
        """
        if agent_type not in self._registry:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        agent_class = self._registry[agent_type]
        agent = agent_class()
        
        logger.debug("agent_spawned", agent_type=agent_type, agent_id=agent.agent_id)
        
        return agent

    async def execute_single(
        self,
        agent_type: str,
        operation: str,
        params: dict[str, Any],
        context: AgentContext,
    ) -> AgentResult:
        """Spawn and execute a single agent.
        
        Args:
            agent_type: Type of agent to spawn
            operation: Operation to execute
            params: Operation parameters
            context: Execution context
            
        Returns:
            Agent execution result
        """
        agent = self.spawn(agent_type)
        return await agent(operation, params, context)

    async def execute_parallel(
        self,
        executions: list[dict[str, Any]],
        context: AgentContext,
    ) -> list[AgentResult]:
        """Execute multiple agents in parallel.
        
        Args:
            executions: List of {agent_type, operation, params} dicts
            context: Shared execution context
            
        Returns:
            List of results in same order as executions
        """
        tasks = []
        
        for execution in executions:
            task = self.execute_single(
                agent_type=execution["agent_type"],
                operation=execution["operation"],
                params=execution.get("params", {}),
                context=context,
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to AgentResult
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(AgentResult(
                    success=False,
                    error=str(result),
                ))
            else:
                processed_results.append(result)
        
        return processed_results

    async def execute_plan(
        self,
        plan: list[dict[str, Any]],
        context: AgentContext,
    ) -> dict[str, AgentResult]:
        """Execute an agent plan respecting dependencies.
        
        Args:
            plan: List of agent execution plans with dependencies
            context: Execution context
            
        Returns:
            Dict mapping agent operation to result
        """
        results: dict[str, AgentResult] = {}
        completed: set[str] = set()
        
        # Sort by priority
        sorted_plan = sorted(plan, key=lambda x: x.get("priority", 1))
        
        while len(completed) < len(sorted_plan):
            # Find executions ready to run (dependencies met)
            ready = []
            for item in sorted_plan:
                key = f"{item['agent']}:{item.get('operation', 'execute')}"
                if key in completed:
                    continue
                
                deps = item.get("depends_on", [])
                deps_met = all(
                    f"{d['agent']}:{d.get('operation', 'execute')}" in completed
                    for d in deps
                ) if isinstance(deps, list) and deps and isinstance(deps[0], dict) else True
                
                if deps_met:
                    ready.append(item)
            
            if not ready:
                # Prevent infinite loop if dependencies can't be resolved
                logger.warning("agent_plan_deadlock", remaining=len(sorted_plan) - len(completed))
                break
            
            # Execute ready agents in parallel
            executions = [
                {
                    "agent_type": item["agent"],
                    "operation": item.get("operation", "execute"),
                    "params": item.get("params", {}),
                }
                for item in ready
            ]
            
            parallel_results = await self.execute_parallel(executions, context)
            
            # Store results
            for item, result in zip(ready, parallel_results):
                key = f"{item['agent']}:{item.get('operation', 'execute')}"
                results[key] = result
                completed.add(key)
        
        return results

    @property
    def available_agents(self) -> list[str]:
        """List available agent types."""
        return list(self._registry.keys())


# Global spawner instance
_spawner: AgentSpawner | None = None


def get_agent_spawner() -> AgentSpawner:
    """Get the global agent spawner instance."""
    global _spawner
    if _spawner is None:
        _spawner = AgentSpawner()
    return _spawner
