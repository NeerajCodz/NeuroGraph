"""Unit tests for API routes."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.fixture
    def client(self, mock_settings):
        """Create test client."""
        with patch("src.main.Neo4jDriver") as mock_neo4j, \
             patch("src.main.PostgresDriver") as mock_postgres, \
             patch("src.main.RedisDriver") as mock_redis:
            
            mock_neo4j.return_value = AsyncMock()
            mock_postgres.return_value = AsyncMock()
            mock_redis.return_value = AsyncMock()
            
            from src.main import app
            return TestClient(app)

    def test_health_endpoint(self, client):
        """Test /health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_ready_endpoint(self, client):
        """Test /ready endpoint."""
        response = client.get("/ready")
        
        # May be 200 or 503 depending on DB state
        assert response.status_code in [200, 503]


class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    @pytest.fixture
    def client(self, mock_settings):
        """Create test client."""
        with patch("src.main.Neo4jDriver"), \
             patch("src.main.PostgresDriver"), \
             patch("src.main.RedisDriver"):
            from src.main import app
            return TestClient(app)

    def test_login_missing_credentials(self, client):
        """Test login with missing credentials."""
        response = client.post("/api/v1/auth/login", json={})
        
        assert response.status_code in [400, 422]

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        with patch("src.api.routes.auth.authenticate_user", return_value=None):
            response = client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "wrong",
            })
            
            assert response.status_code == 401

    def test_register_new_user(self, client):
        """Test registering a new user."""
        with patch("src.api.routes.auth.create_user") as mock_create:
            mock_create.return_value = {
                "id": "user_123",
                "email": "new@example.com",
            }
            
            response = client.post("/api/v1/auth/register", json={
                "email": "new@example.com",
                "password": "password123",
                "name": "New User",
            })
            
            assert response.status_code in [200, 201]


class TestMemoryEndpoints:
    """Tests for memory API endpoints."""

    @pytest.fixture
    def authenticated_client(self, mock_settings):
        """Create authenticated test client."""
        with patch("src.main.Neo4jDriver"), \
             patch("src.main.PostgresDriver"), \
             patch("src.main.RedisDriver"), \
             patch("src.api.dependencies.auth.get_current_user") as mock_user:
            
            mock_user.return_value = {
                "id": "user_123",
                "email": "test@example.com",
            }
            
            from src.main import app
            client = TestClient(app)
            client.headers["Authorization"] = "Bearer test_token"
            return client

    def test_create_memory(self, authenticated_client):
        """Test creating a memory."""
        with patch("src.api.routes.memory.MemoryManager") as mock_manager:
            mock_instance = AsyncMock()
            mock_instance.remember = AsyncMock(return_value={"id": "mem_1"})
            mock_manager.return_value = mock_instance
            
            response = authenticated_client.post("/api/v1/memory", json={
                "content": "Test memory content",
                "layer": "personal",
            })
            
            assert response.status_code in [200, 201]

    def test_search_memories(self, authenticated_client):
        """Test searching memories."""
        with patch("src.api.routes.memory.MemoryManager") as mock_manager:
            mock_instance = AsyncMock()
            mock_instance.search = AsyncMock(return_value=[])
            mock_manager.return_value = mock_instance
            
            response = authenticated_client.get("/api/v1/memory/search?q=test")
            
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    def test_delete_memory(self, authenticated_client):
        """Test deleting a memory."""
        with patch("src.api.routes.memory.MemoryManager") as mock_manager:
            mock_instance = AsyncMock()
            mock_instance.forget = AsyncMock(return_value=True)
            mock_manager.return_value = mock_instance
            
            response = authenticated_client.delete("/api/v1/memory/mem_123")
            
            assert response.status_code in [200, 204]


class TestChatEndpoints:
    """Tests for chat API endpoints."""

    @pytest.fixture
    def authenticated_client(self, mock_settings):
        """Create authenticated test client."""
        with patch("src.main.Neo4jDriver"), \
             patch("src.main.PostgresDriver"), \
             patch("src.main.RedisDriver"), \
             patch("src.api.dependencies.auth.get_current_user") as mock_user:
            
            mock_user.return_value = {
                "id": "user_123",
                "email": "test@example.com",
            }
            
            from src.main import app
            client = TestClient(app)
            client.headers["Authorization"] = "Bearer test_token"
            return client

    def test_chat_message(self, authenticated_client):
        """Test sending a chat message."""
        with patch("src.api.routes.chat.Orchestrator") as mock_orch, \
             patch("src.api.routes.chat.GeminiClient") as mock_gemini:
            
            mock_orch_instance = AsyncMock()
            mock_orch_instance.orchestrate = AsyncMock(return_value={
                "intent": "read",
                "agents": [],
            })
            mock_orch.return_value = mock_orch_instance
            
            mock_gemini_instance = AsyncMock()
            mock_gemini_instance.generate = AsyncMock(return_value="Response")
            mock_gemini.return_value = mock_gemini_instance
            
            response = authenticated_client.post("/api/v1/chat", json={
                "message": "Hello, what can you do?",
            })
            
            assert response.status_code == 200
