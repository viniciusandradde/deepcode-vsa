-- 08_projects_schema.sql (FIXED)
-- 1. Projetos
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    custom_instructions TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name);
-- 2. Threads (Registro de vínculo Projeto <-> Thread do LangGraph)
CREATE TABLE IF NOT EXISTS threads (
    id TEXT PRIMARY KEY,
    -- thread_id do LangGraph (pode ser UUID string)
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_threads_project_id ON threads(project_id);
-- 3. RAG Documents (kb_docs) - Multi-tenancy
ALTER TABLE kb_docs
ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_kb_docs_project ON kb_docs(project_id);
-- 4. RAG Chunks (kb_chunks) - Multi-tenancy
ALTER TABLE kb_chunks
ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_kb_chunks_project ON kb_chunks(project_id);