-- Módulo 1A — Esquema CRM (clean schema)
-- Requisitos: Postgres com extensão pgcrypto para gen_random_uuid()

create extension if not exists "pgcrypto";

-- Tabela de lookup para status de lead
create table if not exists public.status_lead (
  codigo text primary key,
  rotulo text not null,
  criado_em timestamptz not null default now()
);

-- Comentários (documentação)
comment on table public.status_lead is 'Lookup de status de lead (tabela de referência).';
comment on column public.status_lead.codigo is 'Código do status (PK), ex.: novo, qualificado.';
comment on column public.status_lead.rotulo is 'Rótulo amigável do status.';
comment on column public.status_lead.criado_em is 'Timestamp de criação do registro.';

-- Tabela principal de leads
create table if not exists public.leads (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  email text unique,
  telefone text,
  empresa text,
  origem text,
  qualificado boolean not null default false,
  status_codigo text not null references public.status_lead(codigo) default 'novo',
  ultimo_contato_em timestamptz,
  proxima_acao_em timestamptz,
  criado_em timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);

-- Comentários (documentação)
comment on table public.leads is 'Entidade principal de leads (potenciais clientes).';
comment on column public.leads.id is 'Identificador único do lead (UUID).';
comment on column public.leads.nome is 'Nome do lead ou contato principal.';
comment on column public.leads.email is 'E-mail do lead (único quando preenchido).';
comment on column public.leads.telefone is 'Telefone do lead (formato livre).';
comment on column public.leads.empresa is 'Empresa do lead.';
comment on column public.leads.origem is 'Origem do lead (campanha, canal etc.).';
comment on column public.leads.qualificado is 'Indica se o lead está qualificado.';
comment on column public.leads.status_codigo is 'Código do status do lead (FK para status_lead.codigo).';
comment on column public.leads.ultimo_contato_em is 'Data/hora do último contato.';
comment on column public.leads.proxima_acao_em is 'Data/hora da próxima ação planejada.';
comment on column public.leads.criado_em is 'Timestamp de criação.';
comment on column public.leads.atualizado_em is 'Timestamp da última atualização.';

-- Unicidade (case-insensitive) de email quando presente
do $$ begin
  if not exists (
    select 1 from pg_indexes where schemaname = 'public' and indexname = 'uq_leads_email'
  ) then
    execute 'create unique index uq_leads_email on public.leads (lower(email)) where email is not null';
  end if;
end $$;

-- Índices úteis para busca/listagem
do $$ begin
  if not exists (
    select 1 from pg_indexes where schemaname = 'public' and indexname = 'idx_leads_nome_lower'
  ) then
    execute 'create index idx_leads_nome_lower on public.leads (lower(nome))';
  end if;
  if not exists (
    select 1 from pg_indexes where schemaname = 'public' and indexname = 'idx_leads_empresa_lower'
  ) then
    execute 'create index idx_leads_empresa_lower on public.leads (lower(empresa))';
  end if;
end $$;

-- Índices adicionais (idempotentes)
create index if not exists idx_leads_status_codigo on public.leads (status_codigo);
create index if not exists idx_leads_criado_em on public.leads (criado_em desc);

-- Unicidade (case-insensitive) de telefone normalizado quando presente
-- Garante que dois telefones equivalentes (com/sem máscara) não coexistam
create unique index if not exists uq_leads_phone_digits
  on public.leads ((regexp_replace(telefone, '[^0-9]', '', 'g'))) where telefone is not null;

-- Notas por lead (1:N)
create table if not exists public.notas_lead (
  id uuid primary key default gen_random_uuid(),
  lead_id uuid not null references public.leads(id) on delete cascade,
  texto text not null,
  criado_em timestamptz not null default now()
);

-- Comentários (documentação)
comment on table public.notas_lead is 'Notas associadas a um lead (histórico de interações).';
comment on column public.notas_lead.id is 'Identificador da nota (UUID).';
comment on column public.notas_lead.lead_id is 'Referência ao lead (FK).';
comment on column public.notas_lead.texto is 'Conteúdo livre da nota.';
comment on column public.notas_lead.criado_em is 'Timestamp da criação da nota.';

create index if not exists idx_notas_lead_lead_id on public.notas_lead (lead_id);
create index if not exists idx_notas_lead_criado_em on public.notas_lead (criado_em desc);

