-- Índices para kb_docs
CREATE INDEX idx_kb_docs_empresa ON public.kb_docs(empresa);
CREATE INDEX idx_kb_docs_client_id ON public.kb_docs(client_id);
CREATE INDEX idx_kb_docs_source_path ON public.kb_docs(source_path);
-- Índices para kb_chunks
CREATE INDEX idx_kb_chunks_empresa ON public.kb_chunks(empresa);
CREATE INDEX idx_kb_chunks_client_id ON public.kb_chunks(client_id);
CREATE INDEX idx_kb_chunks_doc_path ON public.kb_chunks(doc_path);
-- Índice HNSW para busca vetorial (pgvector)
CREATE INDEX idx_kb_chunks_embedding ON public.kb_chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
-- Índice GIN para full-text search
CREATE INDEX idx_kb_chunks_content_trgm ON public.kb_chunks USING gin (content gin_trgm_ops);