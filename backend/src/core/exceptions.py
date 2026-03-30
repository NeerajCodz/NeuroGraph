"""Custom exceptions for NeuroGraph."""

from http import HTTPStatus
from typing import Any


class NeuroGraphException(Exception):
    """Base exception for all NeuroGraph errors."""

    def __init__(
        self,
        message: str,
        code: str = "NEUROGRAPH_ERROR",
        status_code: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dict for API responses."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


# Alias for backward compatibility
NeuroGraphError = NeuroGraphException


class ConfigurationError(NeuroGraphException):
    """Raised when there's a configuration error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "CONFIGURATION_ERROR", HTTPStatus.INTERNAL_SERVER_ERROR, details)


class DatabaseError(NeuroGraphException):
    """Base exception for database errors."""

    def __init__(self, message: str, code: str = "DATABASE_ERROR", details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code, HTTPStatus.SERVICE_UNAVAILABLE, details)


class Neo4jError(DatabaseError):
    """Raised when there's a Neo4j error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "NEO4J_ERROR", details)


class PostgresError(DatabaseError):
    """Raised when there's a PostgreSQL error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "POSTGRES_ERROR", details)


class RedisError(DatabaseError):
    """Raised when there's a Redis error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "REDIS_ERROR", details)


class ConnectionError(DatabaseError):
    """Raised when database connection fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "CONNECTION_ERROR", details)


class QueryError(DatabaseError):
    """Raised when query execution fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.code = "QUERY_ERROR"
        self.status_code = HTTPStatus.BAD_REQUEST
        self.details = details or {}
        Exception.__init__(self, message)


class TransactionError(DatabaseError):
    """Raised when transaction fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.code = "TRANSACTION_ERROR"
        self.status_code = HTTPStatus.CONFLICT
        self.details = details or {}
        Exception.__init__(self, message)


class MemoryError(NeuroGraphException):
    """Base exception for memory system errors."""

    def __init__(self, message: str, code: str = "MEMORY_ERROR", details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code, HTTPStatus.INTERNAL_SERVER_ERROR, details)


class MemoryNotFoundError(MemoryError):
    """Raised when a memory/entity is not found."""

    def __init__(self, memory_id: str, details: dict[str, Any] | None = None) -> None:
        self.memory_id = memory_id
        message = f"Memory not found: {memory_id}"
        self.message = message
        self.code = "MEMORY_NOT_FOUND"
        self.status_code = HTTPStatus.NOT_FOUND
        self.details = details or {}
        Exception.__init__(self, message)


class MemoryAccessDeniedError(MemoryError):
    """Raised when user lacks access to a memory layer."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "MEMORY_ACCESS_DENIED", details)
        self.status_code = HTTPStatus.FORBIDDEN


class MemoryConflictError(MemoryError):
    """Raised when there's a conflict in memory data."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.code = "MEMORY_CONFLICT"
        self.status_code = HTTPStatus.CONFLICT
        self.details = details or {}
        Exception.__init__(self, message)


class LayerError(MemoryError):
    """Raised when there's an invalid layer operation."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "LAYER_ERROR", details)


class LayerAccessError(MemoryError):
    """Raised when user lacks access to perform operation on layer."""

    def __init__(self, layer: str, operation: str, details: dict[str, Any] | None = None) -> None:
        self.layer = layer
        self.operation = operation
        message = f"Cannot perform {operation} on {layer} layer"
        self.message = message
        self.code = "LAYER_ACCESS_ERROR"
        self.status_code = HTTPStatus.FORBIDDEN
        self.details = details or {}
        Exception.__init__(self, message)


class AuthenticationError(NeuroGraphException):
    """Raised when authentication fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.code = "AUTHENTICATION_ERROR"
        self.status_code = HTTPStatus.UNAUTHORIZED
        self.details = details or {}
        Exception.__init__(self, message)


class AuthorizationError(NeuroGraphException):
    """Raised when user lacks permission."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.code = "AUTHORIZATION_ERROR"
        self.status_code = HTTPStatus.FORBIDDEN
        self.details = details or {}
        Exception.__init__(self, message)


class TokenError(AuthenticationError):
    """Raised when there's a JWT token error."""


class TokenExpiredError(TokenError):
    """Raised when JWT token has expired."""

    def __init__(self, message: str = "Token has expired", details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.code = "TOKEN_EXPIRED"
        self.status_code = HTTPStatus.UNAUTHORIZED
        self.details = details or {}
        Exception.__init__(self, message)


class InvalidTokenError(TokenError):
    """Raised when JWT token is invalid."""

    def __init__(self, message: str = "Invalid token", details: dict[str, Any] | None = None) -> None:
        super().__init__(message, details)
        self.code = "INVALID_TOKEN"


class LLMError(NeuroGraphException):
    """Base exception for LLM errors."""

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        model: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.provider = provider
        self.model = model
        self.message = message
        self.code = "LLM_ERROR"
        self.status_code = HTTPStatus.SERVICE_UNAVAILABLE
        self.details = details or {}
        Exception.__init__(self, message)


class GeminiError(LLMError):
    """Raised when there's a Gemini API error."""

    def __init__(self, message: str, model: str | None = None, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "gemini", model, details)
        self.code = "GEMINI_ERROR"


class GroqError(LLMError):
    """Raised when there's a Groq API error."""

    def __init__(self, message: str, model: str | None = None, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "groq", model, details)
        self.code = "GROQ_ERROR"


class EmbeddingError(LLMError):
    """Raised when embedding generation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.code = "EMBEDDING_ERROR"
        self.status_code = HTTPStatus.SERVICE_UNAVAILABLE
        self.details = details or {}
        self.provider = None
        self.model = None
        Exception.__init__(self, message)


class RateLimitError(LLMError):
    """Raised when API rate limit is hit."""

    def __init__(self, provider: str, retry_after: int | None = None, details: dict[str, Any] | None = None) -> None:
        self.retry_after = retry_after
        message = f"Rate limit exceeded for {provider}"
        self.message = message
        self.code = "RATE_LIMIT_ERROR"
        self.status_code = HTTPStatus.TOO_MANY_REQUESTS
        self.details = details or {}
        self.provider = provider
        self.model = None
        Exception.__init__(self, message)


class RAGError(NeuroGraphException):
    """Base exception for RAG pipeline errors."""

    def __init__(self, message: str, code: str = "RAG_ERROR", details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code, HTTPStatus.INTERNAL_SERVER_ERROR, details)


class SearchError(RAGError):
    """Raised when search operation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "SEARCH_ERROR", details)


class ContextBuildError(RAGError):
    """Raised when context assembly fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "CONTEXT_BUILD_ERROR", details)


class TokenBudgetExceededError(RAGError):
    """Raised when context exceeds token budget."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "TOKEN_BUDGET_EXCEEDED", details)


class AgentError(NeuroGraphException):
    """Base exception for agent errors."""

    def __init__(
        self,
        message: str,
        agent_name: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.agent_name = agent_name
        self.message = message
        self.code = "AGENT_ERROR"
        self.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        self.details = details or {}
        Exception.__init__(self, message)


class AgentTimeoutError(AgentError):
    """Raised when agent execution times out."""

    def __init__(self, agent_name: str | None = None, details: dict[str, Any] | None = None) -> None:
        message = f"Agent {agent_name or 'unknown'} timed out"
        super().__init__(message, agent_name, details)
        self.code = "AGENT_TIMEOUT"


class AgentSpawnError(AgentError):
    """Raised when agent spawning fails."""

    def __init__(self, agent_name: str | None = None, details: dict[str, Any] | None = None) -> None:
        message = f"Failed to spawn agent {agent_name or 'unknown'}"
        super().__init__(message, agent_name, details)
        self.code = "AGENT_SPAWN_ERROR"


class OrchestrationError(AgentError):
    """Raised when orchestration fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.code = "ORCHESTRATION_ERROR"
        self.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        self.details = details or {}
        self.agent_name = None
        Exception.__init__(self, message)


class ToolExecutionError(AgentError):
    """Raised when tool execution fails."""

    def __init__(self, tool_name: str, message: str, details: dict[str, Any] | None = None) -> None:
        self.tool_name = tool_name
        full_message = f"Tool {tool_name} failed: {message}"
        self.message = full_message
        self.code = "TOOL_EXECUTION_ERROR"
        self.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        self.details = details or {}
        self.agent_name = None
        Exception.__init__(self, full_message)


class MCPError(NeuroGraphException):
    """Base exception for MCP errors."""

    def __init__(self, message: str, code: str = "MCP_ERROR", details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code, HTTPStatus.INTERNAL_SERVER_ERROR, details)


class MCPSessionError(MCPError):
    """Raised when there's an MCP session error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "MCP_SESSION_ERROR", details)


class MCPToolError(MCPError):
    """Raised when MCP tool execution fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "MCP_TOOL_ERROR", details)


class WebhookError(NeuroGraphException):
    """Base exception for webhook errors."""

    def __init__(self, message: str, code: str = "WEBHOOK_ERROR", details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code, HTTPStatus.BAD_REQUEST, details)


class WebhookVerificationError(WebhookError):
    """Raised when webhook signature verification fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "WEBHOOK_VERIFICATION_ERROR", details)


class WebhookProcessingError(WebhookError):
    """Raised when webhook processing fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "WEBHOOK_PROCESSING_ERROR", details)


class IntegrationError(NeuroGraphException):
    """Base exception for integration errors."""

    def __init__(self, message: str, code: str = "INTEGRATION_ERROR", details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code, HTTPStatus.SERVICE_UNAVAILABLE, details)


class SlackError(IntegrationError):
    """Raised when there's a Slack integration error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "SLACK_ERROR", details)


class GitHubError(IntegrationError):
    """Raised when there's a GitHub integration error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "GITHUB_ERROR", details)


class GmailError(IntegrationError):
    """Raised when there's a Gmail integration error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "GMAIL_ERROR", details)


class ValidationError(NeuroGraphException):
    """Raised when validation fails."""

    def __init__(self, message: str, code: str = "VALIDATION_ERROR", details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code, HTTPStatus.BAD_REQUEST, details)


class EntityValidationError(ValidationError):
    """Raised when entity validation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "ENTITY_VALIDATION_ERROR", details)


class RelationshipValidationError(ValidationError):
    """Raised when relationship validation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "RELATIONSHIP_VALIDATION_ERROR", details)
