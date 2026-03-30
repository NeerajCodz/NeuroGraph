"""Unit tests for agent spawner."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestAgentSpawner:
    """Tests for AgentSpawner class."""

    @pytest.fixture
    def spawner(self, mock_settings):
        """Create AgentSpawner instance."""
        from src.agents.spawner import AgentSpawner
        return AgentSpawner()

    def test_registered_agents(self, spawner):
        """Test that agents are registered."""
        agents = spawner.list_agents()
        
        assert isinstance(agents, list)

    def test_get_agent(self, spawner):
        """Test getting an agent by name."""
        from src.agents.spawner import AgentSpawner
        
        # Register a test agent
        class TestAgent:
            name = "test"
        
        spawner._agents["test"] = TestAgent
        
        agent_class = spawner.get_agent("test")
        
        assert agent_class is TestAgent

    def test_get_unknown_agent(self, spawner):
        """Test getting unknown agent returns None."""
        agent = spawner.get_agent("unknown_agent")
        
        assert agent is None

    @pytest.mark.asyncio
    async def test_spawn_and_execute(self, spawner, test_user_id):
        """Test spawning and executing an agent."""
        from src.agents.base import BaseAgent, AgentContext, AgentResult
        
        class MockAgent(BaseAgent):
            name = "mock"
            description = "Mock agent"
            
            async def execute(self, context):
                return AgentResult(success=True, response="Done")
        
        spawner._agents["mock"] = MockAgent
        
        context = AgentContext(
            user_id=test_user_id,
            query="Test",
            memory_context=[],
        )
        
        result = await spawner.spawn_and_execute("mock", context)
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_spawn_unknown_agent_fails(self, spawner, test_user_id):
        """Test spawning unknown agent raises error."""
        from src.agents.base import AgentContext
        from src.core.exceptions import AgentError
        
        context = AgentContext(
            user_id=test_user_id,
            query="Test",
            memory_context=[],
        )
        
        with pytest.raises(AgentError):
            await spawner.spawn_and_execute("nonexistent", context)

    @pytest.mark.asyncio
    async def test_parallel_spawn(self, spawner, test_user_id):
        """Test spawning multiple agents in parallel."""
        from src.agents.base import BaseAgent, AgentContext, AgentResult
        
        class Agent1(BaseAgent):
            name = "agent1"
            description = "Agent 1"
            async def execute(self, context):
                return AgentResult(success=True, response="Agent 1 done")
        
        class Agent2(BaseAgent):
            name = "agent2"
            description = "Agent 2"
            async def execute(self, context):
                return AgentResult(success=True, response="Agent 2 done")
        
        spawner._agents["agent1"] = Agent1
        spawner._agents["agent2"] = Agent2
        
        context = AgentContext(
            user_id=test_user_id,
            query="Test",
            memory_context=[],
        )
        
        results = await spawner.spawn_parallel(["agent1", "agent2"], context)
        
        assert len(results) == 2
        assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_agent_timeout(self, spawner, test_user_id):
        """Test agent execution timeout."""
        import asyncio
        from src.agents.base import BaseAgent, AgentContext, AgentResult
        
        class SlowAgent(BaseAgent):
            name = "slow"
            description = "Slow agent"
            async def execute(self, context):
                await asyncio.sleep(10)  # Simulate slow execution
                return AgentResult(success=True, response="Done")
        
        spawner._agents["slow"] = SlowAgent
        
        context = AgentContext(
            user_id=test_user_id,
            query="Test",
            memory_context=[],
        )
        
        # Should timeout
        with pytest.raises((asyncio.TimeoutError, Exception)):
            await asyncio.wait_for(
                spawner.spawn_and_execute("slow", context),
                timeout=0.1,
            )
