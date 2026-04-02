-- Chat and Workspace schema for NeuroGraph
-- Workspaces replace tenants for chat context (shareable via link)

-- Create chat schema
CREATE SCHEMA IF NOT EXISTS chat;

-- Workspace status enum
DO $$ BEGIN
    CREATE TYPE chat.workspace_status AS ENUM ('active', 'archived', 'deleted');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Message role enum
DO $$ BEGIN
    CREATE TYPE chat.message_role AS ENUM ('user', 'assistant', 'system');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Processing step status enum
DO $$ BEGIN
    CREATE TYPE chat.step_status AS ENUM ('pending', 'running', 'completed', 'failed', 'skipped');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Workspaces (shareable chat contexts)
CREATE TABLE IF NOT EXISTS chat.workspaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    share_token VARCHAR(64) UNIQUE,  -- For sharing via link
    is_public BOOLEAN DEFAULT FALSE,
    status chat.workspace_status DEFAULT 'active',
    settings JSONB DEFAULT '{}',
    memory_enabled BOOLEAN DEFAULT TRUE,
    default_model VARCHAR(100) DEFAULT 'devstral-2-123b',
    default_provider VARCHAR(50) DEFAULT 'nvidia',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workspace members (for shared workspaces)
CREATE TABLE IF NOT EXISTS chat.workspace_members (
    workspace_id UUID REFERENCES chat.workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member',  -- owner, admin, member, viewer
    can_write BOOLEAN DEFAULT TRUE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (workspace_id, user_id)
);

-- Conversations (chat threads within workspaces)
CREATE TABLE IF NOT EXISTS chat.conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES chat.workspaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    summary TEXT,
    message_count INTEGER DEFAULT 0,
    is_pinned BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    last_message_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Messages in conversations
CREATE TABLE IF NOT EXISTS chat.messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES chat.conversations(id) ON DELETE CASCADE,
    role chat.message_role NOT NULL,
    content TEXT NOT NULL,
    provider VARCHAR(50),
    model VARCHAR(100),
    tokens_used INTEGER,
    confidence FLOAT,
    reasoning_path JSONB,  -- Stores the reasoning steps
    sources JSONB,  -- Stores memory sources used
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Processing steps (for live status display)
CREATE TABLE IF NOT EXISTS chat.processing_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id UUID REFERENCES chat.messages(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL REFERENCES chat.conversations(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    action VARCHAR(100) NOT NULL,  -- e.g., 'analyzing_memory', 'web_search', 'generating_response'
    status chat.step_status DEFAULT 'pending',
    result TEXT,
    reasoning TEXT,
    duration_ms INTEGER,
    metadata JSONB DEFAULT '{}',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User preferences (model selection, etc.)
CREATE TABLE IF NOT EXISTS chat.user_preferences (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    default_provider VARCHAR(50) DEFAULT 'nvidia',
    default_model VARCHAR(100) DEFAULT 'devstral-2-123b',
    default_memory_layer VARCHAR(20) DEFAULT 'personal',
    agents_enabled BOOLEAN DEFAULT TRUE,
    theme VARCHAR(50) DEFAULT 'dark',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_workspaces_owner ON chat.workspaces(owner_id);
CREATE INDEX IF NOT EXISTS idx_workspaces_share_token ON chat.workspaces(share_token) WHERE share_token IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_workspaces_status ON chat.workspaces(status);

CREATE INDEX IF NOT EXISTS idx_workspace_members_user ON chat.workspace_members(user_id);

CREATE INDEX IF NOT EXISTS idx_conversations_workspace ON chat.conversations(workspace_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user ON chat.conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_last_message ON chat.conversations(last_message_at DESC);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON chat.messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON chat.messages(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_processing_steps_message ON chat.processing_steps(message_id);
CREATE INDEX IF NOT EXISTS idx_processing_steps_conversation ON chat.processing_steps(conversation_id);
CREATE INDEX IF NOT EXISTS idx_processing_steps_status ON chat.processing_steps(status);

-- Update triggers
CREATE TRIGGER update_workspaces_updated_at BEFORE UPDATE ON chat.workspaces
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON chat.conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON chat.user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update conversation message count and last_message_at
CREATE OR REPLACE FUNCTION update_conversation_stats()
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
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_conversation_on_message
    AFTER INSERT ON chat.messages
    FOR EACH ROW EXECUTE FUNCTION update_conversation_stats();

-- Generate share token function
CREATE OR REPLACE FUNCTION generate_share_token()
RETURNS TEXT AS $$
BEGIN
    RETURN encode(gen_random_bytes(32), 'hex');
END;
$$ LANGUAGE plpgsql;
