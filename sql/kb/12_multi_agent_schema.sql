-- ============================================================
-- 12_multi_agent_schema.sql
-- Multi-Agent Platform: Organizations, Agents, Connectors,
-- Skills, Knowledge Domains
-- ============================================================

-- Enable uuid-ossp if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. Organizations (multi-tenant root)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_organizations_slug ON public.organizations(slug);

-- ============================================================
-- 2. Connectors (system-level integration registry)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.connectors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    icon TEXT,            -- icon name or emoji
    category TEXT DEFAULT 'integration',  -- integration, search, utility
    config_schema JSONB DEFAULT '{}',     -- JSON Schema for per-agent config
    is_system BOOLEAN DEFAULT true,       -- system connectors can't be deleted
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_connectors_slug ON public.connectors(slug);

-- ============================================================
-- 3. Skills (system-level capability registry)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    category TEXT DEFAULT 'methodology',  -- methodology, analysis, reporting
    prompt_fragment TEXT,                  -- appended to system prompt when enabled
    is_system BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_skills_slug ON public.skills(slug);

-- ============================================================
-- 4. Knowledge Domains (per-org RAG isolation)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.knowledge_domains (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    description TEXT,
    color TEXT DEFAULT '#6366f1',  -- for UI badge color
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(org_id, slug)
);

CREATE INDEX IF NOT EXISTS idx_knowledge_domains_org ON public.knowledge_domains(org_id);

-- ============================================================
-- 5. Agents (per-org agent definitions)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    slug TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    avatar TEXT,           -- URL or emoji
    system_prompt TEXT,
    agent_type TEXT DEFAULT 'simple',  -- simple, unified, vsa
    model_override TEXT,               -- NULL = use default model
    is_default BOOLEAN DEFAULT false,  -- one default per org
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(org_id, slug)
);

CREATE INDEX IF NOT EXISTS idx_agents_org ON public.agents(org_id);
CREATE INDEX IF NOT EXISTS idx_agents_default ON public.agents(org_id, is_default) WHERE is_default = true;

-- ============================================================
-- 6. Junction: Agent <-> Connector
-- ============================================================
CREATE TABLE IF NOT EXISTS public.agent_connectors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES public.agents(id) ON DELETE CASCADE,
    connector_id UUID NOT NULL REFERENCES public.connectors(id) ON DELETE CASCADE,
    enabled BOOLEAN DEFAULT true,
    config JSONB DEFAULT '{}',  -- per-agent connector config overrides
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(agent_id, connector_id)
);

CREATE INDEX IF NOT EXISTS idx_agent_connectors_agent ON public.agent_connectors(agent_id);

-- ============================================================
-- 7. Junction: Agent <-> Skill
-- ============================================================
CREATE TABLE IF NOT EXISTS public.agent_skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES public.agents(id) ON DELETE CASCADE,
    skill_id UUID NOT NULL REFERENCES public.skills(id) ON DELETE CASCADE,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(agent_id, skill_id)
);

CREATE INDEX IF NOT EXISTS idx_agent_skills_agent ON public.agent_skills(agent_id);

-- ============================================================
-- 8. Junction: Agent <-> Knowledge Domain
-- ============================================================
CREATE TABLE IF NOT EXISTS public.agent_domains (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES public.agents(id) ON DELETE CASCADE,
    domain_id UUID NOT NULL REFERENCES public.knowledge_domains(id) ON DELETE CASCADE,
    access_level TEXT DEFAULT 'read',  -- read, write, admin
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(agent_id, domain_id)
);

CREATE INDEX IF NOT EXISTS idx_agent_domains_agent ON public.agent_domains(agent_id);

-- ============================================================
-- 9. ALTER users: add org_id, role, display_name
-- ============================================================
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS org_id UUID REFERENCES public.organizations(id);
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user';
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS display_name TEXT;

CREATE INDEX IF NOT EXISTS idx_users_org ON public.users(org_id);

-- ============================================================
-- 10. ALTER kb_docs & kb_chunks: add domain_id for RAG isolation
-- ============================================================
ALTER TABLE public.kb_docs ADD COLUMN IF NOT EXISTS domain_id UUID REFERENCES public.knowledge_domains(id);
ALTER TABLE public.kb_chunks ADD COLUMN IF NOT EXISTS domain_id UUID REFERENCES public.knowledge_domains(id);

CREATE INDEX IF NOT EXISTS idx_kb_docs_domain ON public.kb_docs(domain_id);
CREATE INDEX IF NOT EXISTS idx_kb_chunks_domain ON public.kb_chunks(domain_id);

-- ============================================================
-- SEED DATA
-- ============================================================

-- Default organization
INSERT INTO public.organizations (id, name, slug, settings)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'Default',
    'default',
    '{"description": "Organização padrão do sistema"}'
)
ON CONFLICT (slug) DO NOTHING;

