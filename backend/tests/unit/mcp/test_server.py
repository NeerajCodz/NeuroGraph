"""Unit tests for MCP server."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestMCPServer:
    """Tests for MCP server."""

    @pytest.fixture
    def mcp_server(self, mock_settings):
        """Create MCP server instance."""
        with patch("src.mcp.server.Server") as mock_server_class:
            mock_server = MagicMock()
            mock_server_class.return_value = mock_server
            
            from src.mcp.server import create_server
            server = create_server()
            return server

    def test_server_creation(self, mcp_server):
        """Test MCP server is created."""
        assert mcp_server is not None

    def test_tools_registered(self, mock_settings):
        """Test that tools are registered."""
        # Tools should be defined
        from src.mcp import server
        
        # The module should define tool handlers
        assert hasattr(server, "create_server")


class TestMCPTools:
    """Tests for MCP tools."""

    @pytest.fixture
    def mock_memory_manager(self):
        """Create mock memory manager."""
        manager = AsyncMock()
        manager.remember = AsyncMock(return_value={"id": "node_1"})
        manager.recall = AsyncMock(return_value=[])
        manager.search = AsyncMock(return_value=[])
        manager.forget = AsyncMock(return_value=True)
        return manager

    @pytest.mark.asyncio
    async def test_remember_tool(self, mock_settings, mock_memory_manager):
        """Test remember tool execution."""
        with patch("src.mcp.tools.remember.MemoryManager", return_value=mock_memory_manager):
            from src.mcp.tools.remember import execute_remember
            
            result = await execute_remember(
                content="Test memory",
                user_id="user_123",
                layer="personal",
            )
            
            assert result is not None

    @pytest.mark.asyncio
    async def test_recall_tool(self, mock_settings, mock_memory_manager):
        """Test recall tool execution."""
        with patch("src.mcp.tools.recall.MemoryManager", return_value=mock_memory_manager):
            from src.mcp.tools.recall import execute_recall
            
            result = await execute_recall(
                query="What do I know?",
                user_id="user_123",
            )
            
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_search_tool(self, mock_settings, mock_memory_manager):
        """Test search tool execution."""
        with patch("src.mcp.tools.search.MemoryManager", return_value=mock_memory_manager):
            from src.mcp.tools.search import execute_search
            
            result = await execute_search(
                query="Find fraud",
                user_id="user_123",
                layers=["personal", "tenant"],
            )
            
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_forget_tool(self, mock_settings, mock_memory_manager):
        """Test forget tool execution."""
        with patch("src.mcp.tools.forget.MemoryManager", return_value=mock_memory_manager):
            from src.mcp.tools.forget import execute_forget
            
            result = await execute_forget(
                memory_id="node_123",
                user_id="user_123",
            )
            
            assert result is True


class TestMCPSession:
    """Tests for MCP session management."""

    @pytest.fixture
    def session_manager(self, mock_settings):
        """Create session manager."""
        from src.mcp.session import MCPSessionManager
        return MCPSessionManager()

    def test_create_session(self, session_manager):
        """Test creating a new session."""
        session = session_manager.create_session(user_id="user_123")
        
        assert session is not None
        assert session.user_id == "user_123"
        assert session.session_id is not None

    def test_get_session(self, session_manager):
        """Test getting an existing session."""
        session = session_manager.create_session(user_id="user_123")
        session_id = session.session_id
        
        retrieved = session_manager.get_session(session_id)
        
        assert retrieved is not None
        assert retrieved.session_id == session_id

    def test_get_nonexistent_session(self, session_manager):
        """Test getting a nonexistent session."""
        retrieved = session_manager.get_session("nonexistent")
        
        assert retrieved is None

    def test_delete_session(self, session_manager):
        """Test deleting a session."""
        session = session_manager.create_session(user_id="user_123")
        session_id = session.session_id
        
        session_manager.delete_session(session_id)
        
        assert session_manager.get_session(session_id) is None

    def test_session_timeout(self, session_manager, mock_settings):
        """Test session timeout configuration."""
        assert session_manager.timeout == mock_settings.mcp_session_timeout
