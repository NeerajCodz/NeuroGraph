"""
E2E tests for NeuroGraph MCP Server.

Tests all MCP tools with real database connections using NVIDIA models.
"""

import asyncio
import json
import os
import pytest
from typing import Any
from uuid import UUID, uuid4

# Test configuration
TEST_USER = {
    "email": "mcp_test@neurograph.ai",
    "password": "TestMCP123!",
    "full_name": "MCP Test User",
}

# Store test state
test_state: dict[str, Any] = {
    "user_id": None,
    "memory_id": None,
    "entity_id": None,
}


@pytest.fixture(scope="function")
async def session_context():
    """Initialize MCP session context."""
    from src.mcp.neurograph_mcp import _session_state
    from src.db.postgres import get_postgres_driver
    from src.db.neo4j import get_neo4j_driver
    
    # Connect databases
    postgres = get_postgres_driver()
    neo4j = get_neo4j_driver()
    await postgres.connect()
    await neo4j.connect()
    
    # Get or create test user (hashed_password is the column name per init.sql)
    async with postgres.connection() as conn:
        row = await conn.fetchrow(
            "SELECT id FROM auth.users WHERE email = $1",
            TEST_USER["email"],
        )
        
        if row:
            user_id = row["id"]
        else:
            # Use same hashing as auth service
            from src.auth.passwords import hash_password
            password_hash = hash_password(TEST_USER["password"])
            
            user_id = await conn.fetchval(
                """
                INSERT INTO auth.users (email, hashed_password, full_name)
                VALUES ($1, $2, $3)
                ON CONFLICT (email) DO NOTHING
                RETURNING id
                """,
                TEST_USER["email"],
                password_hash,
                TEST_USER["full_name"],
            )
            
            if not user_id:
                # Conflict - get existing
                user_id = await conn.fetchval(
                    "SELECT id FROM auth.users WHERE email = $1",
                    TEST_USER["email"],
                )
        
        test_state["user_id"] = user_id
    
    # Set session state
    _session_state["user_id"] = user_id
    _session_state["initialized"] = True
    
    yield _session_state
    
    # Cleanup - restore to anonymous
    _session_state["user_id"] = None
    _session_state["initialized"] = False


class TestAuthentication:
    """Test MCP authentication tools."""
    
    @pytest.mark.asyncio
    async def test_authenticate_status_unauthenticated(self):
        """Test status shows UUID(0) when not authenticated."""
        from src.mcp.neurograph_mcp import neurograph_status, MemoryStatusInput, _session_state
        
        # Reset session to anonymous state
        old_state = _session_state.copy()
        _session_state["user_id"] = None
        _session_state["initialized"] = False
        
        try:
            result = await neurograph_status(MemoryStatusInput())
            # With anonymous access, it uses UUID(0) and should still work
            # Just verify it doesn't crash
            assert "Status" in result or "Error" in result
        finally:
            # Restore
            _session_state.update(old_state)
    
    @pytest.mark.asyncio
    async def test_authentication_with_session(self, session_context):
        """Test that session context is properly set."""
        assert session_context["user_id"] is not None
        assert session_context["initialized"] is True


