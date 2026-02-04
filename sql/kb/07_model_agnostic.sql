-- =============================================================================
-- RAG Model-Agnostic: vetor genérico + índices parciais por dimensão
-- Aplicar após 06_rag_planning.sql
-- =============================================================================

-- 1. Remover índice antigo (vetor dimensionado)
DROP INDEX IF EXISTS idx_kb_chunks_embedding;

-- 2. Coluna embedding genérica (sem dimensão fixa)
ALTER TABLE kb_chunks ALTER COLUMN embedding TYPE vector;

-- 3. Índices HNSW parciais por dimensão
CREATE INDEX IF NOT EXISTS idx_kb_openai
ON kb_chunks USING hnsw ((embedding::vector(1536)) vector_cosine_ops)
WHERE (vector_dims(embedding) = 1536);

CREATE INDEX IF NOT EXISTS idx_kb_bgem3
ON kb_chunks USING hnsw ((embedding::vector(1024)) vector_cosine_ops)
WHERE (vector_dims(embedding) = 1024);

-- 4. Modelo de embedding por projeto
ALTER TABLE planning_projects
ADD COLUMN IF NOT EXISTS embedding_model TEXT DEFAULT 'openai';
