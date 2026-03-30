"""Unit tests for exceptions module."""

import pytest
from http import HTTPStatus


class TestNeuroGraphException:
    """Tests for base exception."""

    def test_neurograph_exception_defaults(self):
        """Test exception with defaults."""
        from src.core.exceptions import NeuroGraphException
        
        exc = NeuroGraphException("Test error")
        
        assert str(exc) == "Test error"
        assert exc.message == "Test error"
        assert exc.code == "NEUROGRAPH_ERROR"
        assert exc.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

    def test_neurograph_exception_custom(self):
        """Test exception with custom values."""
        from src.core.exceptions import NeuroGraphException
        
        exc = NeuroGraphException(
            "Custom error",
            code="CUSTOM_CODE",
            status_code=HTTPStatus.BAD_REQUEST,
            details={"key": "value"},
        )
        
        assert exc.message == "Custom error"
        assert exc.code == "CUSTOM_CODE"
        assert exc.status_code == HTTPStatus.BAD_REQUEST
        assert exc.details == {"key": "value"}

    def test_neurograph_exception_to_dict(self):
        """Test exception serialization."""
        from src.core.exceptions import NeuroGraphException
        
        exc = NeuroGraphException(
            "Test error",
            code="TEST_CODE",
            details={"foo": "bar"},
        )
        
        result = exc.to_dict()
        
        assert result["error"]["code"] == "TEST_CODE"
        assert result["error"]["message"] == "Test error"
        assert result["error"]["details"] == {"foo": "bar"}


class TestDatabaseExceptions:
    """Tests for database exceptions."""

    def test_connection_error(self):
        """Test ConnectionError exception."""
        from src.core.exceptions import ConnectionError
        
        exc = ConnectionError("Failed to connect")
        
        assert exc.code == "CONNECTION_ERROR"
        assert exc.status_code == HTTPStatus.SERVICE_UNAVAILABLE

    def test_query_error(self):
        """Test QueryError exception."""
        from src.core.exceptions import QueryError
        
        exc = QueryError("Invalid query")
        
        assert exc.code == "QUERY_ERROR"
        assert exc.status_code == HTTPStatus.BAD_REQUEST

    def test_transaction_error(self):
        """Test TransactionError exception."""
        from src.core.exceptions import TransactionError
        
        exc = TransactionError("Transaction failed")
        
        assert exc.code == "TRANSACTION_ERROR"
        assert exc.status_code == HTTPStatus.CONFLICT


class TestMemoryExceptions:
    """Tests for memory exceptions."""

    def test_memory_not_found(self):
        """Test MemoryNotFoundError exception."""
        from src.core.exceptions import MemoryNotFoundError
        
        exc = MemoryNotFoundError("node_123")
        
        assert "node_123" in exc.message
        assert exc.code == "MEMORY_NOT_FOUND"
        assert exc.status_code == HTTPStatus.NOT_FOUND

    def test_memory_conflict_error(self):
        """Test MemoryConflictError exception."""
        from src.core.exceptions import MemoryConflictError
        
        exc = MemoryConflictError("Conflicting memories")
        
        assert exc.code == "MEMORY_CONFLICT"
        assert exc.status_code == HTTPStatus.CONFLICT

    def test_layer_access_error(self):
        """Test LayerAccessError exception."""
        from src.core.exceptions import LayerAccessError
        
        exc = LayerAccessError("global", "write")
        
        assert "global" in exc.message
        assert "write" in exc.message
        assert exc.code == "LAYER_ACCESS_ERROR"
        assert exc.status_code == HTTPStatus.FORBIDDEN


class TestAuthExceptions:
    """Tests for authentication exceptions."""

    def test_authentication_error(self):
        """Test AuthenticationError exception."""
        from src.core.exceptions import AuthenticationError
        
        exc = AuthenticationError("Invalid token")
        
        assert exc.code == "AUTHENTICATION_ERROR"
        assert exc.status_code == HTTPStatus.UNAUTHORIZED

    def test_authorization_error(self):
        """Test AuthorizationError exception."""
        from src.core.exceptions import AuthorizationError
        
        exc = AuthorizationError("Insufficient permissions")
        
        assert exc.code == "AUTHORIZATION_ERROR"
        assert exc.status_code == HTTPStatus.FORBIDDEN

    def test_token_expired_error(self):
        """Test TokenExpiredError exception."""
        from src.core.exceptions import TokenExpiredError
        
        exc = TokenExpiredError()
        
        assert exc.code == "TOKEN_EXPIRED"
        assert exc.status_code == HTTPStatus.UNAUTHORIZED


class TestAgentExceptions:
    """Tests for agent exceptions."""

    def test_agent_error(self):
        """Test AgentError exception."""
        from src.core.exceptions import AgentError
        
        exc = AgentError("Agent failed", agent_name="memory_manager")
        
        assert exc.agent_name == "memory_manager"
        assert exc.code == "AGENT_ERROR"

    def test_orchestration_error(self):
        """Test OrchestrationError exception."""
        from src.core.exceptions import OrchestrationError
        
        exc = OrchestrationError("Orchestration failed")
        
        assert exc.code == "ORCHESTRATION_ERROR"

    def test_tool_execution_error(self):
        """Test ToolExecutionError exception."""
        from src.core.exceptions import ToolExecutionError
        
        exc = ToolExecutionError("remember", "Failed to store memory")
        
        assert exc.tool_name == "remember"
        assert "remember" in exc.message
        assert exc.code == "TOOL_EXECUTION_ERROR"


class TestLLMExceptions:
    """Tests for LLM exceptions."""

    def test_llm_error(self):
        """Test LLMError exception."""
        from src.core.exceptions import LLMError
        
        exc = LLMError("Generation failed", provider="gemini", model="flash")
        
        assert exc.provider == "gemini"
        assert exc.model == "flash"
        assert exc.code == "LLM_ERROR"

    def test_rate_limit_error(self):
        """Test RateLimitError exception."""
        from src.core.exceptions import RateLimitError
        
        exc = RateLimitError("gemini", retry_after=60)
        
        assert exc.retry_after == 60
        assert exc.code == "RATE_LIMIT_ERROR"
        assert exc.status_code == HTTPStatus.TOO_MANY_REQUESTS

    def test_embedding_error(self):
        """Test EmbeddingError exception."""
        from src.core.exceptions import EmbeddingError
        
        exc = EmbeddingError("Failed to generate embedding")
        
        assert exc.code == "EMBEDDING_ERROR"
