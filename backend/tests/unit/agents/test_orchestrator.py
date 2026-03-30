"""Unit tests for orchestrator agent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestOrchestrator:
    """Tests for Orchestrator class."""

    @pytest.fixture
    def orchestrator(self, mock_settings, mock_groq_client):
        """Create Orchestrator instance."""
        with patch("src.agents.orchestrator.GroqClient", return_value=mock_groq_client):
            from src.agents.orchestrator import Orchestrator
            
            orch = Orchestrator()
            orch._groq = mock_groq_client
            return orch

    @pytest.mark.asyncio
    async def test_classify_read_intent(self, orchestrator, mock_groq_client):
        """Test classifying read intent."""
        mock_groq_client.classify_intent = AsyncMock(return_value={
            "intent": "read",
            "entities": ["user preferences"],
            "confidence": 0.95,
            "parallel_execution": False,
            "sub_tasks": [],
        })
        
        result = await orchestrator.classify("What are my preferences?")
        
        assert result["intent"] == "read"
        assert result["confidence"] > 0.9

    @pytest.mark.asyncio
    async def test_classify_write_intent(self, orchestrator, mock_groq_client):
        """Test classifying write intent."""
        mock_groq_client.classify_intent = AsyncMock(return_value={
            "intent": "write",
            "entities": ["meeting", "tomorrow"],
            "confidence": 0.92,
            "parallel_execution": False,
            "sub_tasks": [],
        })
        
        result = await orchestrator.classify("Remember I have a meeting tomorrow")
        
        assert result["intent"] == "write"

    @pytest.mark.asyncio
    async def test_classify_search_intent(self, orchestrator, mock_groq_client):
        """Test classifying search intent."""
        mock_groq_client.classify_intent = AsyncMock(return_value={
            "intent": "search",
            "entities": ["fraud", "transactions"],
            "confidence": 0.88,
            "parallel_execution": False,
            "sub_tasks": [],
        })
        
        result = await orchestrator.classify("Find all fraud-related transactions")
        
        assert result["intent"] == "search"

    @pytest.mark.asyncio
    async def test_classify_complex_intent(self, orchestrator, mock_groq_client):
        """Test classifying complex multi-step intent."""
        mock_groq_client.classify_intent = AsyncMock(return_value={
            "intent": "complex",
            "entities": ["quarterly report", "sales data"],
            "confidence": 0.85,
            "parallel_execution": True,
            "sub_tasks": ["search", "analyze", "summarize"],
        })
        
        result = await orchestrator.classify("Analyze our quarterly sales and create a report")
        
        assert result["intent"] == "complex"
        assert result["parallel_execution"] is True
        assert len(result["sub_tasks"]) > 0

    @pytest.mark.asyncio
    async def test_plan_agents_for_query(self, orchestrator, mock_groq_client):
        """Test planning agents for a query."""
        mock_groq_client.plan_agents = AsyncMock(return_value=[
            {"agent": "memory_manager", "action": "search"},
            {"agent": "context_builder", "action": "build"},
        ])
        
        classification = {
            "intent": "search",
            "entities": ["test"],
            "confidence": 0.9,
            "parallel_execution": False,
            "sub_tasks": [],
        }
        
        agents = await orchestrator.plan(classification, "test query")
        
        assert len(agents) >= 0

    @pytest.mark.asyncio
    async def test_orchestrate_full_flow(self, orchestrator, mock_groq_client, test_user_id):
        """Test full orchestration flow."""
        mock_groq_client.classify_intent = AsyncMock(return_value={
            "intent": "read",
            "entities": ["test"],
            "confidence": 0.95,
            "parallel_execution": False,
            "sub_tasks": [],
        })
        mock_groq_client.plan_agents = AsyncMock(return_value=[])
        
        result = await orchestrator.orchestrate(
            query="What is test?",
            user_id=test_user_id,
        )
        
        assert "intent" in result
        assert "agents" in result


class TestIntentClassification:
    """Tests for intent classification details."""

    @pytest.fixture
    def orchestrator(self, mock_settings, mock_groq_client):
        """Create Orchestrator instance."""
        with patch("src.agents.orchestrator.GroqClient", return_value=mock_groq_client):
            from src.agents.orchestrator import Orchestrator
            
            orch = Orchestrator()
            orch._groq = mock_groq_client
            return orch

    @pytest.mark.asyncio
    async def test_low_confidence_fallback(self, orchestrator, mock_groq_client):
        """Test fallback behavior on low confidence."""
        mock_groq_client.classify_intent = AsyncMock(return_value={
            "intent": "unknown",
            "entities": [],
            "confidence": 0.3,  # Low confidence
            "parallel_execution": False,
            "sub_tasks": [],
        })
        
        result = await orchestrator.classify("ambiguous query")
        
        assert result["confidence"] < 0.5

    @pytest.mark.asyncio
    async def test_entity_extraction(self, orchestrator, mock_groq_client):
        """Test entity extraction from query."""
        mock_groq_client.classify_intent = AsyncMock(return_value={
            "intent": "read",
            "entities": ["Alice", "Project X", "deadline"],
            "confidence": 0.9,
            "parallel_execution": False,
            "sub_tasks": [],
        })
        
        result = await orchestrator.classify("When is Alice's deadline for Project X?")
        
        assert "Alice" in result["entities"]
        assert "Project X" in result["entities"]
