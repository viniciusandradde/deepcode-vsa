-- =============================================================================
-- RAG Planning: multi-tenancy por project_id em kb_chunks
-- Aplicar após 05_planning_schema.sql (planning_projects deve existir)
-- =============================================================================

-- 1. Coluna project_id na tabela de vetores
ALTER TABLE kb_chunks
ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES planning_projects(id) ON DELETE CASCADE;

-- 2. Índice para busca rápida dentro de um projeto (isolamento de contexto)
CREATE INDEX IF NOT EXISTS idx_kb_chunks_project_id ON kb_chunks(project_id);

-- 3. Índice para busca híbrida (Full Text Search) restrita ao projeto
CREATE INDEX IF NOT EXISTS idx_kb_chunks_fts_project
ON kb_chunks USING gin(to_tsvector('portuguese', content))
WHERE project_id IS NOT NULL;

-- =============================================================================
-- Funções de busca com filtro opcional por project_id
-- =============================================================================

-- Busca Vetorial (com p_project_id)
CREATE OR REPLACE FUNCTION public.kb_vector_search(
        query_vec TEXT,
        k INTEGER,
        threshold FLOAT DEFAULT NULL,
        p_client_id UUID DEFAULT NULL,
        p_empresa TEXT DEFAULT NULL,
        p_chunking TEXT DEFAULT NULL,
        p_project_id UUID DEFAULT NULL
    ) RETURNS TABLE (
        doc_path TEXT,
        chunk_ix INTEGER,
        content TEXT,
        score FLOAT,
        meta JSONB
    ) AS $$ BEGIN RETURN QUERY
SELECT c.doc_path,
    c.chunk_ix,
    c.content,
    1 - (c.embedding <=> query_vec::vector) AS score,
    c.meta
FROM public.kb_chunks c
WHERE (
        p_client_id IS NULL
        OR c.client_id = p_client_id
    )
    AND (
        p_empresa IS NULL
        OR lower(c.empresa) = lower(p_empresa)
    )
    AND (
        p_chunking IS NULL
        OR c.meta->>'chunking' = p_chunking
    )
    AND (p_project_id IS NULL OR c.project_id = p_project_id)
    AND (
        threshold IS NULL
        OR 1 - (c.embedding <=> query_vec::vector) >= threshold
    )
ORDER BY c.embedding <=> query_vec::vector
LIMIT k;
END;
$$ LANGUAGE plpgsql;

-- Busca Full-Text (com p_project_id)
CREATE OR REPLACE FUNCTION public.kb_text_search(
        query_text TEXT,
        k INTEGER,
        p_client_id UUID DEFAULT NULL,
        p_empresa TEXT DEFAULT NULL,
        p_chunking TEXT DEFAULT NULL,
        p_project_id UUID DEFAULT NULL
    ) RETURNS TABLE (
        doc_path TEXT,
        chunk_ix INTEGER,
        content TEXT,
        score FLOAT,
        meta JSONB
    ) AS $$ BEGIN RETURN QUERY
SELECT c.doc_path,
    c.chunk_ix,
    c.content,
    similarity(c.content, query_text) AS score,
    c.meta
FROM public.kb_chunks c
WHERE (
        p_client_id IS NULL
        OR c.client_id = p_client_id
    )
    AND (
        p_empresa IS NULL
        OR lower(c.empresa) = lower(p_empresa)
    )
    AND (
        p_chunking IS NULL
        OR c.meta->>'chunking' = p_chunking
    )
    AND (p_project_id IS NULL OR c.project_id = p_project_id)
    AND c.content % query_text
ORDER BY similarity(c.content, query_text) DESC
LIMIT k;
END;
$$ LANGUAGE plpgsql;

-- Busca Híbrida RRF (com p_project_id)
CREATE OR REPLACE FUNCTION public.kb_hybrid_search(
        query_text TEXT,
        query_vec TEXT,
        k INTEGER,
        threshold FLOAT DEFAULT NULL,
        p_client_id UUID DEFAULT NULL,
        p_empresa TEXT DEFAULT NULL,
        p_chunking TEXT DEFAULT NULL,
        p_project_id UUID DEFAULT NULL
    ) RETURNS TABLE (
        doc_path TEXT,
        chunk_ix INTEGER,
        content TEXT,
        score FLOAT,
        meta JSONB
    ) AS $$ BEGIN RETURN QUERY WITH vector_results AS (
        SELECT c.doc_path,
            c.chunk_ix,
            c.content,
            c.meta,
            ROW_NUMBER() OVER (
                ORDER BY c.embedding <=> query_vec::vector
            ) AS vec_rank
        FROM public.kb_chunks c
        WHERE (
                p_client_id IS NULL
                OR c.client_id = p_client_id
            )
            AND (
                p_empresa IS NULL
                OR lower(c.empresa) = lower(p_empresa)
            )
            AND (
                p_chunking IS NULL
                OR c.meta->>'chunking' = p_chunking
            )
            AND (p_project_id IS NULL OR c.project_id = p_project_id)
            AND (
                threshold IS NULL
                OR 1 - (c.embedding <=> query_vec::vector) >= threshold
            )
        LIMIT k * 2
    ), text_results AS (
        SELECT c.doc_path,
            c.chunk_ix,
            c.content,
            c.meta,
            ROW_NUMBER() OVER (
                ORDER BY similarity(c.content, query_text) DESC
            ) AS text_rank
        FROM public.kb_chunks c
        WHERE (
                p_client_id IS NULL
                OR c.client_id = p_client_id
            )
            AND (
                p_empresa IS NULL
                OR lower(c.empresa) = lower(p_empresa)
            )
            AND (
                p_chunking IS NULL
                OR c.meta->>'chunking' = p_chunking
            )
            AND (p_project_id IS NULL OR c.project_id = p_project_id)
            AND c.content % query_text
        LIMIT k * 2
    ), combined AS (
        SELECT COALESCE(v.doc_path, t.doc_path) AS doc_path,
            COALESCE(v.chunk_ix, t.chunk_ix) AS chunk_ix,
            COALESCE(v.content, t.content) AS content,
            COALESCE(v.meta, t.meta) AS meta,
            COALESCE(1.0 / (60 + v.vec_rank), 0) + COALESCE(1.0 / (60 + t.text_rank), 0) AS rrf_score
        FROM vector_results v
            FULL OUTER JOIN text_results t ON v.doc_path = t.doc_path
            AND v.chunk_ix = t.chunk_ix
    )
SELECT combined.doc_path,
    combined.chunk_ix,
    combined.content,
    combined.rrf_score AS score,
    combined.meta
FROM combined
ORDER BY rrf_score DESC
LIMIT k;
END;
$$ LANGUAGE plpgsql;
