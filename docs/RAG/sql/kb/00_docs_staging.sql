-- Staging de documentos brutos do KB

create table if not exists public.kb_docs (
  id bigserial primary key,
  source_path text not null,
  source_hash text not null,
  mime_type text not null default 'text/markdown',
  content text not null,
  meta jsonb not null default '{}'::jsonb,
  client_id uuid null,
  empresa text null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (source_path, source_hash)
);

create or replace function public.kb_docs_touch_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

drop trigger if exists kb_docs_set_updated_at on public.kb_docs;
create trigger kb_docs_set_updated_at
before update on public.kb_docs
for each row execute function public.kb_docs_touch_updated_at();

create index if not exists ix_kb_docs_source on public.kb_docs (source_path);
create index if not exists ix_kb_docs_empresa on public.kb_docs (empresa);
create index if not exists ix_kb_docs_client on public.kb_docs (client_id);