-- System connectors
INSERT INTO public.connectors (slug, name, description, icon, category) VALUES
    ('glpi',     'GLPI',     'Gestão de chamados e ativos ITSM',         'ticket',  'integration'),
    ('zabbix',   'Zabbix',   'Monitoramento de infraestrutura',          'activity','integration'),
    ('linear',   'Linear',   'Gestão de projetos e issues',              'kanban',  'integration'),
    ('tavily',   'Tavily',   'Busca web com IA',                         'search',  'search'),
    ('planning', 'Planning', 'Planejamento de projetos (NotebookLM-like)','book',   'utility')
ON CONFLICT (slug) DO NOTHING;

-- System skills
INSERT INTO public.skills (slug, name, description, icon, category, prompt_fragment) VALUES
    ('itil_classification', 'Classificação ITIL',
     'Classifica requisições em tipos ITIL (Incidente, Problema, Mudança, Requisição)',
     'tag', 'methodology',
     'Classifique em ITIL (INCIDENTE, PROBLEMA, MUDANÇA, REQUISIÇÃO, CONVERSA). Tipos: INCIDENTE=interrupção/degradação; PROBLEMA=causa raiz; MUDANÇA=alteração planejada; REQUISIÇÃO=serviço padrão; CONVERSA=geral.'),

    ('gut_scoring', 'Priorização GUT',
     'Calcula score de prioridade usando matriz GUT (Gravidade, Urgência, Tendência)',
     'bar-chart', 'methodology',
     'Priorize com GUT (Gravidade×Urgência×Tendência, cada 1-5). Apresente em tabela: | Critério | Score | Justificativa |'),

    ('rca_5whys', 'RCA - 5 Porquês',
     'Análise de causa raiz usando técnica dos 5 Porquês',
     'search', 'analysis',
     'Para problemas, aplique RCA com 5 Porquês: Por quê #1 → #2 → #3 → #4 → #5 até a causa raiz. Documente cada nível.'),

    ('analysis_5w2h', 'Análise 5W2H',
     'Estrutura análise com What, Why, Where, When, Who, How, How much',
     'clipboard', 'analysis',
     'Estruture a análise em 5W2H: | Elemento | Detalhe | — What, Why, Where, When, Who, How, How much.'),

    ('report_generation', 'Geração de Relatórios',
     'Gera relatórios executivos formatados em Markdown com tabelas',
     'file-text', 'reporting',
     'Gere relatórios executivos com: Resumo Executivo, Dados (tabelas markdown), Análise, Recomendações, Próximos Passos.'),

    ('web_search', 'Busca Web',
     'Permite buscar informações na web via Tavily',
     'globe', 'search',
     'Quando necessário, busque informações atualizadas na web para complementar sua análise.')
ON CONFLICT (slug) DO NOTHING;

-- Default knowledge domain (TI)
INSERT INTO public.knowledge_domains (id, org_id, name, slug, description, color)
VALUES (
    '00000000-0000-0000-0000-000000000010',
    '00000000-0000-0000-0000-000000000001',
    'Tecnologia da Informação',
    'ti',
    'Base de conhecimento de TI, infraestrutura, suporte e operações',
    '#f97316'
)
ON CONFLICT (org_id, slug) DO NOTHING;

-- Default agent (mirrors current behavior)
INSERT INTO public.agents (id, org_id, slug, name, description, avatar, system_prompt, agent_type, is_default)
VALUES (
    '00000000-0000-0000-0000-000000000100',
    '00000000-0000-0000-0000-000000000001',
    'vsa-default',
    'VSA - Assistente de TI',
    'Agente padrão com acesso a todas as integrações e habilidades ITIL',
    'bot',
    NULL,  -- uses default VSA_CORE_PROMPT from chat.py
    'unified',
    true
)
ON CONFLICT (org_id, slug) DO NOTHING;

-- Link default agent to all connectors
INSERT INTO public.agent_connectors (agent_id, connector_id)
SELECT
    '00000000-0000-0000-0000-000000000100',
    c.id
FROM public.connectors c
WHERE c.slug IN ('glpi', 'zabbix', 'linear', 'tavily', 'planning')
ON CONFLICT (agent_id, connector_id) DO NOTHING;

-- Link default agent to all skills
INSERT INTO public.agent_skills (agent_id, skill_id)
SELECT
    '00000000-0000-0000-0000-000000000100',
    s.id
FROM public.skills s
WHERE s.slug IN ('itil_classification', 'gut_scoring', 'rca_5whys', 'analysis_5w2h', 'report_generation', 'web_search')
ON CONFLICT (agent_id, skill_id) DO NOTHING;

-- Link default agent to TI domain
INSERT INTO public.agent_domains (agent_id, domain_id, access_level)
VALUES (
    '00000000-0000-0000-0000-000000000100',
    '00000000-0000-0000-0000-000000000010',
    'admin'
)
ON CONFLICT (agent_id, domain_id) DO NOTHING;

-- Assign existing users to default org (if they don't have one)
UPDATE public.users SET org_id = '00000000-0000-0000-0000-000000000001' WHERE org_id IS NULL;
UPDATE public.users SET role = 'admin' WHERE role IS NULL OR role = 'user';
