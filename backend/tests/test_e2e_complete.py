"""
E2E tests for NeuroGraph backend - comprehensive test suite.
Tests all API endpoints with real database connections.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from uuid import UUID

# Import the FastAPI app
from src.main import app

# Test data
TEST_USER = {
    "email": "test_e2e@neurograph.ai",
    "password": "TestPass123!",
    "full_name": "E2E Test User"
}

TEST_USER_2 = {
    "email": "neeraj@ng.ai",
    "password": "Password@123",
}


@pytest.fixture
async def client():
    """Create async HTTP client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
async def auth_token(client: AsyncClient):
    """Get auth token for existing test user."""
    # Try to login with existing user first
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": TEST_USER_2["email"], "password": TEST_USER_2["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    
    if response.status_code == 200:
        return response.json()["access_token"]
    
    # If not exists, register new user
    response = await client.post(
        "/api/v1/auth/register",
        json=TEST_USER,
    )
    
    # Then login
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": TEST_USER["email"], "password": TEST_USER["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Get authorization headers."""
    return {"Authorization": f"Bearer {auth_token}"}


class TestHealth:
    """Test health and readiness endpoints."""
    
    @pytest.mark.asyncio
    async def test_health(self, client: AsyncClient):
        """Test health endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_readiness(self, client: AsyncClient):
        """Test readiness endpoint."""
        response = await client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
        assert "postgres" in data
        assert "neo4j" in data
        assert "redis" in data


class TestAuth:
    """Test authentication endpoints."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """Test successful login."""
        seeded_login = await client.post(
            "/api/v1/auth/login",
            data={"username": TEST_USER_2["email"], "password": TEST_USER_2["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if seeded_login.status_code == 200:
            response = seeded_login
        else:
            register_response = await client.post(
                "/api/v1/auth/register",
                json=TEST_USER,
            )
            if register_response.status_code not in (201, 400):
                assert register_response.status_code == 201
            response = await client.post(
                "/api/v1/auth/login",
                data={"username": TEST_USER["email"], "password": TEST_USER["password"]},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_failure(self, client: AsyncClient):
        """Test failed login."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "wrong@email.com", "password": "wrongpass"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_me_endpoint(self, client: AsyncClient, auth_headers):
        """Test /me endpoint."""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "id" in data


