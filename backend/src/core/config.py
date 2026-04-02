"""Core configuration management using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "neurograph"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = False
    app_secret_key: SecretStr = Field(default=...)

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    log_level: Literal["debug", "info", "warning", "error", "critical"] = "info"

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:5174,https://neurograph-ai.vercel.app"
    cors_origin_regex: str | None = None

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: SecretStr = Field(default=...)
    neo4j_database: str = "neo4j"
    neo4j_max_connection_pool_size: int = 50

    # PostgreSQL
    database_url: str | None = None  # Generic DB URL (e.g., Neon/Vercel)
    postgres_uri: str | None = None  # Legacy DSN alias
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "neurograph"
    postgres_password: SecretStr = Field(default=...)
    postgres_db: str = "neurograph"
    postgres_min_pool_size: int = 5
    postgres_max_pool_size: int = 20

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 20

    # Gemini API
    gemini_api_key: SecretStr = Field(default=...)
    gemini_model_flash: str = "gemini-2.0-flash"
    gemini_model_pro: str = "gemini-2.5-pro"
    gemini_model_lite: str = "gemini-2.0-flash-lite"
    gemini_model_embedding: str = "models/gemini-embedding-2-preview"

    # Groq API
    groq_api_key: SecretStr = Field(default=...)
    groq_model: str = "llama-3.3-70b-versatile"

    # NVIDIA API (build.nvidia.com)
    nvidia_api_key: SecretStr | None = None
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"

    # Tavily API
    tavily_api_key: SecretStr | None = None
    
    # Default model provider and model for agents
    default_llm_provider: str = "gemini"
    default_llm_model: str = "gemini-2.0-flash"

    # JWT Auth
    jwt_secret_key: SecretStr = Field(default=...)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Memory Settings
    memory_default_layer: Literal["personal", "tenant", "global"] = "personal"
    memory_max_results: int = 20
    memory_min_confidence: float = 0.5
    memory_decay_rate: float = 0.05
    memory_max_hop_depth: int = 3

    # RAG Settings
    rag_embedding_dimension: int = 768
    rag_similarity_threshold: float = 0.5  # Lowered from 0.7 for better recall
    rag_max_context_tokens: int = 4000
    rag_graph_budget_tokens: int = 2000
    rag_asset_budget_tokens: int = 800
    rag_integration_budget_tokens: int = 600

    # Scoring Weights
    scoring_semantic_weight: float = 0.35
    scoring_hop_weight: float = 0.25
    scoring_centrality_weight: float = 0.20
    scoring_temporal_weight: float = 0.20

    # MCP Settings
    mcp_transport: Literal["stdio", "sse"] = "stdio"
    mcp_session_timeout: int = 3600

    # Webhook Settings
    webhook_secret: SecretStr | None = None
    webhook_timeout: int = 30

    # Slack Integration
    slack_bot_token: SecretStr | None = None
    slack_signing_secret: SecretStr | None = None

    # GitHub Integration
    github_webhook_secret: SecretStr | None = None
    github_app_id: str | None = None
    github_private_key_path: str | None = None

    # Gmail Integration
    gmail_pubsub_project_id: str | None = None
    gmail_pubsub_subscription: str | None = None
    
    # Notion Integration
    notion_api_key: SecretStr | None = None

    @field_validator("scoring_semantic_weight", "scoring_hop_weight", 
                     "scoring_centrality_weight", "scoring_temporal_weight")
    @classmethod
    def validate_weights(cls, v: float) -> float:
        """Ensure weights are between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("Weight must be between 0 and 1")
        return v

    @property
    def postgres_dsn(self) -> str:
        """Generate PostgreSQL connection string."""
        if self.database_url:
            if self.database_url.startswith("postgres://"):
                return self.database_url.replace("postgres://", "postgresql+asyncpg://", 1)
            if self.database_url.startswith("postgresql://"):
                return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return self.database_url
        if self.postgres_uri:
            if self.postgres_uri.startswith("postgres://"):
                return self.postgres_uri.replace("postgres://", "postgresql+asyncpg://", 1)
            if self.postgres_uri.startswith("postgresql://"):
                return self.postgres_uri.replace("postgresql://", "postgresql+asyncpg://", 1)
            return self.postgres_uri
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password.get_secret_value()}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def postgres_dsn_sync(self) -> str:
        """Generate synchronous PostgreSQL connection string for migrations."""
        if self.database_url:
            if self.database_url.startswith("postgres://"):
                return self.database_url.replace("postgres://", "postgresql+psycopg://", 1)
            if self.database_url.startswith("postgresql://"):
                return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
            return self.database_url
        if self.postgres_uri:
            if self.postgres_uri.startswith("postgres://"):
                return self.postgres_uri.replace("postgres://", "postgresql+psycopg://", 1)
            if self.postgres_uri.startswith("postgresql://"):
                return self.postgres_uri.replace("postgresql://", "postgresql+psycopg://", 1)
            return self.postgres_uri
        return (
            f"postgresql+psycopg://{self.postgres_user}:"
            f"{self.postgres_password.get_secret_value()}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a normalized list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