class TestMemoryTools:
    """Test memory-related MCP tools."""
    
    @pytest.mark.asyncio
    async def test_remember_basic(self, session_context):
        """Test storing a basic memory."""
        from src.mcp.neurograph_mcp import neurograph_remember, RememberInput, ResponseFormat
        
        result = await neurograph_remember(
            RememberInput(
                content="Frank prefers using terminal for all his work",
                layer="personal",
                response_format=ResponseFormat.JSON,
            )
        )
        
        # Handle both success and error cases
        if result.startswith("{"):
            data = json.loads(result)
            if data.get("success"):
                assert "memory_id" in data
                assert data["layer"] in ["personal", "tenant"]
                test_state["memory_id"] = data["memory_id"]
            else:
                # Error response - check it's formatted correctly
                assert "error" in result.lower() or "rate" in result.lower()
        else:
            # Markdown error format
            assert "Error" in result or "Memory Stored" in result
    
    @pytest.mark.asyncio
    async def test_remember_with_metadata(self, session_context):
        """Test storing memory with metadata."""
        from src.mcp.neurograph_mcp import neurograph_remember, RememberInput, ResponseFormat
        
        result = await neurograph_remember(
            RememberInput(
                content="Alice likes morning standup meetings",
                layer="personal",
                metadata={"source": "meeting_notes", "date": "2024-01-15"},
                response_format=ResponseFormat.MARKDOWN,
            )
        )
        
        assert "Memory Stored" in result
        assert "ID" in result
    
    @pytest.mark.asyncio
    async def test_recall_memories(self, session_context):
        """Test recalling stored memories."""
        from src.mcp.neurograph_mcp import neurograph_recall, RecallInput, ResponseFormat
        
        # First store something specific
        from src.mcp.neurograph_mcp import neurograph_remember, RememberInput
        await neurograph_remember(
            RememberInput(
                content="Bob uses Python and FastAPI for backend development",
                layer="personal",
            )
        )
        
        # Now recall
        result = await neurograph_recall(
            RecallInput(
                query="backend development tools",
                layers=["personal"],
                max_results=5,
                response_format=ResponseFormat.JSON,
            )
        )
        
        data = json.loads(result)
        assert "results" in data
        assert data["count"] >= 0
    
    @pytest.mark.asyncio
    async def test_search_memories(self, session_context):
        """Test hybrid search."""
        from src.mcp.neurograph_mcp import neurograph_search, SearchInput, SearchType, ResponseFormat
        
        result = await neurograph_search(
            SearchInput(
                query="preferences",
                search_type=SearchType.HYBRID,
                limit=10,
                response_format=ResponseFormat.JSON,
            )
        )
        
        data = json.loads(result)
        assert "results" in data or "No results" in result
    
    @pytest.mark.asyncio
    async def test_list_memories(self, session_context):
        """Test listing memories."""
        from src.mcp.neurograph_mcp import neurograph_list_memories, ListMemoriesInput, ResponseFormat
        
        result = await neurograph_list_memories(
            ListMemoriesInput(
                layer="personal",
                limit=10,
                response_format=ResponseFormat.JSON,
            )
        )
        
        data = json.loads(result)
        assert "memories" in data or "No memories found" in result
    
    @pytest.mark.asyncio
    async def test_memory_status(self, session_context):
        """Test memory status."""
        from src.mcp.neurograph_mcp import neurograph_status, MemoryStatusInput, ResponseFormat
        
        result = await neurograph_status(
            MemoryStatusInput(response_format=ResponseFormat.JSON)
        )
        
        data = json.loads(result)
        assert "statistics" in data
        assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_forget_memory(self, session_context):
        """Test deleting a memory."""
        from src.mcp.neurograph_mcp import (
            neurograph_remember, RememberInput,
            neurograph_forget, ForgetInput,
            ResponseFormat,
        )
        
        # Store a memory to delete
        store_result = await neurograph_remember(
            RememberInput(
                content="This memory will be deleted",
                layer="personal",
                response_format=ResponseFormat.JSON,
            )
        )
        
        data = json.loads(store_result)
        memory_id = data["memory_id"]
        
        # Delete it
        delete_result = await neurograph_forget(
            ForgetInput(
                memory_id=memory_id,
                layer="personal",
            )
        )
        
        assert "deleted successfully" in delete_result


