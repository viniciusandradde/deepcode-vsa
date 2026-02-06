-- 08_projects_schema.sql
-- DeepCode Projects: standalone project management with thread/RAG integration
--
-- NOTE: kb_chunks.project_id may already exist from 06_rag_planning.sql
-- referencing planning_projects(id). This script adds a SEPARATE column
-- dc_project_id for the DeepCode Projects system to avoid FK conflict.

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

-- 2. Threads (Registro de vinculo Projeto <-> Thread do LangGraph)
CREATE TABLE IF NOT EXISTS threads (
    id TEXT PRIMARY KEY,
    -- thread_id do LangGraph (pode ser UUID string)
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_threads_project_id ON threads(project_id);

-- 3. RAG Documents (kb_docs) - add dc_project_id for DeepCode Projects
ALTER TABLE kb_docs
ADD COLUMN IF NOT EXISTS dc_project_id UUID REFERENCES projects(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_kb_docs_dc_project ON kb_docs(dc_project_id);

-- 4. RAG Chunks (kb_chunks) - add dc_project_id for DeepCode Projects
-- NOTE: kb_chunks.project_id references planning_projects (from 06_rag_planning.sql)
-- We use dc_project_id to avoid FK conflict
ALTER TABLE kb_chunks
ADD COLUMN IF NOT EXISTS dc_project_id UUID REFERENCES projects(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_kb_chunks_dc_project ON kb_chunks(dc_project_id);