class TestWorkspaces:
    """Test workspace endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_workspace(self, client: AsyncClient, auth_headers):
        """Test workspace creation."""
        response = await client.post(
            "/api/v1/workspaces",
            headers=auth_headers,
            json={"name": "Test Workspace", "description": "E2E test workspace"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Workspace"
        assert "id" in data
        assert "share_token" in data
    
    @pytest.mark.asyncio
    async def test_list_workspaces(self, client: AsyncClient, auth_headers):
        """Test listing workspaces."""
        response = await client.get("/api/v1/workspaces", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_get_workspace(self, client: AsyncClient, auth_headers):
        """Test getting a specific workspace."""
        # Create first
        create_response = await client.post(
            "/api/v1/workspaces",
            headers=auth_headers,
            json={"name": "Get Test Workspace"},
        )
        workspace_id = create_response.json()["id"]
        
        # Then get
        response = await client.get(
            f"/api/v1/workspaces/{workspace_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == workspace_id


class TestConversations:
    """Test conversation endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_conversation(self, client: AsyncClient, auth_headers):
        """Test conversation creation."""
        response = await client.post(
            "/api/v1/conversations",
            headers=auth_headers,
            json={"title": "Test Conversation"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["title"] == "Test Conversation"
    
    @pytest.mark.asyncio
    async def test_list_conversations(self, client: AsyncClient, auth_headers):
        """Test listing conversations."""
        response = await client.get("/api/v1/conversations", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestMemory:
    """Test memory endpoints."""
    
    @pytest.mark.asyncio
    async def test_store_memory(self, client: AsyncClient, auth_headers):
        """Test storing a memory."""
        response = await client.post(
            "/api/v1/memory/remember",
            headers=auth_headers,
            json={"content": "The capital of France is Paris", "layer": "personal"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["content"] == "The capital of France is Paris"
    
    @pytest.mark.asyncio
    async def test_recall_memory(self, client: AsyncClient, auth_headers):
        """Test recalling memories."""
        # Store first
        await client.post(
            "/api/v1/memory/remember",
            headers=auth_headers,
            json={"content": "Python is a programming language", "layer": "personal"},
        )
        
        # Then recall
        response = await client.post(
            "/api/v1/memory/recall",
            headers=auth_headers,
            json={"query": "programming language", "max_results": 10},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_list_memories(self, client: AsyncClient, auth_headers):
        """Test listing memories."""
        response = await client.get(
            "/api/v1/memory/list?layer=personal&limit=20",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_memory_count(self, client: AsyncClient, auth_headers):
        """Test getting memory counts."""
        response = await client.get("/api/v1/memory/count", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "personal" in data
        assert "workspace" in data
        assert "global" in data
        assert "total" in data


class TestChat:
    """Test chat endpoints."""
    
    @pytest.mark.asyncio
    async def test_send_message(self, client: AsyncClient, auth_headers):
        """Test sending a chat message."""
        response = await client.post(
            "/api/v1/chat/message",
            headers=auth_headers,
            json={
                "content": "Hello, how are you?",
                "layer": "personal",
                "agents_enabled": False,  # Disable agents for faster test
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "conversation_id" in data
        assert "content" in data
        assert len(data["content"]) > 0
    
    @pytest.mark.asyncio
    async def test_chat_with_memory(self, client: AsyncClient, auth_headers):
        """Test chat with memory context."""
        # Store memory first
        await client.post(
            "/api/v1/memory/remember",
            headers=auth_headers,
            json={"content": "My favorite color is blue", "layer": "personal"},
        )
        
        # Ask question that should use memory
        response = await client.post(
            "/api/v1/chat/message",
            headers=auth_headers,
            json={
                "content": "What is my favorite color?",
                "layer": "personal",
                "agents_enabled": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "sources" in data


class TestGraph:
    """Test graph endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_entities(self, client: AsyncClient, auth_headers):
        """Test listing entities."""
        response = await client.get("/api/v1/graph/entities", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "entities" in data or isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_visualize_graph(self, client: AsyncClient, auth_headers):
        """Test graph visualization."""
        response = await client.get("/api/v1/graph/visualize", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data


class TestModels:
    """Test model management endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_providers(self, client: AsyncClient, auth_headers):
        """Test listing LLM providers."""
        response = await client.get("/api/v1/models/providers", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert len(data["providers"]) > 0
    
    @pytest.mark.asyncio
    async def test_list_all_models(self, client: AsyncClient, auth_headers):
        """Test listing all models."""
        response = await client.get("/api/v1/models/all", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert data["total"] > 0
    
    @pytest.mark.asyncio
    async def test_get_recommendations(self, client: AsyncClient, auth_headers):
        """Test getting model recommendations."""
        response = await client.get("/api/v1/models/recommendations", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert "chat" in data["recommendations"]
        assert "embeddings" in data["recommendations"]


@pytest.mark.asyncio
async def test_full_workflow(client: AsyncClient, auth_headers):
    """Test a complete workflow: workspace -> conversation -> memory -> chat."""
    
    # 1. Create workspace
    workspace_resp = await client.post(
        "/api/v1/workspaces",
        headers=auth_headers,
        json={"name": "Full Workflow Workspace"},
    )
    assert workspace_resp.status_code == 200
    workspace_id = workspace_resp.json()["id"]
    
    # 2. Create conversation in workspace
    conv_resp = await client.post(
        "/api/v1/conversations",
        headers=auth_headers,
        json={"workspace_id": workspace_id, "title": "Workflow Conversation"},
    )
    assert conv_resp.status_code == 200
    conversation_id = conv_resp.json()["id"]
    
    # 3. Store some memory
    memory_resp = await client.post(
        "/api/v1/memory/remember",
        headers=auth_headers,
        json={"content": "NeuroGraph is an AI knowledge graph system", "layer": "personal"},
    )
    assert memory_resp.status_code == 200
    
    # 4. Send chat message in conversation
    chat_resp = await client.post(
        "/api/v1/chat/message",
        headers=auth_headers,
        json={
            "content": "What is NeuroGraph?",
            "conversation_id": conversation_id,
            "workspace_id": workspace_id,
            "layer": "personal",
            "agents_enabled": True,
        },
    )
    assert chat_resp.status_code == 200
    data = chat_resp.json()
    assert data["conversation_id"] == conversation_id
    assert len(data["content"]) > 0
    
    # 5. Get conversation with messages
    get_conv_resp = await client.get(
        f"/api/v1/conversations/{conversation_id}",
        headers=auth_headers,
    )
    assert get_conv_resp.status_code == 200
    conv_data = get_conv_resp.json()
    assert "messages" in conv_data
    assert len(conv_data["messages"]) >= 2  # User message + assistant response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