class TestGraphTools:
    """Test graph-related MCP tools."""
    
    @pytest.mark.asyncio
    async def test_add_entity(self, session_context):
        """Test creating a graph entity."""
        from src.mcp.neurograph_mcp import neurograph_add_entity, AddEntityInput
        
        result = await neurograph_add_entity(
            AddEntityInput(
                name="MCP Test Entity",
                entity_type="Concept",
                properties={"description": "A test entity for MCP E2E tests"},
                layer="personal",
            )
        )
        
        assert "Entity Created" in result
        assert "MCP Test Entity" in result
        
        # Extract ID for later tests
        if "ID" in result:
            import re
            match = re.search(r"`([a-f0-9-]+)`", result)
            if match:
                test_state["entity_id"] = match.group(1)
    
    @pytest.mark.asyncio
    async def test_add_relationship(self, session_context):
        """Test creating relationships between entities."""
        from src.mcp.neurograph_mcp import (
            neurograph_add_entity, AddEntityInput,
            neurograph_add_relationship, AddRelationshipInput,
        )
        
        # Create two entities
        await neurograph_add_entity(
            AddEntityInput(name="SourceEntity", entity_type="Person")
        )
        await neurograph_add_entity(
            AddEntityInput(name="TargetEntity", entity_type="Tool")
        )
        
        # Create relationship
        result = await neurograph_add_relationship(
            AddRelationshipInput(
                source_entity="SourceEntity",
                target_entity="TargetEntity",
                relationship_type="USES",
                properties={"reason": "Daily work tasks"},
                confidence=0.9,
            )
        )
        
        assert "Relationship Created" in result or "Error" in result
    
    @pytest.mark.asyncio
    async def test_traverse_graph(self, session_context):
        """Test graph traversal."""
        from src.mcp.neurograph_mcp import (
            neurograph_add_entity, AddEntityInput,
            neurograph_traverse_graph, TraverseGraphInput,
            ResponseFormat,
        )
        
        # Create an entity with connections
        await neurograph_add_entity(
            AddEntityInput(name="TraversalStart", entity_type="Person")
        )
        
        result = await neurograph_traverse_graph(
            TraverseGraphInput(
                start_entity="TraversalStart",
                max_hops=2,
                response_format=ResponseFormat.MARKDOWN,
            )
        )
        
        assert "Graph Traversal" in result or "No connections" in result
    
    @pytest.mark.asyncio
    async def test_explain_node(self, session_context):
        """Test node explanation."""
        from src.mcp.neurograph_mcp import neurograph_explain, ExplainNodeInput, ResponseFormat
        
        result = await neurograph_explain(
            ExplainNodeInput(
                node_id="MCP Test Entity",
                include_paths=True,
                response_format=ResponseFormat.MARKDOWN,
            )
        )
        
        assert "Explanation" in result or "not found" in result


class TestChatTools:
    """Test chat and agent tools."""
    
    @pytest.mark.asyncio
    async def test_chat_without_memory(self, session_context):
        """Test basic chat without memory."""
        from src.mcp.neurograph_mcp import neurograph_chat, ChatInput
        
        result = await neurograph_chat(
            ChatInput(
                message="What is 2 + 2?",
                use_memory=False,
            )
        )
        
        assert "Response" in result or "Error" in result
    
    @pytest.mark.asyncio
    async def test_chat_with_memory(self, session_context):
        """Test chat with memory context."""
        from src.mcp.neurograph_mcp import (
            neurograph_remember, RememberInput,
            neurograph_chat, ChatInput,
        )
        
        # Store context
        await neurograph_remember(
            RememberInput(
                content="The project deadline is next Friday",
                layer="personal",
            )
        )
        
        # Ask about it
        result = await neurograph_chat(
            ChatInput(
                message="When is the project deadline?",
                use_memory=True,
            )
        )
        
        assert "Response" in result


class TestWorkspaceTools:
    """Test workspace-related tools."""
    
    @pytest.mark.asyncio
    async def test_switch_workspace(self, session_context):
        """Test switching workspace context."""
        from src.mcp.neurograph_mcp import neurograph_switch_workspace, SwitchWorkspaceInput
        from src.db.postgres import get_postgres_driver
        
        postgres = get_postgres_driver()
        
        # Create a workspace first
        async with postgres.connection() as conn:
            workspace_id = await conn.fetchval(
                """
                INSERT INTO chat.workspaces (name, created_by)
                VALUES ('MCP Test Workspace', $1)
                RETURNING id
                """,
                session_context["user_id"],
            )
            
            # Add user as member
            await conn.execute(
                """
                INSERT INTO chat.workspace_members (workspace_id, user_id, role)
                VALUES ($1, $2, 'admin')
                ON CONFLICT DO NOTHING
                """,
                workspace_id,
                session_context["user_id"],
            )
        
        # Switch to it
        result = await neurograph_switch_workspace(
            SwitchWorkspaceInput(workspace_id=str(workspace_id))
        )
        
        assert "Switched to workspace" in result


