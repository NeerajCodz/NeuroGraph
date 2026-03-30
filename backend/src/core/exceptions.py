"""Custom exceptions for NeuroGraph."""

from typing import Any


class NeuroGraphError(Exception):
    """Base exception for all NeuroGraph errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(NeuroGraphError):
    """Raised when there's a configuration error."""


class DatabaseError(NeuroGraphError):
    """Base exception for database errors."""


class Neo4jError(DatabaseError):
    """Raised when there's a Neo4j error."""


class PostgresError(DatabaseError):
    """Raised when there's a PostgreSQL error."""


class RedisError(DatabaseError):
    """Raised when there's a Redis error."""


class ConnectionError(DatabaseError):
    """Raised when database connection fails."""


class MemoryError(NeuroGraphError):
    """Base exception for memory system errors."""


class MemoryNotFoundError(MemoryError):
    """Raised when a memory/entity is not found."""


class MemoryAccessDeniedError(MemoryError):
    """Raised when user lacks access to a memory layer."""


class MemoryConflictError(MemoryError):
    """Raised when there's a conflict in memory data."""


class LayerError(MemoryError):
    """Raised when there's an invalid layer operation."""


class AuthenticationError(NeuroGraphError):
    """Raised when authentication fails."""


class AuthorizationError(NeuroGraphError):
    """Raised when user lacks permission."""


class TokenError(AuthenticationError):
    """Raised when there's a JWT token error."""


class TokenExpiredError(TokenError):
    """Raised when JWT token has expired."""


class InvalidTokenError(TokenError):
    """Raised when JWT token is invalid."""


class LLMError(NeuroGraphError):
    """Base exception for LLM errors."""


class GeminiError(LLMError):
    """Raised when there's a Gemini API error."""


class GroqError(LLMError):
    """Raised when there's a Groq API error."""


class EmbeddingError(LLMError):
    """Raised when embedding generation fails."""


class RateLimitError(LLMError):
    """Raised when API rate limit is hit."""


class RAGError(NeuroGraphError):
    """Base exception for RAG pipeline errors."""


class SearchError(RAGError):
    """Raised when search operation fails."""


class ContextBuildError(RAGError):
    """Raised when context assembly fails."""


class TokenBudgetExceededError(RAGError):
    """Raised when context exceeds token budget."""


class AgentError(NeuroGraphError):
    """Base exception for agent errors."""


class AgentTimeoutError(AgentError):
    """Raised when agent execution times out."""


class AgentSpawnError(AgentError):
    """Raised when agent spawning fails."""


class OrchestrationError(AgentError):
    """Raised when orchestration fails."""


class MCPError(NeuroGraphError):
    """Base exception for MCP errors."""


class MCPSessionError(MCPError):
    """Raised when there's an MCP session error."""


class MCPToolError(MCPError):
    """Raised when MCP tool execution fails."""


class WebhookError(NeuroGraphError):
    """Base exception for webhook errors."""


class WebhookVerificationError(WebhookError):
    """Raised when webhook signature verification fails."""


class WebhookProcessingError(WebhookError):
    """Raised when webhook processing fails."""


class IntegrationError(NeuroGraphError):
    """Base exception for integration errors."""


class SlackError(IntegrationError):
    """Raised when there's a Slack integration error."""


class GitHubError(IntegrationError):
    """Raised when there's a GitHub integration error."""


class GmailError(IntegrationError):
    """Raised when there's a Gmail integration error."""


class ValidationError(NeuroGraphError):
    """Raised when validation fails."""


class EntityValidationError(ValidationError):
    """Raised when entity validation fails."""


class RelationshipValidationError(ValidationError):
    """Raised when relationship validation fails."""
