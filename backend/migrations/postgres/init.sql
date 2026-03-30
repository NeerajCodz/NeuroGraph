-- PostgreSQL initialization script for NeuroGraph
-- This script runs when the container is first created

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS memory;
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS integrations;

-- Memory layer enum
CREATE TYPE memory.layer AS ENUM ('personal', 'tenant', 'global');

-- Users table
CREATE TABLE IF NOT EXISTS auth.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tenants (organizations)
CREATE TABLE IF NOT EXISTS auth.tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User-tenant membership
CREATE TABLE IF NOT EXISTS auth.tenant_members (
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES auth.tenants(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, tenant_id)
);

-- API keys
CREATE TABLE IF NOT EXISTS auth.api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES auth.tenants(id) ON DELETE SET NULL,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    scopes TEXT[] DEFAULT '{}',
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Embeddings table for vector search
CREATE TABLE IF NOT EXISTS memory.embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id VARCHAR(100) NOT NULL,
    layer memory.layer NOT NULL DEFAULT 'personal',
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES auth.tenants(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(768),
    metadata JSONB DEFAULT '{}',
    confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(node_id, layer, user_id, tenant_id)
);

-- Create indexes for vector similarity search
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON memory.embeddings 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create indexes for filtering
CREATE INDEX IF NOT EXISTS idx_embeddings_layer ON memory.embeddings(layer);
CREATE INDEX IF NOT EXISTS idx_embeddings_user ON memory.embeddings(user_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_tenant ON memory.embeddings(tenant_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_node ON memory.embeddings(node_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_created ON memory.embeddings(created_at DESC);

-- Memory facts table
CREATE TABLE IF NOT EXISTS memory.facts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    layer memory.layer NOT NULL DEFAULT 'personal',
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES auth.tenants(id) ON DELETE CASCADE,
    entity1 VARCHAR(255) NOT NULL,
    relation VARCHAR(100) NOT NULL,
    entity2 VARCHAR(255) NOT NULL,
    reason TEXT,
    source VARCHAR(100),
    confidence FLOAT DEFAULT 1.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_facts_layer ON memory.facts(layer);
CREATE INDEX IF NOT EXISTS idx_facts_user ON memory.facts(user_id);
CREATE INDEX IF NOT EXISTS idx_facts_tenant ON memory.facts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_facts_entities ON memory.facts(entity1, entity2);
CREATE INDEX IF NOT EXISTS idx_facts_created ON memory.facts(created_at DESC);

-- Reasoning paths (for explainability)
CREATE TABLE IF NOT EXISTS memory.reasoning_paths (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_id UUID NOT NULL,
    path_json JSONB NOT NULL,
    score FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reasoning_query ON memory.reasoning_paths(query_id);

-- Integration events
CREATE TABLE IF NOT EXISTS integrations.events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source VARCHAR(50) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    tenant_id UUID REFERENCES auth.tenants(id) ON DELETE SET NULL,
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP WITH TIME ZONE,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_source ON integrations.events(source);
CREATE INDEX IF NOT EXISTS idx_events_processed ON integrations.events(processed);
CREATE INDEX IF NOT EXISTS idx_events_created ON integrations.events(created_at DESC);

-- Reminders
CREATE TABLE IF NOT EXISTS memory.reminders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES auth.tenants(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    trigger_at TIMESTAMP WITH TIME ZONE NOT NULL,
    triggered BOOLEAN DEFAULT FALSE,
    triggered_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reminders_trigger ON memory.reminders(trigger_at) WHERE NOT triggered;
CREATE INDEX IF NOT EXISTS idx_reminders_user ON memory.reminders(user_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON auth.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON auth.tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_embeddings_updated_at BEFORE UPDATE ON memory.embeddings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_facts_updated_at BEFORE UPDATE ON memory.facts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
