-- Funções utilitárias de busca (KISS)
-- Observação: evitamos RRF no banco; híbrido = união simples de candidatos

-- Busca vetorial
create or replace function public.kb_vector_search(
  query_embedding text,
  p_k int,
  p_threshold double precision default null,
  p_client_id uuid default null,
  p_empresa text default null,
  p_chunking text default null
)
returns table (
  doc_path text,
  chunk_ix int,
  content text,
  score double precision,
  meta jsonb
) language sql stable as $$
  with q as (
    select query_embedding::vector(1536) as qvec
  ), base as (
    select * from public.kb_chunks
    where (p_client_id is null or client_id = p_client_id)
      and (p_empresa  is null or lower(empresa) = lower(p_empresa))
      and (p_chunking is null or meta->>'chunking' = p_chunking)
  )
  select b.doc_path, b.chunk_ix, b.content,
         1 - (b.embedding <=> q.qvec) as score,
         b.meta
  from base b, q
  where (p_threshold is null) or (1 - (b.embedding <=> q.qvec)) >= p_threshold
  order by b.embedding <=> q.qvec asc
  limit p_k
$$;

-- Busca textual (FTS)
create or replace function public.kb_text_search(
  query_text text,
  p_k int,
  p_client_id uuid default null,
  p_empresa text default null,
  p_chunking text default null
)
returns table (
  doc_path text,
  chunk_ix int,
  content text,
  score double precision,
  meta jsonb
) language sql stable as $$
  with base as (
    select * from public.kb_chunks
    where (p_client_id is null or client_id = p_client_id)
      and (p_empresa  is null or lower(empresa) = lower(p_empresa))
      and (p_chunking is null or meta->>'chunking' = p_chunking)
  ), q as (
    select plainto_tsquery('portuguese', query_text) as tsq
  )
  select b.doc_path, b.chunk_ix, b.content,
         ts_rank_cd(b.fts, q.tsq) as score,
         b.meta
  from base b, q
  where b.fts @@ q.tsq
  order by ts_rank_cd(b.fts, q.tsq) desc
  limit p_k
$$;

-- Híbrido com RRF (Reciprocal Rank Fusion) no banco
-- Parâmetros de RRF fixos (K=60) e pesos (text=1.0, vector=1.5) por simplicidade (KISS)
create or replace function public.kb_hybrid_search(
  query_text text,
  query_embedding text,
  p_k int,
  p_threshold double precision default null,
  p_client_id uuid default null,
  p_empresa text default null,
  p_chunking text default null
)
returns table (
  doc_path text,
  chunk_ix int,
  content text,
  score double precision,
  meta jsonb
) language sql stable as $$
  with v as (
    select doc_path, chunk_ix, content, score, meta,
           row_number() over (order by score desc) as rnk_v
    from public.kb_vector_search(query_embedding, p_k, p_threshold, p_client_id, p_empresa, p_chunking)
  ), t as (
    select doc_path, chunk_ix, content, score, meta,
           row_number() over (order by score desc) as rnk_t
    from public.kb_text_search(query_text, p_k, p_client_id, p_empresa, p_chunking)
  ), u as (
    select coalesce(v.doc_path, t.doc_path) as doc_path,
           coalesce(v.chunk_ix, t.chunk_ix) as chunk_ix,
           coalesce(v.content, t.content) as content,
           coalesce(v.meta, t.meta) as meta,
           v.rnk_v, t.rnk_t
    from v full outer join t
      on v.doc_path = t.doc_path and v.chunk_ix = t.chunk_ix
  ), r as (
    select doc_path, chunk_ix, content, meta,
           coalesce(1.5 / (60 + rnk_v), 0) + coalesce(1.0 / (60 + rnk_t), 0) as score
    from u
  )
  select doc_path, chunk_ix, content, score, meta
  from r
  order by score desc
  limit p_k
$$;

-- Versão com união simples (sem RRF), útil para experimentos
create or replace function public.kb_hybrid_union(
  query_text text,
  query_embedding text,
  p_k int,
  p_threshold double precision default null,
  p_client_id uuid default null,
  p_empresa text default null,
  p_chunking text default null
)
returns table (
  doc_path text,
  chunk_ix int,
  content text,
  score double precision,
  meta jsonb
) language sql stable as $$
  with v as (
    select * from public.kb_vector_search(query_embedding, p_k, p_threshold, p_client_id, p_empresa, p_chunking)
  ), t as (
    select * from public.kb_text_search(query_text, p_k, p_client_id, p_empresa, p_chunking)
  ), u as (
    select * from v
    union
    select * from t
  )
  select doc_path, chunk_ix, content, score, meta
  from u
  order by score desc
  limit p_k
$$;
