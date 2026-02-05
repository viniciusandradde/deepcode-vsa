-- 09_update_search_functions.sql
-- Atualiza TODAS as funções de busca para suportar project_id de forma consistente via filtro OR/AND
-- 1. Busca Vetorial
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
    AND (
        p_project_id IS NULL
        OR c.project_id = p_project_id
    )
    AND (
        threshold IS NULL
        OR 1 - (c.embedding <=> query_vec::vector) >= threshold
    )
ORDER BY c.embedding <=> query_vec::vector
LIMIT k;
END;
$$ LANGUAGE plpgsql;
-- 2. Busca Full-Text
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
    AND (
        p_project_id IS NULL
        OR c.project_id = p_project_id
    )
    AND c.content % query_text
ORDER BY similarity(c.content, query_text) DESC
LIMIT k;
END;
$$ LANGUAGE plpgsql;
-- 3. Busca Híbrida (RRF - Reciprocal Rank Fusion)
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
            AND (
                p_project_id IS NULL
                OR c.project_id = p_project_id
            )
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
            AND (
                p_project_id IS NULL
                OR c.project_id = p_project_id
            )
            AND c.content % query_text
        LIMIT k * 2
    ), combined AS (
        SELECT COALESCE(v.doc_path, t.doc_path) AS doc_path,
            COALESCE(v.chunk_ix, t.chunk_ix) AS chunk_ix,
            COALESCE(v.content, t.content) AS content,
            COALESCE(v.meta, t.meta) AS meta,
            COALESCE(
                1.0::double precision / (60 + v.vec_rank),
                0.0::double precision
            ) + COALESCE(
                1.0::double precision / (60 + t.text_rank),
                0.0::double precision
            ) AS rrf_score
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
-- 4. Busca Híbrida (Union - Score Máximo)
-- Usada em alguns contextos que preferem score direto em vez de RRF
CREATE OR REPLACE FUNCTION public.kb_hybrid_union(
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
            1 - (c.embedding <=> query_vec::vector) AS score
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
            AND (
                p_project_id IS NULL
                OR c.project_id = p_project_id
            )
            AND (
                threshold IS NULL
                OR 1 - (c.embedding <=> query_vec::vector) >= threshold
            )
        ORDER BY score DESC
        LIMIT k
    ), text_results AS (
        SELECT c.doc_path,
            c.chunk_ix,
            c.content,
            c.meta,
            similarity(c.content, query_text) AS score
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
            AND (
                p_project_id IS NULL
                OR c.project_id = p_project_id
            )
            AND c.content % query_text
        ORDER BY score DESC
        LIMIT k
    )
SELECT DISTINCT ON (doc_path, chunk_ix) doc_path,
    chunk_ix,
    content,
    score,
    meta
FROM (
        SELECT *
        FROM vector_results
        UNION ALL
        SELECT *
        FROM text_results
    ) AS combined
ORDER BY doc_path,
    chunk_ix,
    score DESC
LIMIT k;
END;
$$ LANGUAGE plpgsql;