"""Runtime PostgreSQL schema bootstrap for deployment compatibility."""

from __future__ import annotations

import asyncpg

from src.core.logging import get_logger

logger = get_logger(__name__)


BOOTSTRAP_STATEMENTS: tuple[str, ...] = (
    """
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp"
    """,
    """
    CREATE EXTENSION IF NOT EXISTS pgcrypto
    """,
    """
    CREATE SCHEMA IF NOT EXISTS chat
    """,
    """
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql
    """,
    """
    CREATE TABLE IF NOT EXISTS chat.workspaces (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(255) NOT NULL,
        description TEXT,
        owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
        share_token VARCHAR(64),
        is_public BOOLEAN DEFAULT FALSE,
        status VARCHAR(20) DEFAULT 'active',
        settings JSONB DEFAULT '{}',
        memory_enabled BOOLEAN DEFAULT TRUE,
        default_model VARCHAR(100) DEFAULT 'gemini-2.0-flash',
        default_provider VARCHAR(50) DEFAULT 'gemini',
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS chat.workspace_members (
        workspace_id UUID NOT NULL REFERENCES chat.workspaces(id) ON DELETE CASCADE,
        user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
        role VARCHAR(50) DEFAULT 'member',
        can_write BOOLEAN DEFAULT TRUE,
        joined_at TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (workspace_id, user_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS chat.conversations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        workspace_id UUID REFERENCES chat.workspaces(id) ON DELETE CASCADE,
        user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
        title VARCHAR(255),
        summary TEXT,
        message_count INTEGER DEFAULT 0,
        is_pinned BOOLEAN DEFAULT FALSE,
        is_archived BOOLEAN DEFAULT FALSE,
        last_message_at TIMESTAMPTZ,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS chat.messages (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        conversation_id UUID NOT NULL REFERENCES chat.conversations(id) ON DELETE CASCADE,
        role VARCHAR(20) NOT NULL,
        content TEXT NOT NULL,
        provider VARCHAR(50),
        model VARCHAR(100),
        tokens_used INTEGER,
        confidence FLOAT,
        reasoning_path JSONB,
        sources JSONB,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS chat.processing_steps (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        message_id UUID REFERENCES chat.messages(id) ON DELETE CASCADE,
        conversation_id UUID NOT NULL REFERENCES chat.conversations(id) ON DELETE CASCADE,
        step_number INTEGER NOT NULL,
        action VARCHAR(100) NOT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        result TEXT,
        reasoning TEXT,
        duration_ms INTEGER,
        metadata JSONB DEFAULT '{}',
        started_at TIMESTAMPTZ,
        completed_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS chat.user_preferences (
        user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
        default_provider VARCHAR(50) DEFAULT 'gemini',
        default_model VARCHAR(100) DEFAULT 'gemini-2.0-flash',
        default_memory_layer VARCHAR(20) DEFAULT 'personal',
        agents_enabled BOOLEAN DEFAULT TRUE,
        theme VARCHAR(50) DEFAULT 'dark',
        settings JSONB DEFAULT '{}',
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    # Workspaces compatibility columns.
    "ALTER TABLE chat.workspaces ALTER COLUMN id SET DEFAULT gen_random_uuid()",
    "ALTER TABLE chat.workspaces ADD COLUMN IF NOT EXISTS share_token VARCHAR(64)",
    "ALTER TABLE chat.workspaces ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE",
    "ALTER TABLE chat.workspaces ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active'",
    "ALTER TABLE chat.workspaces ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}'",
    "ALTER TABLE chat.workspaces ADD COLUMN IF NOT EXISTS memory_enabled BOOLEAN DEFAULT TRUE",
    "ALTER TABLE chat.workspaces ADD COLUMN IF NOT EXISTS default_model VARCHAR(100) DEFAULT 'gemini-2.0-flash'",
    "ALTER TABLE chat.workspaces ADD COLUMN IF NOT EXISTS default_provider VARCHAR(50) DEFAULT 'gemini'",
    "ALTER TABLE chat.workspaces ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()",
    "ALTER TABLE chat.workspaces ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()",
    # Workspace members compatibility columns.
    "ALTER TABLE chat.workspace_members ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'member'",
    "ALTER TABLE chat.workspace_members ADD COLUMN IF NOT EXISTS can_write BOOLEAN DEFAULT TRUE",
    "ALTER TABLE chat.workspace_members ADD COLUMN IF NOT EXISTS joined_at TIMESTAMPTZ DEFAULT NOW()",
    # Conversations compatibility columns.
    "ALTER TABLE chat.conversations ALTER COLUMN id SET DEFAULT gen_random_uuid()",
    "ALTER TABLE chat.conversations ADD COLUMN IF NOT EXISTS summary TEXT",
    "ALTER TABLE chat.conversations ADD COLUMN IF NOT EXISTS message_count INTEGER DEFAULT 0",
    "ALTER TABLE chat.conversations ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT FALSE",
    "ALTER TABLE chat.conversations ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE",
    "ALTER TABLE chat.conversations ADD COLUMN IF NOT EXISTS last_message_at TIMESTAMPTZ",
    "ALTER TABLE chat.conversations ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'",
    "ALTER TABLE chat.conversations ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()",
    "ALTER TABLE chat.conversations ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()",
    # Messages compatibility columns.
    "ALTER TABLE chat.messages ALTER COLUMN id SET DEFAULT gen_random_uuid()",
    "ALTER TABLE chat.messages ADD COLUMN IF NOT EXISTS provider VARCHAR(50)",
    "ALTER TABLE chat.messages ADD COLUMN IF NOT EXISTS model VARCHAR(100)",
    "ALTER TABLE chat.messages ADD COLUMN IF NOT EXISTS tokens_used INTEGER",
    "ALTER TABLE chat.messages ADD COLUMN IF NOT EXISTS confidence FLOAT",
    "ALTER TABLE chat.messages ADD COLUMN IF NOT EXISTS reasoning_path JSONB",
    "ALTER TABLE chat.messages ADD COLUMN IF NOT EXISTS sources JSONB",
    "ALTER TABLE chat.messages ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'",
    "ALTER TABLE chat.messages ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()",
    # Processing step compatibility columns.
    "ALTER TABLE chat.processing_steps ALTER COLUMN id SET DEFAULT gen_random_uuid()",
    "ALTER TABLE chat.processing_steps ADD COLUMN IF NOT EXISTS message_id UUID REFERENCES chat.messages(id) ON DELETE CASCADE",
    "ALTER TABLE chat.processing_steps ADD COLUMN IF NOT EXISTS conversation_id UUID REFERENCES chat.conversations(id) ON DELETE CASCADE",
    "ALTER TABLE chat.processing_steps ADD COLUMN IF NOT EXISTS step_number INTEGER",
    "ALTER TABLE chat.processing_steps ADD COLUMN IF NOT EXISTS action VARCHAR(100)",
    "ALTER TABLE chat.processing_steps ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending'",
    "ALTER TABLE chat.processing_steps ADD COLUMN IF NOT EXISTS result TEXT",
    "ALTER TABLE chat.processing_steps ADD COLUMN IF NOT EXISTS reasoning TEXT",
    "ALTER TABLE chat.processing_steps ADD COLUMN IF NOT EXISTS duration_ms INTEGER",
    "ALTER TABLE chat.processing_steps ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'",
    "ALTER TABLE chat.processing_steps ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ",
    "ALTER TABLE chat.processing_steps ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ",
    "ALTER TABLE chat.processing_steps ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()",
    # User preferences compatibility columns.
    "ALTER TABLE chat.user_preferences ADD COLUMN IF NOT EXISTS default_provider VARCHAR(50) DEFAULT 'gemini'",
    "ALTER TABLE chat.user_preferences ADD COLUMN IF NOT EXISTS default_model VARCHAR(100) DEFAULT 'gemini-2.0-flash'",
    "ALTER TABLE chat.user_preferences ADD COLUMN IF NOT EXISTS default_memory_layer VARCHAR(20) DEFAULT 'personal'",
    "ALTER TABLE chat.user_preferences ADD COLUMN IF NOT EXISTS agents_enabled BOOLEAN DEFAULT TRUE",
    "ALTER TABLE chat.user_preferences ADD COLUMN IF NOT EXISTS theme VARCHAR(50) DEFAULT 'dark'",
    "ALTER TABLE chat.user_preferences ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}'",
    "ALTER TABLE chat.user_preferences ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()",
    "ALTER TABLE chat.user_preferences ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()",
    # Indexes.
    "CREATE INDEX IF NOT EXISTS idx_workspaces_owner ON chat.workspaces(owner_id)",
    "CREATE INDEX IF NOT EXISTS idx_workspaces_status ON chat.workspaces(status)",
    "CREATE INDEX IF NOT EXISTS idx_workspaces_share_token ON chat.workspaces(share_token) WHERE share_token IS NOT NULL",
    "CREATE INDEX IF NOT EXISTS idx_workspace_members_user ON chat.workspace_members(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_conversations_workspace ON chat.conversations(workspace_id)",
    "CREATE INDEX IF NOT EXISTS idx_conversations_user ON chat.conversations(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_conversations_last_message ON chat.conversations(last_message_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_messages_conversation ON chat.messages(conversation_id)",
    "CREATE INDEX IF NOT EXISTS idx_messages_created ON chat.messages(created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_processing_steps_message ON chat.processing_steps(message_id)",
    "CREATE INDEX IF NOT EXISTS idx_processing_steps_conversation ON chat.processing_steps(conversation_id)",
    "CREATE INDEX IF NOT EXISTS idx_processing_steps_status ON chat.processing_steps(status)",
    # Triggers / trigger funcs.
    "DROP TRIGGER IF EXISTS update_workspaces_updated_at ON chat.workspaces",
    "CREATE TRIGGER update_workspaces_updated_at BEFORE UPDATE ON chat.workspaces FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()",
    "DROP TRIGGER IF EXISTS update_conversations_updated_at ON chat.conversations",
    "CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON chat.conversations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()",
    "DROP TRIGGER IF EXISTS update_user_preferences_updated_at ON chat.user_preferences",
    "CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON chat.user_preferences FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()",
    """
    CREATE OR REPLACE FUNCTION chat.update_conversation_stats()
    RETURNS TRIGGER AS $$
    BEGIN
        UPDATE chat.conversations
        SET
            message_count = (SELECT COUNT(*) FROM chat.messages WHERE conversation_id = NEW.conversation_id),
            last_message_at = NEW.created_at,
            updated_at = NOW()
        WHERE id = NEW.conversation_id;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql
    """,
    "DROP TRIGGER IF EXISTS update_conversation_on_message ON chat.messages",
    "CREATE TRIGGER update_conversation_on_message AFTER INSERT ON chat.messages FOR EACH ROW EXECUTE FUNCTION chat.update_conversation_stats()",
    # Backfill required defaults for old rows.
    "UPDATE chat.workspaces SET status = 'active' WHERE status IS NULL",
    "UPDATE chat.workspaces SET is_public = FALSE WHERE is_public IS NULL",
    "UPDATE chat.workspaces SET memory_enabled = TRUE WHERE memory_enabled IS NULL",
    "UPDATE chat.workspace_members SET can_write = TRUE WHERE can_write IS NULL",
    "UPDATE chat.conversations SET message_count = 0 WHERE message_count IS NULL",
    "UPDATE chat.conversations SET is_pinned = FALSE WHERE is_pinned IS NULL",
    "UPDATE chat.conversations SET is_archived = FALSE WHERE is_archived IS NULL",
    "UPDATE chat.processing_steps SET status = 'pending' WHERE status IS NULL",
    "UPDATE chat.user_preferences SET agents_enabled = TRUE WHERE agents_enabled IS NULL",
)


async def ensure_runtime_schema(conn: asyncpg.Connection) -> None:
    """Ensure required runtime tables/columns exist for deployed environments."""
    for statement in BOOTSTRAP_STATEMENTS:
        await conn.execute(statement)
    logger.info("postgres_runtime_schema_ready")