-- Tarefas por lead (1:N)
create table if not exists public.tarefas_lead (
  id uuid primary key default gen_random_uuid(),
  lead_id uuid not null references public.leads(id) on delete cascade,
  tipo text not null check (tipo in ('ligacao','email','reuniao','tarefa')),
  titulo text not null,
  status text not null check (status in ('aberta','concluida','cancelada')),
  data_limite timestamptz,
  prioridade text,
  criado_em timestamptz not null default now(),
  concluido_em timestamptz
);

-- Comentários (documentação)
comment on table public.tarefas_lead is 'Tarefas vinculadas a um lead (to-dos e follow-ups).';
comment on column public.tarefas_lead.id is 'Identificador da tarefa (UUID).';
comment on column public.tarefas_lead.lead_id is 'Referência ao lead (FK).';
comment on column public.tarefas_lead.tipo is 'Tipo da tarefa: ligacao, email, reuniao, tarefa.';
comment on column public.tarefas_lead.titulo is 'Título/descritivo curto da tarefa.';
comment on column public.tarefas_lead.status is 'Status da tarefa: aberta, concluida, cancelada.';
comment on column public.tarefas_lead.data_limite is 'Prazo/vence em (opcional).';
comment on column public.tarefas_lead.prioridade is 'Prioridade textual (opcional).';
comment on column public.tarefas_lead.criado_em is 'Timestamp de criação da tarefa.';
comment on column public.tarefas_lead.concluido_em is 'Timestamp de conclusão (quando completada).';

create index if not exists idx_tarefas_lead_status_data on public.tarefas_lead (lead_id, status, data_limite);

-- Propostas (1:N com leads)
create table if not exists public.propostas (
  id uuid primary key default gen_random_uuid(),
  lead_id uuid not null references public.leads(id) on delete cascade,
  titulo text not null,
  moeda text not null default 'BRL',
  subtotal numeric(12,2) not null default 0,
  desconto_pct numeric(5,2) not null default 0 check (desconto_pct >= 0 and desconto_pct <= 100),
  total numeric(12,2) not null default 0,
  corpo_md text,
  status text not null default 'rascunho',
  criado_em timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);

-- Comentários (documentação)
comment on table public.propostas is 'Propostas comerciais associadas a um lead.';
comment on column public.propostas.id is 'Identificador da proposta (UUID).';
comment on column public.propostas.lead_id is 'Lead associado (FK).';
comment on column public.propostas.titulo is 'Título da proposta.';
comment on column public.propostas.moeda is 'Moeda da proposta (padrão BRL).';
comment on column public.propostas.subtotal is 'Soma dos itens antes de descontos.';
comment on column public.propostas.desconto_pct is 'Desconto percentual aplicado (0–100).';
comment on column public.propostas.total is 'Valor total após desconto.';
comment on column public.propostas.corpo_md is 'Corpo da proposta em Markdown (conteúdo textual).';
comment on column public.propostas.status is 'Status da proposta (ex.: rascunho).';
comment on column public.propostas.criado_em is 'Timestamp de criação.';
comment on column public.propostas.atualizado_em is 'Timestamp de atualização.';

create index if not exists idx_propostas_lead_id on public.propostas (lead_id);

-- Itens de proposta (1:N)
create table if not exists public.itens_proposta (
  id uuid primary key default gen_random_uuid(),
  proposta_id uuid not null references public.propostas(id) on delete cascade,
  descricao text not null,
  quantidade numeric(12,2) not null check (quantidade >= 0),
  preco_unitario numeric(12,2) not null check (preco_unitario >= 0),
  total numeric(12,2) not null
);

-- Comentários (documentação)
comment on table public.itens_proposta is 'Itens de uma proposta (produtos/serviços).';
comment on column public.itens_proposta.id is 'Identificador do item da proposta (UUID).';
comment on column public.itens_proposta.proposta_id is 'Proposta associada (FK).';
comment on column public.itens_proposta.descricao is 'Descrição do item.';
comment on column public.itens_proposta.quantidade is 'Quantidade.';
comment on column public.itens_proposta.preco_unitario is 'Preço unitário.';
comment on column public.itens_proposta.total is 'Total do item (quantidade x preço).';

create index if not exists idx_itens_proposta_proposta_id on public.itens_proposta (proposta_id);
