-- KB schema para RAG (chunks de Markdown)
-- KISS: tabela única com vetor + FTS + filtros simples (empresa/cliente)

create extension if not exists vector;

-- Observação: evitamos dependências extras (uuid-ossp/pgcrypto).
-- Usamos chave surrogate BIGSERIAL e unicidade por (doc_path, chunk_ix).

create table if not exists public.kb_chunks (
  id bigserial primary key,
  doc_path text not null,
  chunk_ix int not null,
  content text not null,
  embedding vector(1536) not null,
  fts tsvector generated always as (to_tsvector('portuguese', coalesce(content, ''))) stored,
  meta jsonb not null default '{}'::jsonb,
  -- filtros opcionais por tenant/empresa
  client_id uuid null,
  empresa text null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (doc_path, chunk_ix)
);

create or replace function public.kb_touch_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

drop trigger if exists kb_chunks_set_updated_at on public.kb_chunks;
create trigger kb_chunks_set_updated_at
before update on public.kb_chunks
for each row execute function public.kb_touch_updated_at();
