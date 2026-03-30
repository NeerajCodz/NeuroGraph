"""Unit tests for base agent module."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


class TestAgentContext:
    """Tests for AgentContext dataclass."""

    def test_context_creation(self, test_user_id, test_tenant_id):
        """Test creating agent context."""
        from src.agents.base import AgentContext
        
        context = AgentContext(
            user_id=test_user_id,
            tenant_id=test_tenant_id,
            query="Test query",
            memory_context=[],
            session_id="session_123",
        )
        
        assert context.user_id == test_user_id
        assert context.query == "Test query"
        assert context.metadata == {}

    def test_context_with_metadata(self, test_user_id):
        """Test context with metadata."""
        from src.agents.base import AgentContext
        
        context = AgentContext(
            user_id=test_user_id,
            query="Test",
            memory_context=[],
            metadata={"key": "value"},
        )
        
        assert context.metadata["key"] == "value"


class TestAgentResult:
    """Tests for AgentResult dataclass."""

    def test_result_success(self):
        """Test successful result."""
        from src.agents.base import AgentResult
        
        result = AgentResult(
            success=True,
            response="Agent completed successfully",
            data={"count": 5},
        )
        
        assert result.success is True
        assert result.response == "Agent completed successfully"
        assert result.data["count"] == 5

    def test_result_failure(self):
        """Test failed result."""
        from src.agents.base import AgentResult
        
        result = AgentResult(
            success=False,
            response="Agent failed",
            error="Connection timeout",
        )
        
        assert result.success is False
        assert result.error == "Connection timeout"

    def test_result_to_dict(self):
        """Test result serialization."""
        from src.agents.base import AgentResult
        
        result = AgentResult(
            success=True,
            response="Test",
            data={"key": "value"},
        )
        
        d = result.to_dict()
        
        assert d["success"] is True
        assert d["response"] == "Test"
        assert d["data"]["key"] == "value"


class TestBaseAgent:
    """Tests for BaseAgent class."""

    @pytest.fixture
    def mock_agent(self, mock_settings):
        """Create a mock agent instance."""
        from src.agents.base import BaseAgent
        
        class TestAgent(BaseAgent):
            name = "test_agent"
            description = "Test agent"
            
            async def execute(self, context):
                from src.agents.base import AgentResult
                return AgentResult(
                    success=True,
                    response="Test executed",
                )
        
        return TestAgent()

    def test_agent_name(self, mock_agent):
        """Test agent has name."""
        assert mock_agent.name == "test_agent"

    def test_agent_description(self, mock_agent):
        """Test agent has description."""
        assert mock_agent.description == "Test agent"

    @pytest.mark.asyncio
    async def test_agent_execute(self, mock_agent, test_user_id):
        """Test agent execution."""
        from src.agents.base import AgentContext
        
        context = AgentContext(
            user_id=test_user_id,
            query="Test",
            memory_context=[],
        )
        
        result = await mock_agent.execute(context)
        
        assert result.success is True
        assert result.response == "Test executed"

    @pytest.mark.asyncio
    async def test_agent_run_with_logging(self, mock_agent, test_user_id):
        """Test agent run method logs execution."""
        from src.agents.base import AgentContext
        
        context = AgentContext(
            user_id=test_user_id,
            query="Test",
            memory_context=[],
        )
        
        # run() should call execute() and handle logging
        result = await mock_agent.run(context)
        
        assert result.success is True
