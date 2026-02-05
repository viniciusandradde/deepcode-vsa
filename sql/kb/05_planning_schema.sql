-- =============================================================================
-- Planning Schema for NotebookLM-like functionality
-- Supports project planning with documents, stages, and budget management
-- =============================================================================
-- Projetos de Planejamento
CREATE TABLE IF NOT EXISTS planning_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'draft',
    -- draft, active, completed, archived
    empresa TEXT,
    -- multi-tenancy (same as kb_docs)
    client_id UUID,
    -- multi-tenancy (same as kb_docs)
    embedding_model TEXT DEFAULT 'openai',
    -- embedding model for RAG (openai, cohere, etc)
    linear_project_id TEXT,
    -- Linear.app project ID if synced
    linear_project_url TEXT,
    -- Linear.app project URL
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
-- Etapas/Fases do Projeto
CREATE TABLE IF NOT EXISTS planning_stages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES planning_projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    order_index INTEGER NOT NULL DEFAULT 0,
    status TEXT DEFAULT 'pending',
    -- pending, in_progress, completed
    estimated_days INTEGER,
    start_date DATE,
    end_date DATE,
    linear_milestone_id TEXT,
    -- Linear.app milestone ID if synced
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
-- Documentos de Suporte (fonte de conhecimento para análise)
CREATE TABLE IF NOT EXISTS planning_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES planning_projects(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_type TEXT,
    -- pdf, md, txt, docx
    content TEXT,
    -- texto extraído para o LLM analisar
    file_size INTEGER,
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);
-- Itens de Orçamento
CREATE TABLE IF NOT EXISTS planning_budget_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES planning_projects(id) ON DELETE CASCADE,
    stage_id UUID REFERENCES planning_stages(id) ON DELETE
    SET NULL,
        category TEXT NOT NULL,
        -- infra, pessoal, licencas, hardware, software, servicos
        description TEXT,
        estimated_cost NUMERIC(15, 2) DEFAULT 0,
        actual_cost NUMERIC(15, 2) DEFAULT 0,
        currency TEXT DEFAULT 'BRL',
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
);
-- =============================================================================
-- Índices para Performance
-- =============================================================================
-- Projetos
CREATE INDEX IF NOT EXISTS idx_planning_projects_empresa ON planning_projects(lower(empresa));
CREATE INDEX IF NOT EXISTS idx_planning_projects_client_id ON planning_projects(client_id);
CREATE INDEX IF NOT EXISTS idx_planning_projects_status ON planning_projects(status);
CREATE INDEX IF NOT EXISTS idx_planning_projects_created ON planning_projects(created_at DESC);
-- Etapas
CREATE INDEX IF NOT EXISTS idx_planning_stages_project ON planning_stages(project_id);
CREATE INDEX IF NOT EXISTS idx_planning_stages_order ON planning_stages(project_id, order_index);
-- Documentos
CREATE INDEX IF NOT EXISTS idx_planning_docs_project ON planning_documents(project_id);
-- Orçamento
CREATE INDEX IF NOT EXISTS idx_planning_budget_project ON planning_budget_items(project_id);
CREATE INDEX IF NOT EXISTS idx_planning_budget_stage ON planning_budget_items(stage_id);
CREATE INDEX IF NOT EXISTS idx_planning_budget_category ON planning_budget_items(category);
-- =============================================================================
-- Trigger para updated_at automático
-- =============================================================================
CREATE OR REPLACE FUNCTION update_planning_updated_at() RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = NOW();
RETURN NEW;
END;
$$ LANGUAGE plpgsql;
-- Triggers
DROP TRIGGER IF EXISTS trg_planning_projects_updated ON planning_projects;
CREATE TRIGGER trg_planning_projects_updated BEFORE
UPDATE ON planning_projects FOR EACH ROW EXECUTE FUNCTION update_planning_updated_at();
DROP TRIGGER IF EXISTS trg_planning_stages_updated ON planning_stages;
CREATE TRIGGER trg_planning_stages_updated BEFORE
UPDATE ON planning_stages FOR EACH ROW EXECUTE FUNCTION update_planning_updated_at();
DROP TRIGGER IF EXISTS trg_planning_budget_updated ON planning_budget_items;
CREATE TRIGGER trg_planning_budget_updated BEFORE
UPDATE ON planning_budget_items FOR EACH ROW EXECUTE FUNCTION update_planning_updated_at();
-- =============================================================================
-- Funções Auxiliares
-- =============================================================================
-- Função para obter resumo do projeto com totais
CREATE OR REPLACE FUNCTION get_planning_project_summary(p_project_id UUID) RETURNS TABLE (
        project_id UUID,
        title TEXT,
        status TEXT,
        total_stages INTEGER,
        completed_stages INTEGER,
        total_documents INTEGER,
        total_budget_estimated NUMERIC,
        total_budget_actual NUMERIC
    ) AS $$ BEGIN RETURN QUERY
SELECT p.id AS project_id,
    p.title,
    p.status,
    (
        SELECT COUNT(*)::INTEGER
        FROM planning_stages s
        WHERE s.project_id = p.id
    ) AS total_stages,
    (
        SELECT COUNT(*)::INTEGER
        FROM planning_stages s
        WHERE s.project_id = p.id
            AND s.status = 'completed'
    ) AS completed_stages,
    (
        SELECT COUNT(*)::INTEGER
        FROM planning_documents d
        WHERE d.project_id = p.id
    ) AS total_documents,
    (
        SELECT COALESCE(SUM(b.estimated_cost), 0)
        FROM planning_budget_items b
        WHERE b.project_id = p.id
    ) AS total_budget_estimated,
    (
        SELECT COALESCE(SUM(b.actual_cost), 0)
        FROM planning_budget_items b
        WHERE b.project_id = p.id
    ) AS total_budget_actual
FROM planning_projects p
WHERE p.id = p_project_id;
END;
$$ LANGUAGE plpgsql;
-- Função para obter todo o contexto de documentos de um projeto (para análise LLM)
CREATE OR REPLACE FUNCTION get_planning_documents_context(p_project_id UUID) RETURNS TEXT AS $$
DECLARE result TEXT := '';
doc RECORD;
BEGIN FOR doc IN
SELECT file_name,
    content
FROM planning_documents
WHERE project_id = p_project_id
ORDER BY uploaded_at LOOP result := result || E'\n\n--- ' || doc.file_name || E' ---\n' || COALESCE(doc.content, '');
END LOOP;
RETURN result;
END;
$$ LANGUAGE plpgsql;