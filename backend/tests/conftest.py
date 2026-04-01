"""Pytest configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch


# Use session-scoped event loop
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch("src.core.config.get_settings") as mock:
        settings = MagicMock()
        settings.app_env = "development"
        settings.app_debug = True
        settings.neo4j_uri = "bolt://localhost:7687"
        settings.neo4j_username = "neo4j"
        settings.neo4j_password = MagicMock()
        settings.neo4j_password.get_secret_value.return_value = "password"
        settings.neo4j_database = "neo4j"
        settings.neo4j_max_connection_pool_size = 10
        settings.postgres_host = "localhost"
        settings.postgres_port = 5432
        settings.postgres_user = "test"
        settings.postgres_password = MagicMock()
        settings.postgres_password.get_secret_value.return_value = "password"
        settings.postgres_db = "test"
        settings.postgres_min_pool_size = 1
        settings.postgres_max_pool_size = 5
        settings.redis_url = "redis://localhost:6379/0"
        settings.redis_max_connections = 5
        settings.gemini_api_key = MagicMock()
        settings.gemini_api_key.get_secret_value.return_value = "test-key"
        settings.gemini_model_flash = "gemini-2.0-flash"
        settings.gemini_model_pro = "gemini-2.0-pro"
        settings.gemini_model_embedding = "models/gemini-embedding-2-preview"
        settings.groq_api_key = MagicMock()
        settings.groq_api_key.get_secret_value.return_value = "test-key"
        settings.groq_model = "llama-3.3-70b-versatile"
        settings.jwt_secret_key = MagicMock()
        settings.jwt_secret_key.get_secret_value.return_value = "test-secret"
        settings.jwt_algorithm = "HS256"
        settings.jwt_access_token_expire_minutes = 30
        settings.jwt_refresh_token_expire_days = 7
        settings.memory_default_layer = "personal"
        settings.memory_max_results = 20
        settings.memory_min_confidence = 0.5
        settings.memory_decay_rate = 0.05
        settings.memory_max_hop_depth = 3
        settings.rag_embedding_dimension = 768
        settings.rag_similarity_threshold = 0.7
        settings.rag_max_context_tokens = 4000
        settings.rag_graph_budget_tokens = 2000
        settings.rag_asset_budget_tokens = 800
        settings.rag_integration_budget_tokens = 600
        settings.scoring_semantic_weight = 0.35
        settings.scoring_hop_weight = 0.25
        settings.scoring_centrality_weight = 0.20
        settings.scoring_temporal_weight = 0.20
        settings.mcp_transport = "stdio"
        settings.mcp_session_timeout = 3600
        settings.is_development = True
        settings.is_production = False
        settings.log_level = "debug"
        mock.return_value = settings
        yield settings


@pytest.fixture
def test_user_id():
    """Generate a test user ID."""
    return uuid4()


@pytest.fixture
def test_tenant_id():
    """Generate a test tenant ID."""
    return uuid4()


@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver."""
    driver = AsyncMock()
    driver.connect = AsyncMock()
    driver.disconnect = AsyncMock()
    driver.execute_read = AsyncMock(return_value=[])
    driver.execute_write = AsyncMock(return_value=[])
    driver.health_check = AsyncMock(return_value=True)
    return driver


@pytest.fixture
def mock_postgres_driver():
    """Mock PostgreSQL driver."""
    driver = AsyncMock()
    driver.connect = AsyncMock()
    driver.disconnect = AsyncMock()
    driver.fetch = AsyncMock(return_value=[])
    driver.fetchrow = AsyncMock(return_value=None)
    driver.fetchval = AsyncMock(return_value=None)
    driver.execute = AsyncMock(return_value="")
    driver.health_check = AsyncMock(return_value=True)
    return driver


@pytest.fixture
def mock_redis_driver():
    """Mock Redis driver."""
    driver = AsyncMock()
    driver.connect = AsyncMock()
    driver.disconnect = AsyncMock()
    driver.get = AsyncMock(return_value=None)
    driver.set = AsyncMock(return_value=True)
    driver.delete = AsyncMock(return_value=1)
    driver.health_check = AsyncMock(return_value=True)
    return driver


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini client."""
    import numpy as np
    
    client = AsyncMock()
    client.generate = AsyncMock(return_value="Test response")
    client.embed = AsyncMock(return_value=np.random.rand(1, 768))
    client.extract_entities = AsyncMock(return_value={
        "entities": [{"name": "Test", "type": "Concept"}],
        "relationships": [],
    })
    return client


@pytest.fixture
def mock_groq_client():
    """Mock Groq client."""
    client = AsyncMock()
    client.generate = AsyncMock(return_value='{"intent": "read", "confidence": 0.9}')
    client.classify_intent = AsyncMock(return_value={
        "intent": "read",
        "entities": ["test"],
        "confidence": 0.9,
        "parallel_execution": False,
        "sub_tasks": [],
    })
    client.plan_agents = AsyncMock(return_value=[])
    return client


@pytest.fixture
def sample_embedding():
    """Generate a sample embedding vector."""
    import numpy as np
    return np.random.rand(768).astype(np.float32)


@pytest.fixture
def sample_scored_nodes():
    """Generate sample scored nodes for testing."""
    from src.memory.scoring import ScoredNode
    
    return [
        ScoredNode(
            node_id="node_1",
            name="Test Node 1",
            content="Test content 1",
            layer="personal",
            semantic_score=0.9,
            hop_score=1.0,
            centrality_score=0.5,
            temporal_score=0.8,
            confidence=0.95,
            hops=0,
            age_days=2,
            edge_count=5,
        ),
        ScoredNode(
            node_id="node_2",
            name="Test Node 2",
            content="Test content 2",
            layer="personal",
            semantic_score=0.7,
            hop_score=0.5,
            centrality_score=0.3,
            temporal_score=0.6,
            confidence=0.8,
            hops=1,
            age_days=10,
            edge_count=3,
        ),
    ]