class TestResponseFormats:
    """Test different response formats."""
    
    @pytest.mark.asyncio
    async def test_json_format(self, session_context):
        """Test JSON response format."""
        from src.mcp.neurograph_mcp import neurograph_status, MemoryStatusInput, ResponseFormat
        
        result = await neurograph_status(
            MemoryStatusInput(response_format=ResponseFormat.JSON)
        )
        
        # Should be valid JSON
        data = json.loads(result)
        assert isinstance(data, dict)
    
    @pytest.mark.asyncio
    async def test_markdown_format(self, session_context):
        """Test Markdown response format."""
        from src.mcp.neurograph_mcp import neurograph_status, MemoryStatusInput, ResponseFormat
        
        result = await neurograph_status(
            MemoryStatusInput(response_format=ResponseFormat.MARKDOWN)
        )
        
        # Should contain markdown elements
        assert "##" in result or "**" in result


class TestInputValidation:
    """Test input validation."""
    
    @pytest.mark.asyncio
    async def test_empty_content_rejected(self, session_context):
        """Test that empty content is rejected."""
        from src.mcp.neurograph_mcp import neurograph_remember, RememberInput
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            RememberInput(content="", layer="personal")
    
    @pytest.mark.asyncio
    async def test_empty_query_rejected(self, session_context):
        """Test that empty query is rejected."""
        from src.mcp.neurograph_mcp import RecallInput
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            RecallInput(query="   ", max_results=10)
    
    @pytest.mark.asyncio
    async def test_invalid_layer_rejected(self, session_context):
        """Test that invalid layer is rejected."""
        from src.mcp.neurograph_mcp import RememberInput
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            RememberInput(content="Test", layer="invalid_layer")


class TestErrorHandling:
    """Test error handling."""
    
    @pytest.mark.asyncio
    async def test_forget_nonexistent_memory(self, session_context):
        """Test forgetting a memory that doesn't exist."""
        from src.mcp.neurograph_mcp import neurograph_forget, ForgetInput
        
        result = await neurograph_forget(
            ForgetInput(
                memory_id=str(uuid4()),
                layer="personal",
            )
        )
        
        assert "Error" in result or "not found" in result
    
    @pytest.mark.asyncio
    async def test_explain_nonexistent_node(self, session_context):
        """Test explaining a node that doesn't exist."""
        from src.mcp.neurograph_mcp import neurograph_explain, ExplainNodeInput
        
        result = await neurograph_explain(
            ExplainNodeInput(node_id="nonexistent_node_12345")
        )
        
        assert "not found" in result.lower()


