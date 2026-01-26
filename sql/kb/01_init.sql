-- Habilitar extensão pgvector
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- Para full-text search
-- Tabela kb_docs (Staging)
CREATE TABLE public.kb_docs (
    id SERIAL PRIMARY KEY,
    source_path TEXT NOT NULL,
    source_hash VARCHAR(64) NOT NULL,
    mime_type TEXT DEFAULT 'text/markdown',
    content TEXT,
    meta JSONB DEFAULT '{}',
    client_id UUID,
    empresa TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT kb_docs_unique UNIQUE (source_path, source_hash)
);
-- Tabela kb_chunks (Vetores)
CREATE TABLE public.kb_chunks (
    id SERIAL PRIMARY KEY,
    doc_path TEXT NOT NULL,
    chunk_ix INTEGER NOT NULL,
    content TEXT,
    embedding vector(1536),
    -- OpenAI text-embedding-3-small
    meta JSONB DEFAULT '{}',
    client_id UUID,
    empresa TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT kb_chunks_unique UNIQUE (doc_path, chunk_ix)
);