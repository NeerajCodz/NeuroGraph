"""Base agent class for all NeuroGraph agents."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AgentContext:
    """Context passed to agent execution."""
    user_id: UUID
    tenant_id: UUID | None = None
    layer: str = "personal"
    include_global: bool = False
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Result from agent execution."""
    success: bool
    data: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0


class BaseAgent(ABC):
    """Abstract base class for all agents.
    
    Key principles:
    - Stateless: No persistent state between invocations
    - Specialized: Each agent handles a specific category of operations
    - Ephemeral: Created, executed, destroyed
    """

    def __init__(self, agent_id: str | None = None) -> None:
        self.agent_id = agent_id or f"agent_{uuid4().hex[:8]}"
        self.created_at = datetime.utcnow()

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent type name."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Agent description for orchestration."""
        ...

    @property
    def capabilities(self) -> list[str]:
        """List of operations this agent can perform."""
        return []

    @abstractmethod
    async def execute(
        self,
        operation: str,
        params: dict[str, Any],
        context: AgentContext,
    ) -> AgentResult:
        """Execute an operation.
        
        Args:
            operation: Specific operation to perform
            params: Operation parameters
            context: Execution context
            
        Returns:
            AgentResult with execution outcome
        """
        ...

    async def __call__(
        self,
        operation: str,
        params: dict[str, Any],
        context: AgentContext,
    ) -> AgentResult:
        """Allow agent to be called directly."""
        import time
        start = time.perf_counter()
        
        try:
            logger.info(
                "agent_execute_start",
                agent_id=self.agent_id,
                agent_type=self.name,
                operation=operation,
                user_id=str(context.user_id),
            )
            
            result = await self.execute(operation, params, context)
            
            execution_time = (time.perf_counter() - start) * 1000
            result.execution_time_ms = execution_time
            
            logger.info(
                "agent_execute_complete",
                agent_id=self.agent_id,
                success=result.success,
                execution_time_ms=execution_time,
            )
            
            return result
            
        except Exception as e:
            execution_time = (time.perf_counter() - start) * 1000
            
            logger.error(
                "agent_execute_failed",
                agent_id=self.agent_id,
                error=str(e),
                execution_time_ms=execution_time,
            )
            
            return AgentResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
            )