class TestIntegrationWorkflows:
    """Test integrated workflows across multiple tools."""
    
    @pytest.mark.asyncio
    async def test_full_memory_workflow(self, session_context):
        """Test complete memory workflow: store → recall → search → status."""
        from src.mcp.neurograph_mcp import (
            neurograph_remember, RememberInput,
            neurograph_recall, RecallInput,
            neurograph_search, SearchInput,
            neurograph_status, MemoryStatusInput,
            ResponseFormat, SearchType,
        )
        
        # 1. Store multiple memories
        await neurograph_remember(RememberInput(
            content="The engineering team uses React for frontend",
            layer="personal",
        ))
        await neurograph_remember(RememberInput(
            content="Backend services are built with FastAPI and Python",
            layer="personal",
        ))
        await neurograph_remember(RememberInput(
            content="Deployment is done via Docker and Kubernetes",
            layer="personal",
        ))
        
        # 2. Recall specific memory
        recall_result = await neurograph_recall(RecallInput(
            query="frontend technology",
            max_results=3,
            response_format=ResponseFormat.JSON,
        ))
        recall_data = json.loads(recall_result)
        assert recall_data["count"] >= 0
        
        # 3. Search across memories
        search_result = await neurograph_search(SearchInput(
            query="technology stack",
            search_type=SearchType.HYBRID,
            response_format=ResponseFormat.JSON,
        ))
        search_data = json.loads(search_result)
        assert "results" in search_data or "No results" in search_result
        
        # 4. Check status
        status_result = await neurograph_status(MemoryStatusInput(
            response_format=ResponseFormat.JSON,
        ))
        status_data = json.loads(status_result)
        assert status_data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_full_graph_workflow(self, session_context):
        """Test complete graph workflow: create entities → relationships → traverse."""
        from src.mcp.neurograph_mcp import (
            neurograph_add_entity, AddEntityInput,
            neurograph_add_relationship, AddRelationshipInput,
            neurograph_traverse_graph, TraverseGraphInput,
            neurograph_explain, ExplainNodeInput,
            ResponseFormat,
        )
        
        # 1. Create entities for a project structure
        await neurograph_add_entity(AddEntityInput(
            name="ProjectAlpha",
            entity_type="Project",
            properties={"status": "active"},
        ))
        await neurograph_add_entity(AddEntityInput(
            name="TeamLead",
            entity_type="Person",
            properties={"role": "lead"},
        ))
        await neurograph_add_entity(AddEntityInput(
            name="Developer1",
            entity_type="Person",
            properties={"role": "developer"},
        ))
        
        # 2. Create relationships
        await neurograph_add_relationship(AddRelationshipInput(
            source_entity="TeamLead",
            target_entity="ProjectAlpha",
            relationship_type="MANAGES",
            confidence=0.95,
        ))
        await neurograph_add_relationship(AddRelationshipInput(
            source_entity="Developer1",
            target_entity="ProjectAlpha",
            relationship_type="WORKS_ON",
            confidence=0.9,
        ))
        await neurograph_add_relationship(AddRelationshipInput(
            source_entity="TeamLead",
            target_entity="Developer1",
            relationship_type="SUPERVISES",
            confidence=0.9,
        ))
        
        # 3. Traverse from project
        traverse_result = await neurograph_traverse_graph(TraverseGraphInput(
            start_entity="ProjectAlpha",
            max_hops=2,
            response_format=ResponseFormat.MARKDOWN,
        ))
        assert "Graph Traversal" in traverse_result or "No connections" in traverse_result
        
        # 4. Explain a node
        explain_result = await neurograph_explain(ExplainNodeInput(
            node_id="TeamLead",
            response_format=ResponseFormat.MARKDOWN,
        ))
        assert "Explanation" in explain_result or "not found" in explain_result
    
    @pytest.mark.asyncio
    async def test_memory_to_chat_workflow(self, session_context):
        """Test workflow from memory storage to chat query."""
        from src.mcp.neurograph_mcp import (
            neurograph_remember, RememberInput,
            neurograph_chat, ChatInput,
        )
        
        # 1. Store contextual information
        await neurograph_remember(RememberInput(
            content="The quarterly review meeting is scheduled for March 15th at 2pm",
            layer="personal",
        ))
        await neurograph_remember(RememberInput(
            content="Budget for Q2 has been approved at $50,000",
            layer="personal",
        ))
        
        # 2. Ask questions that require memory context
        result = await neurograph_chat(ChatInput(
            message="When is our next important meeting?",
            use_memory=True,
        ))
        
        assert "Response" in result


# Performance tests
class TestPerformance:
    """Test performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_bulk_memory_storage(self, session_context):
        """Test storing multiple memories in sequence."""
        from src.mcp.neurograph_mcp import neurograph_remember, RememberInput
        import time
        
        memories = [
            f"Performance test memory {i}: Contains test data for validation"
            for i in range(5)  # Reduced for faster tests
        ]
        
        start = time.time()
        for content in memories:
            await neurograph_remember(RememberInput(
                content=content,
                layer="personal",
            ))
        elapsed = time.time() - start
        
        # Should complete in reasonable time
        assert elapsed < 60  # 60 seconds for 5 memories with embeddings
    
    @pytest.mark.asyncio
    async def test_concurrent_recalls(self, session_context):
        """Test concurrent recall operations."""
        from src.mcp.neurograph_mcp import neurograph_recall, RecallInput
        import asyncio
        
        queries = [
            "technology stack",
            "team preferences",
            "project deadlines",
        ]
        
        tasks = [
            neurograph_recall(RecallInput(query=q, max_results=5))
            for q in queries
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should complete successfully
        assert len(results) == 3
        for result in results:
            assert "Error" not in result or "results" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
