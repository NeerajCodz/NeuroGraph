-- Canvas migration: Add canvas columns to embeddings and create canvas_edges table
-- Run this on existing databases to enable memory canvas feature

-- Add canvas columns to embeddings table if they don't exist
ALTER TABLE memory.embeddings ADD COLUMN IF NOT EXISTS is_locked BOOLEAN DEFAULT FALSE;
ALTER TABLE memory.embeddings ADD COLUMN IF NOT EXISTS canvas_x DOUBLE PRECISION;
ALTER TABLE memory.embeddings ADD COLUMN IF NOT EXISTS canvas_y DOUBLE PRECISION;

-- Create index for locked memories
CREATE INDEX IF NOT EXISTS idx_embeddings_locked ON memory.embeddings(is_locked);

-- Create canvas_edges table for memory-to-memory visual links
CREATE TABLE IF NOT EXISTS memory.canvas_edges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_memory_id UUID NOT NULL REFERENCES memory.embeddings(id) ON DELETE CASCADE,
    target_memory_id UUID NOT NULL REFERENCES memory.embeddings(id) ON DELETE CASCADE,
    layer memory.layer NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES auth.tenants(id) ON DELETE CASCADE,
    reason TEXT,
    confidence FLOAT DEFAULT 0.8,
    weight FLOAT DEFAULT 1.0,
    connection_count INTEGER DEFAULT 1,
    metadata JSONB DEFAULT '{}',
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT chk_canvas_edges_scope CHECK (
        (layer = 'personal' AND user_id IS NOT NULL AND tenant_id IS NULL)
        OR (layer = 'tenant' AND tenant_id IS NOT NULL)
        OR (layer = 'global' AND user_id IS NULL AND tenant_id IS NULL)
    ),
    CONSTRAINT chk_canvas_edges_not_self CHECK (source_memory_id <> target_memory_id),
    CONSTRAINT uq_canvas_edges_scope UNIQUE (source_memory_id, target_memory_id, layer, user_id, tenant_id)
);

-- Create indexes for canvas_edges
CREATE INDEX IF NOT EXISTS idx_canvas_edges_source ON memory.canvas_edges(source_memory_id);
CREATE INDEX IF NOT EXISTS idx_canvas_edges_target ON memory.canvas_edges(target_memory_id);
CREATE INDEX IF NOT EXISTS idx_canvas_edges_layer_user ON memory.canvas_edges(layer, user_id);
CREATE INDEX IF NOT EXISTS idx_canvas_edges_layer_tenant ON memory.canvas_edges(layer, tenant_id);
CREATE INDEX IF NOT EXISTS idx_canvas_edges_updated ON memory.canvas_edges(updated_at DESC);

-- Create update trigger for canvas_edges
CREATE OR REPLACE FUNCTION memory.update_canvas_edges_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_canvas_edges_updated_at ON memory.canvas_edges;
CREATE TRIGGER update_canvas_edges_updated_at BEFORE UPDATE ON memory.canvas_edges
    FOR EACH ROW EXECUTE FUNCTION memory.update_canvas_edges_updated_at();

SELECT 'Canvas migration complete' AS status;
