# VSA NEXUS AI: Proposta de Produto Enterprise (SaaS B2B)

> **Versao:** 2.0 | **Data:** 16/02/2026 | **Status:** Pre-Seed / MVP em Producao
> **Autor:** VSA Tecnologia | **Classificacao:** Confidencial

---

## Sumario Executivo

O **VSA NEXUS AI** e uma plataforma SaaS B2B de **Governanca de IA para Gestao de TI** que transforma dados operacionais dispersos em decisoes inteligentes de gestao. Diferente de chatbots genericos, o NEXUS combina:

- **Metodologias ITIL nativas** (classificacao, GUT, RCA, 5W2H)
- **Integracao multi-sistema** (GLPI, Zabbix, Linear, Proxmox, Cloud)
- **RAG com governanca de dados** (isolamento por dominio, schema discovery)
- **Controle financeiro de IA** (custos por modelo, otimizacao automatica)

**Proposta de Valor:** Reduzir tempo diagnostico em 60% (45min -> 15min), com 100% aderencia ITIL e controle total de custos de IA.

**Mercado-alvo:** IT Managers, NOC/SOC, MSPs, Healthcare IT, Educacao.

---

## 1. Diagnostico: Estado Atual do Produto (As-Is)

### 1.1 O que JA funciona (MVP em producao)

| Componente | Status | Detalhes |
|---|---|---|
| **Chat Web (Next.js 15 + React 19)** | FUNCIONAL | SSE streaming, sessoes, selecao de modelo, artifacts |
| **FastAPI Backend (14 routers)** | FUNCIONAL | Chat, RAG, Agents, Planning, Files, Export, Reports, Auth, etc. |
| **Integracao GLPI** | FUNCIONAL | Listar/criar tickets, filtros, cache Redis 120s |
| **Integracao Zabbix** | FUNCIONAL | Alertas com severidade, hosts, items, cache Redis 60s |
| **Integracao Linear.app** | FUNCIONAL | Issues, projetos com milestones, comments, dry_run |
| **Router Rule-Based** | FUNCIONAL | Regex detecta intencoes conhecidas, bypassa LLM (zero tokens) |
| **Sistema de Artifacts** | FUNCIONAL | SSE events, split-panel, export PDF/DOCX/MD |
| **Autenticacao Basica** | FUNCIONAL | JWT + bcrypt, login/registro, API Key + Bearer |
| **RAG Pipeline** | FUNCIONAL | 3 estrategias chunking, pgvector, multi-tenant |
| **UnifiedAgent (LangGraph)** | FUNCIONAL | Router, Classifier ITIL, Planner, Executor, Tiered Models |
| **Planning (NotebookLM-like)** | FUNCIONAL | Upload docs, analise IA, etapas/orcamento, sync Linear |
| **Multi-Model (OpenRouter)** | FUNCIONAL | Fast/Smart/Premium/Creative/Vision tiers |
| **Cache Redis** | FUNCIONAL | TTL configuravel por tipo de dado |
| **File Storage (MinIO)** | FUNCIONAL | Upload, signed URLs, extracao texto |
| **Design System Obsidian** | FUNCIONAL | Deep Void (#050505), Glass Shell, brand gradient laranja/azul |

### 1.2 O que FALTA para Enterprise (To-Be)

| Componente | Gap | Criticidade |
|---|---|---|
| **Multi-Tenant** | Inexistente (single-tenant) | CRITICO |
| **RBAC** | Inexistente (sem roles/permissoes) | CRITICO |
| **Auditoria Estruturada** | Apenas Python logging basico | CRITICO |
| **Billing/Subscricao** | Inexistente | ALTO |
| **LGPD/GDPR** | Inexistente | ALTO |
| **Confirmacao WRITE** | Nodo Confirmer nao implementado | ALTO |
| **Reflector/Replan** | Nodo nao implementado no UnifiedAgent | MEDIO |
| **Correlacao GLPI-Zabbix** | Nao implementado | MEDIO |
| **RCA (5 Whys) Estruturado** | Apenas prompt-based | MEDIO |
| **Webhook/Alertas Proativos** | Query-only, sem push | MEDIO |
| **CLI Interface** | Adiada para v2.0 | BAIXO |

### 1.3 Arquitetura Atual (Validada)

```
                    Frontend (Next.js 15)
                           |
                     /api/v1/* proxy
                           |
                    FastAPI Backend
                    /     |     \
               Chat    RAG    Planning
                |       |        |
          UnifiedAgent  pgvector  Gemini
          (LangGraph)
         /    |    \
      GLPI  Zabbix  Linear
       |      |       |
    Redis   Redis   GraphQL
```

**Stack Validado:** Python 3.11+, FastAPI, LangGraph, LangChain, PostgreSQL 16 + pgvector, Redis, MinIO, Next.js 15 + React 19, Tailwind CSS, OpenRouter (multi-LLM).

---

## 2. Visao de Produto: NEXUS AI Platform

### 2.1 Posicionamento

> "O VSA Nexus nao e um chatbot. E uma **Plataforma de Governanca de IA para TI** que segrega conhecimento em **Dominios Seguros**, aplica **ITIL automaticamente**, e controla **custos de inferencia** com granularidade por tenant, agente e modelo."

### 2.2 Piramide de Valor

```
                    +-------------------+
                    |  DECISAO          |  <- Executive Insights
                    |  ESTRATEGICA      |     Reports 5W2H, Dashboard KPI
                    +-------------------+
                    |  ANALISE          |  <- Correlacao Multi-Sistema
                    |  INTELIGENTE      |     RCA, GUT, Pattern Detection
                    +-------------------+
                    |  METODOLOGIA      |  <- ITIL Automatico
                    |  APLICADA         |     Classification, Prioritization
                    +-------------------+
                    |  INTEGRACAO       |  <- Conectores Multi-API
                    |  DE DADOS         |     GLPI, Zabbix, Linear, Cloud
                    +-------------------+
                    |  GOVERNANCA       |  <- IAM + Multi-Tenant
                    |  & SEGURANCA      |     RBAC, Audit, LGPD
                    +-------------------+
```

---

## 3. Camada 1: Identidade e Acesso (IAM)

### 3.1 Estado Atual vs Enterprise

| Feature | Atual | Enterprise Target |
|---|---|---|
| Login | Email/Senha (JWT, bcrypt) | + OAuth2 (Google, Microsoft), SAML 2.0, OIDC |
| MFA | Inexistente | TOTP, WebAuthn |
| Users | Tabela `users` (id, username, email, hash) | + org_id, role, status, last_login, login_count |
| Roles | Inexistente | Super Admin, Tenant Admin, Gestor, Usuario, Auditor, API User |
| Permissoes | Inexistente | Por modulo, agente, relatorio, integracao |
| Multi-Tenant | Inexistente | Isolamento total (coluna `org_id` + RLS) |

### 3.2 Modelo de Dados Proposto (DBAC - Domain-Based Access Control)

Evoluindo do proposal_iam.md.resolved, com base no codigo real:

```sql
-- Organizacoes (Tenants)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    plan VARCHAR(20) DEFAULT 'trial',  -- trial, starter, pro, enterprise
    settings JSONB DEFAULT '{}',
    max_users INTEGER DEFAULT 5,
    max_agents INTEGER DEFAULT 3,
    max_tokens_month BIGINT DEFAULT 1000000,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Departamentos
CREATE TABLE departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    UNIQUE(org_id, name)
);

-- Dominios de Conhecimento (coraoo do NEXUS)
CREATE TABLE knowledge_domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,         -- "Infraestrutura", "RH", "Financeiro"
    type VARCHAR(20) DEFAULT 'ROOT',  -- ROOT, SUB
    parent_id UUID REFERENCES knowledge_domains(id),
    allowed_tables TEXT[],      -- Schema whitelist para RAG SQL
    config JSONB DEFAULT '{}'
);

-- Evolucao da tabela users existente
ALTER TABLE users ADD COLUMN org_id UUID REFERENCES organizations(id);
ALTER TABLE users ADD COLUMN role VARCHAR(30) DEFAULT 'user';
ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active';
ALTER TABLE users ADD COLUMN department_id UUID REFERENCES departments(id);
ALTER TABLE users ADD COLUMN last_login_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN login_count INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN invited_by INTEGER REFERENCES users(id);
ALTER TABLE users ADD COLUMN access_expires_at TIMESTAMPTZ;

-- Permissoes por dominio
CREATE TABLE user_domain_access (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    domain_id UUID REFERENCES knowledge_domains(id) ON DELETE CASCADE,
    access_level VARCHAR(20) DEFAULT 'READ',  -- READ, WRITE, ADMIN
    PRIMARY KEY (user_id, domain_id)
);

-- Row-Level Security (RLS) para isolamento
ALTER TABLE kb_docs ENABLE ROW LEVEL SECURITY;
ALTER TABLE kb_chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_docs ON kb_docs
    USING (empresa = current_setting('app.current_org_slug'));
CREATE POLICY tenant_isolation_chunks ON kb_chunks
    USING (empresa = current_setting('app.current_org_slug'));
```

### 3.3 Roles e Permissoes (RBAC)

| Role | Chat | Agentes Config | Integ Config | RAG Upload | Usuarios | Billing | Audit |
|---|---|---|---|---|---|---|---|
| **Super Admin** | Full | Full | Full | Full | Full | Full | Full |
| **Tenant Admin** | Full | Full | Full | Full | Full | View | Full |
| **Gestor** | Full | View | View | Full | View | - | View |
| **Usuario** | Full | - | - | Own domain | - | - | - |
| **Auditor** | View | View | View | View | View | View | Full |
| **API User** | API Only | - | - | API Only | - | - | - |

### 3.4 OAuth2/SSO (Prioridade Alta)

Baseado no que as imagens da Fase 4 revelaram (conectores Google, GitHub ja configurados):

```python
# Evolucao do auth.py existente
# Adicionar endpoints OAuth2

@router.get("/oauth/google")
async def oauth_google_redirect():
    """Redirect para Google OAuth consent."""

@router.get("/oauth/google/callback")
async def oauth_google_callback(code: str):
    """Callback do Google OAuth - cria/vincula usuario."""

@router.get("/oauth/microsoft")
async def oauth_microsoft_redirect():
    """Redirect para Microsoft/Azure AD."""

@router.get("/oauth/saml/metadata")
async def saml_metadata():
    """SAML 2.0 Service Provider metadata."""
```

---

## 4. Camada 2: Governanca e Auditoria

### 4.1 Logs de Auditoria Estruturados

O PRD ja define o formato. Implementacao proposta sobre o sistema existente:

```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    org_id UUID REFERENCES organizations(id),
    user_id INTEGER REFERENCES users(id),
    timestamp TIMESTAMPTZ DEFAULT now(),

    -- O que aconteceu
    action VARCHAR(50) NOT NULL,       -- 'chat.message', 'tool.glpi_get_tickets', 'report.export'
    resource_type VARCHAR(50),         -- 'ticket', 'alert', 'issue', 'document'
    resource_id TEXT,                  -- ID externo do recurso

    -- Contexto IA
    model_used VARCHAR(100),           -- 'google/gemini-2.5-flash'
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    tokens_cost_usd DECIMAL(10,6),
    agent_name VARCHAR(50),            -- 'UnifiedAgent', 'SimpleAgent'
    session_id TEXT,

    -- Seguranca
    ip_address INET,
    user_agent TEXT,
    dry_run BOOLEAN DEFAULT false,

    -- Detalhes
    request_data JSONB,
    response_summary TEXT,
    error TEXT,

    -- Indexacao
    INDEX idx_audit_org_time (org_id, timestamp DESC),
    INDEX idx_audit_user (user_id, timestamp DESC),
    INDEX idx_audit_action (action)
);

-- Particionar por mes para performance
CREATE TABLE audit_logs_2026_02 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
```

### 4.2 Metricas de Consumo

Evolucao do monitoramento que ja existe (LangSmith tracing):

```python
# Novo: core/audit.py (aproveitando o pattern do core/auth.py)

class AuditService:
    """Servico centralizado de auditoria."""

    async def log_action(
        self,
        org_id: str,
        user_id: int,
        action: str,
        resource_type: str = None,
        resource_id: str = None,
        model_used: str = None,
        tokens_input: int = 0,
        tokens_output: int = 0,
        ip_address: str = None,
        dry_run: bool = False,
        request_data: dict = None,
        response_summary: str = None,
    ):
        """Registra acao no audit log."""

    async def get_usage_by_model(self, org_id: str, period: str = "month"):
        """Consumo agregado por modelo."""

    async def get_usage_by_user(self, org_id: str, period: str = "month"):
        """Consumo agregado por usuario."""

    async def get_usage_by_agent(self, org_id: str, period: str = "month"):
        """Consumo agregado por agente."""
```

### 4.3 Conformidade (LGPD/GDPR)

| Requisito | Implementacao |
|---|---|
| Consentimento | Termos aceitos no onboarding, versionados |
| Registro de Tratamento | Tabela `data_processing_records` com base legal |
| Direito ao Esquecimento | Endpoint `DELETE /api/v1/users/{id}/data` com cascade |
| Portabilidade | Endpoint `GET /api/v1/users/{id}/export` (JSON completo) |
| Retencao Configuravel | Setting `data_retention_days` por org |
| DPO | Campo `dpo_email` na tabela organizations |
| Anonimizacao | Logs de audit preservados com user_id = NULL apos delete |

---

## 5. Camada 3: Financeira (SaaS)

### 5.1 Planos

| | **Starter** | **Professional** | **Enterprise** | **Custom** |
|---|---|---|---|---|
| **Preco/mes** | R$ 497 | R$ 1.497 | R$ 4.997 | Sob consulta |
| **Usuarios** | 5 | 25 | Ilimitado | Ilimitado |
| **Tokens/mes** | 500K | 5M | 50M | Ilimitado |
| **Agentes** | 2 | 10 | Ilimitado | Ilimitado |
| **Integracoes** | 2 | 5 | Todas | Todas + Custom |
| **RAG Storage** | 1 GB | 10 GB | 100 GB | Ilimitado |
| **Dominios** | 1 | 5 | Ilimitado | Ilimitado |
| **Modelos** | Fast + Smart | + Premium | + Dedicados | GPU Dedicada |
| **Suporte** | Email | Priority | 24/7 + SLA | Dedicado |
| **Audit** | 30 dias | 90 dias | 1 ano | Custom |
| **SSO/SAML** | - | - | Incluso | Incluso |
| **Trial** | 14 dias | 14 dias | POC 30 dias | - |

### 5.2 Billing Engine

```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id),
    plan VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'trial',  -- trial, active, past_due, cancelled
    trial_ends_at TIMESTAMPTZ,
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    stripe_subscription_id TEXT,         -- Stripe ou Asaas (Brasil)
    asaas_subscription_id TEXT,          -- NF-e integrada
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE usage_records (
    id BIGSERIAL PRIMARY KEY,
    org_id UUID REFERENCES organizations(id),
    period_start DATE NOT NULL,
    tokens_used BIGINT DEFAULT 0,
    tokens_limit BIGINT,
    agents_active INTEGER DEFAULT 0,
    integrations_active INTEGER DEFAULT 0,
    storage_bytes BIGINT DEFAULT 0,
    api_calls INTEGER DEFAULT 0,
    overage_cost_brl DECIMAL(10,2) DEFAULT 0,
    UNIQUE(org_id, period_start)
);
```

### 5.3 Rate Limiting (por plano)

Aproveitando o Redis ja existente no projeto:

```python
# Evolucao do core/cache.py
RATE_LIMITS = {
    "starter":     {"rpm": 20,  "tpm": 50_000},
    "professional": {"rpm": 100, "tpm": 500_000},
    "enterprise":   {"rpm": 500, "tpm": 5_000_000},
}
```

---

## 6. Camada 4: IA (Core NEXUS)

### 6.1 Gestao de Agentes (Admin UI)

Baseado no UnifiedAgent ja implementado (`core/agents/unified.py`):

| Feature | Atual | Enterprise |
|---|---|---|
| Ativar/Desativar | Toggles no frontend (GLPI, Zabbix, Linear) | Admin panel com status por tenant |
| Prompt Base | Hardcoded em `get_system_prompt()` | Editavel por tenant no admin |
| Modelo Padrao | `google/gemini-2.5-flash` global | Configuravel por agente/tenant |
| Fallback | Nao implementado | Chain: Fast -> Smart -> Premium |
| Limite de Uso | Inexistente | Tokens/mes por agente |
| Tiered Models | Fast model para Router/Classifier | Completo por tenant |

### 6.2 Orquestrador Inteligente

Evolucao do UnifiedAgent existente (LangGraph StateGraph):

```
START -> Router -> [conversa_geral] -> Executor -> END
                   [it_request]     -> Classifier -> Planner -> Executor -> Reflector -> END
                   [multi_action]   -> Classifier -> Planner -> Executor -> Reflector -> END
                   [web_search]     -> Executor -> END
                                                        ^            |
                                                        |__ replan __|

NOVO: Reflector Node (validacao + replan loop)
NOVO: Confirmer Node (aprovacao WRITE)
NOVO: Auto-Router com score de confianca
NOVO: Metricas de qualidade por execucao
```

### 6.3 RAG Governance (Diferencial Tecnico)

Inspirado nas imagens do "RAG Avancado" (Fase 4) que mostram:
- Catalogo de dados com schema discovery
- Recommended Joins configuravel
- Few-Shot SQL Examples

```sql
-- Catalogo de Dados Governado
CREATE TABLE data_catalog (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id UUID REFERENCES knowledge_domains(id),
    source_type VARCHAR(20),      -- 'postgresql', 'mysql', 'csv', 'api'
    connection_config JSONB,       -- Encrypted connection details

    -- Schema Governance
    allowed_tables TEXT[],         -- Whitelist de tabelas
    blocked_columns TEXT[],        -- Blacklist (ex: CPF, salario)

    -- Semantic Layer
    recommended_joins JSONB,       -- [{"from": "pedido.id", "to": "tarifa.ref_pedido"}]
    few_shot_examples JSONB,       -- [{"question": "...", "sql": "..."}]

    -- Discovery
    last_discovery_at TIMESTAMPTZ,
    schema_snapshot JSONB,

    status VARCHAR(20) DEFAULT 'pending_approval'
);
```

### 6.4 Score de Qualidade e A/B Testing

```python
# Novo: core/quality.py

class QualityScorer:
    """Avaliacao automatica de qualidade das respostas."""

    async def score_response(
        self,
        query: str,
        response: str,
        model: str,
        tool_results: list,
    ) -> QualityScore:
        """
        Retorna score 0-100 baseado em:
        - Relevancia (resposta atende a pergunta?)
        - Completude (todos os dados solicitados?)
        - Precisao (dados consistentes com fontes?)
        - Metodologia (seguiu ITIL quando aplicavel?)
        """

    async def ab_compare(
        self,
        query: str,
        model_a: str,
        model_b: str,
    ) -> ABResult:
        """Comparacao side-by-side de modelos."""
```

---

## 7. Camada 5: Integracoes

### 7.1 Conectores Atuais (Prontos)

| Conector | Tipo | Operations | Status |
|---|---|---|---|
| **GLPI** | REST API | list/create tickets, locations | PRODUCAO |
| **Zabbix** | JSON-RPC | problems, hosts, items | PRODUCAO |
| **Linear.app** | GraphQL | issues, projects, milestones | PRODUCAO |
| **Tavily** | REST API | Web search | PRODUCAO |
| **MinIO/S3** | S3 API | File upload/download | PRODUCAO |

### 7.2 Conectores Planejados

| Conector | Tipo | Prioridade | ETA |
|---|---|---|---|
| **Proxmox** | REST API | Alta | Q2 2026 |
| **AWS (CloudWatch, EC2)** | SDK | Alta | Q2 2026 |
| **WhatsApp (via Zigchat)** | API | Alta | Q2 2026 |
| **Azure (Monitor, VMs)** | SDK | Media | Q3 2026 |
| **Google Drive** | OAuth2 API | Media | Q3 2026 |
| **SharePoint** | Graph API | Media | Q3 2026 |
| **ERP (TOTVS/SAP)** | REST/RFC | Media | Q3 2026 |
| **CRM (Pipedrive/HubSpot)** | REST API | Baixa | Q4 2026 |
| **Banco SQL Generico** | JDBC/ODBC | Media | Q3 2026 |

### 7.3 API Publica

```yaml
# API documentada para cada tenant
endpoints:
  - POST /api/v1/chat/stream       # Chat com SSE
  - GET  /api/v1/reports/dashboard  # Dashboard executivo
  - POST /api/v1/rag/search        # Busca na base de conhecimento
  - POST /api/v1/rag/ingest        # Upload de documentos
  - GET  /api/v1/audit/logs        # Logs de auditoria
  - POST /api/v1/export            # Export PDF/DOCX/MD

auth:
  - X-API-Key por tenant (ja implementado)
  - Bearer JWT (ja implementado)
  - Rate limit por chave (novo)

webhooks:
  - alert.critical                  # Alerta critico detectado
  - ticket.created                  # Ticket criado automaticamente
  - report.generated                # Relatorio pronto
  - usage.limit_approaching         # 80% do limite de tokens
```

---

## 8. Camada 6: Painel Administrativo

### 8.1 Dashboard Executivo (Tenant)

Usando o Design System Obsidian ja definido (Deep Void + Glass Shell + Gradient Brand):

```
+------------------------------------------------------+
|  VSA NEXUS AI        [Org: Hospital Evangelico]  [v2] |
+------+-----------------------------------------------+
| Nav  |  KPI Cards (Glass Panels)                     |
|      |  +----------+ +----------+ +----------+       |
| Visao|  | Tickets  | | Alertas  | | Issues   |       |
| Geral|  | Abertos  | | Criticos | | Linear   |       |
|      |  | 23       | | 5        | | 12       |       |
|      |  +----------+ +----------+ +----------+       |
| Chat |                                                |
|      |  ITIL Distribution (Donut Chart)               |
| Dash |  [Incidente 45%] [Requisicao 30%]              |
|      |  [Problema 15%]  [Mudanca 10%]                 |
| RAG  |                                                |
|      |  GUT Score Timeline (Area Chart)               |
| Users|  [Critico][Alto][Medio][Baixo] last 30 days    |
|      |                                                |
| Audit|  Token Consumption (Bar Chart)                 |
|      |  [Fast 60%] [Smart 30%] [Premium 10%]          |
| Conf |                                                |
|      |  Recent Activity Feed                          |
+------+-----------------------------------------------+
```

### 8.2 Telas Administrativas

| Tela | Descricao |
|---|---|
| **Dashboard Executivo** | KPIs, graficos ITIL, consumo, alertas |
| **Dashboard Tecnico** | Latencia, erros, uptime, model performance |
| **Gestao de Usuarios** | CRUD, convites, roles, status, historico login |
| **Gestao de Agentes** | Ativar/config, prompts, modelos, limites |
| **Gestao de Dominios** | Knowledge domains, schema whitelist, RAG config |
| **Integracoes** | Conectores, credenciais, health check, logs |
| **Auditoria** | Timeline, filtros por user/action/period, export |
| **Billing** | Plano atual, consumo, faturas, upgrade |
| **Configuracoes** | Globals, por tenant, retencao, LGPD |

---

## 9. Camada 7: Seguranca Enterprise

### 9.1 Infraestrutura

| Controle | Status Atual | Enterprise |
|---|---|---|
| HTTPS | Via proxy (nginx) | Obrigatorio + HSTS |
| TLS | 1.2+ | 1.3 preferencial |
| CORS | Configuravel via env | Strict per-origin |
| CSP | Inexistente | Headers completos |
| Rate Limiting | Inexistente | Redis-based, per-plan |
| Brute Force | Inexistente | Account lockout apos 5 tentativas |
| WAF | Inexistente | Cloudflare/AWS WAF |

### 9.2 Protecao de Dados

| Controle | Implementacao |
|---|---|
| **Criptografia em repouso** | PostgreSQL TDE ou volume-level encryption |
| **Criptografia em transito** | TLS 1.3 end-to-end |
| **Secrets** | Vault (HashiCorp) para credenciais de integracao |
| **Backup** | pg_dump automatico diario + WAL streaming |
| **Disaster Recovery** | Replica em regiao secundaria, RPO < 1h |
| **Log Centralization** | Structured JSON -> Loki/ELK |
| **Intrusion Detection** | Fail2ban + anomaly detection em audit logs |

### 9.3 Seguranca de IA

| Risco | Mitigacao |
|---|---|
| **Prompt Injection** | Input sanitization + output validation |
| **Data Leakage** | Domain isolation (RLS) + schema whitelist |
| **Excessive Token Use** | Hard limits per plan + alertas automaticos |
| **Unauthorized API Access** | dry_run=True default + Confirmer node |
| **Model Hallucination** | Anti-hallucination rules no system prompt (ja implementado) |

---

## 10. Camada 8: Observabilidade

### 10.1 Stack de Observabilidade

```
Aplicacao -> Structured Logs (JSON)  -> Loki
          -> Tracing (LangSmith)     -> LangSmith Dashboard
          -> Metricas (Prometheus)   -> Grafana
          -> Alertas                 -> Slack/Email/PagerDuty
          -> Health Check            -> /health endpoint (ja existe)
```

### 10.2 Metricas Chave

| Metrica | Fonte | Alerta |
|---|---|---|
| Response Latency (p50, p95, p99) | FastAPI middleware | > 30s |
| Token Usage / hora | Audit logs | > 80% limit |
| Error Rate | Structured logs | > 5% |
| Tool Call Success Rate | Agent executor | < 90% |
| Cache Hit Rate | Redis stats | < 50% |
| Active Sessions | Session context | > capacity |
| LLM Quality Score | Quality scorer | < 60 |

---

## 11. Camada 9: Documentacao

| Documento | Status | Responsavel |
|---|---|---|
| **API Reference (OpenAPI)** | Auto-gerado (FastAPI) | Equipe Dev |
| **Manual do Usuario** | A criar | Produto |
| **Guia de Administracao** | A criar | Produto |
| **SLA Document** | A criar | Comercial |
| **Politica de Seguranca** | A criar | Compliance |
| **Politica de Privacidade (LGPD)** | A criar | Juridico |
| **Termos de Uso** | A criar | Juridico |
| **Runbook Operacional** | A criar | SRE |
| **Architecture Decision Records** | Existente (docs/adr/) | Equipe Dev |
| **PRD Revisado** | Existente (docs/PRD-REVISADO.md) | Produto |

---

## 12. Camada 10: Experiencia do Cliente

### 12.1 Onboarding Flow

```
1. Cadastro (email/Google/Microsoft)
     |
2. Criar Organizacao (nome, segmento, tamanho)
     |
3. Wizard de Configuracao
     |-- Conectar GLPI (URL + token)
     |-- Conectar Zabbix (URL + API key)
     |-- Conectar Linear (OAuth)
     |
4. Upload Base de Conhecimento (opcional)
     |-- Arrastar PDFs, MDs
     |-- Selecionar dominio
     |
5. Primeiro Chat Guiado
     |-- "Quais alertas criticos no Zabbix?"
     |-- "Liste ultimos 5 tickets GLPI"
     |
6. Convidar Equipe (emails)
```

### 12.2 Self-Service

| Feature | Descricao |
|---|---|
| **Tutorial Interativo** | Tour guiado no primeiro acesso |
| **Base de Ajuda** | Knowledge base com busca |
| **Chat de Suporte** | Widget integrado (proprio VSA) |
| **Status Page** | Uptime, incidentes, manutencoes |
| **Changelog** | Novidades e atualizacoes |
| **Community Forum** | Troca de experiencias entre clientes |

---

## 13. Camada 11: Arquitetura Escalavel

### 13.1 Infraestrutura

```yaml
# docker-compose.production.yml
services:
  frontend:
    image: nexus-frontend:latest
    replicas: 2

  api:
    image: nexus-api:latest
    replicas: 3

  worker:
    image: nexus-worker:latest  # Celery (ja existe core/celery_app.py)
    replicas: 2

  postgres:
    image: pgvector/pgvector:pg16
    volumes: [pgdata:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine

  minio:
    image: minio/minio:latest

  nginx:
    image: nginx:alpine
    # TLS termination, rate limiting, WAF
```

### 13.2 CI/CD

```yaml
# .github/workflows/deploy.yml
stages:
  - lint (ruff check + mypy)
  - test (pytest --cov)
  - build (Docker multi-stage)
  - staging (auto-deploy on PR merge)
  - production (manual approval + canary)

environments:
  - development (local Docker Compose)
  - staging (Kubernetes/Docker Swarm)
  - production (Kubernetes + monitoring)
```

### 13.3 Versionamento de API

```
/api/v1/*  ->  Versao atual (estavel)
/api/v2/*  ->  Proxima versao (preview)

Politica: v1 suportada por 12 meses apos lancamento v2
Headers: X-API-Version, Deprecation warnings
```

---

## 14. Camada 12: Diferenciais Competitivos

### 14.1 vs Chatbots Genericos (ChatGPT, Gemini)

| Aspecto | Chatbot Generico | VSA NEXUS AI |
|---|---|---|
| Integracoes ITSM | Nenhuma nativa | GLPI, Zabbix, Linear nativos |
| Metodologia ITIL | Nao | Classificacao + GUT + RCA automaticos |
| Multi-Tenant | Nao | Isolamento total por org |
| Auditoria | Basica | Audit trail completo (quem, o que, quando, custo) |
| Controle de Custos | Opaco | Transparente por modelo/agente/usuario |
| RAG Governado | Upload generico | Domain-based, schema whitelist, semantic layer |
| Dry-Run Safety | Nao | Todas WRITE operations com confirmacao |

### 14.2 vs Plataformas de IA Enterprise (ServiceNow, BMC)

| Aspecto | Enterprise Legacy | VSA NEXUS AI |
|---|---|---|
| Custo de Implantacao | R$ 500K+ | R$ 4.997/mes (Enterprise) |
| Time to Value | 6-12 meses | 1-2 semanas |
| Modelos de IA | Proprietario locked-in | Multi-model (OpenRouter), sem lock-in |
| Customizacao | Consultoria cara | Self-service + admin panel |
| Stack | Monolitico | API-First, microservices |

### 14.3 Funcionalidades Unicas do NEXUS

1. **Router Rule-Based Zero-Token** - Relatorios comuns sem custo de LLM (ja implementado)
2. **Tiered Model Strategy** - Fast para classificacao, Smart para analise, Premium para critico
3. **A/B de Modelos** - Compare qualidade entre modelos por custo
4. **Logs Auditaveis de Prompts** - Cada interacao com modelo rastreavel
5. **Domain-Based Access Control** - Acesso RAG por dominio de conhecimento
6. **Correlacao Multi-Sistema** - GLPI + Zabbix + Linear em uma unica analise
7. **GUT Score Automatico** - Priorizacao quantitativa, nao subjetiva

---

## 15. Roadmap de Implementacao

### Onda 1: Fundacao Enterprise (Semanas 1-4)

| # | Tarefa | Complexidade | Base Existente |
|---|---|---|---|
| 1.1 | Schema `organizations` + migracao users | Media | `sql/kb/11_users_table.sql` |
| 1.2 | RBAC middleware (roles no JWT) | Media | `api/middleware/auth.py` |
| 1.3 | RLS policies para multi-tenant | Media | `kb_docs.empresa` ja existe |
| 1.4 | Audit log service + tabela | Media | `core/notifications.py` pattern |
| 1.5 | Admin panel basico (usuarios, org) | Alta | Frontend Next.js existente |
| 1.6 | OAuth2 Google/Microsoft | Media | `api/routes/auth.py` |

### Onda 2: RAG Governance + IA (Semanas 5-8)

| # | Tarefa | Complexidade | Base Existente |
|---|---|---|---|
| 2.1 | Knowledge Domains + domain isolation | Alta | `core/rag/ingestion.py` |
| 2.2 | Ativar ITIL no chat (enable_itil=True) | Baixa | `UnifiedAgent` pronto |
| 2.3 | Confirmer node para WRITE ops | Media | `UnifiedAgentState.pending_confirmation` |
| 2.4 | Reflector node (replan loop) | Media | LangGraph conditional edges |
| 2.5 | Data Catalog + schema whitelist | Alta | Novo |
| 2.6 | Quality Scorer baseline | Media | Novo |

### Onda 3: Billing + Intergacoes (Semanas 9-12)

| # | Tarefa | Complexidade | Base Existente |
|---|---|---|---|
| 3.1 | Billing engine (Stripe/Asaas) | Alta | Novo |
| 3.2 | Rate limiting por plano | Baixa | Redis ja existe |
| 3.3 | Token usage tracking | Media | Audit logs |
| 3.4 | Proxmox integration | Media | Pattern de GLPI/Zabbix |
| 3.5 | WhatsApp via Zigchat | Alta | Projeto Agent WhatsApp |
| 3.6 | Dashboard executivo completo | Alta | `core/reports/dashboard.py` |

### Onda 4: Governance + Scale (Semanas 13-16)

| # | Tarefa | Complexidade | Base Existente |
|---|---|---|---|
| 4.1 | LGPD compliance features | Media | Novo |
| 4.2 | SAML 2.0 / OIDC | Alta | Novo |
| 4.3 | A/B testing de modelos | Media | Quality Scorer |
| 4.4 | Prometheus + Grafana | Media | `/health` ja existe |
| 4.5 | CI/CD pipeline completo | Media | Makefile existente |
| 4.6 | Documentacao publica | Media | OpenAPI auto-gerado |

---

## 16. Metricas de Sucesso

### KPIs de Produto

| Metrica | Target v1.0 | Target v2.0 |
|---|---|---|
| Tempo diagnostico medio | < 15 min (-60%) | < 10 min (-78%) |
| NPS de clareza | > 8 | > 9 |
| Aderencia ITIL | 100% | 100% |
| Integracoes ativas | 5+ | 10+ |
| Uptime | 99% | 99.9% |
| Token waste ratio | < 20% | < 10% |

### KPIs de Negocio

| Metrica | 6 meses | 12 meses | 24 meses |
|---|---|---|---|
| MRR | R$ 15K | R$ 80K | R$ 300K |
| Clientes pagantes | 10 | 40 | 100 |
| Churn mensal | < 10% | < 5% | < 3% |
| CAC | R$ 2.000 | R$ 1.500 | R$ 1.000 |
| LTV/CAC | > 3x | > 5x | > 8x |

---

## 17. Checklist Enterprise-Ready

| Requisito | Status | Onda |
|---|---|---|
| Multi-Tenant | A implementar | 1 |
| RBAC Completo | A implementar | 1 |
| Auditoria Estruturada | A implementar | 1 |
| Billing/Subscricao | A implementar | 3 |
| Seguranca Forte (HTTPS, HSTS, CSP) | Parcial | 1-2 |
| Monitoramento (Prometheus, LangSmith) | Parcial | 4 |
| API Documentada (OpenAPI) | Existente | - |
| Dashboard Executivo | Parcial (reports) | 3 |
| SLA Definido | A criar | 4 |
| Politica LGPD | A criar | 4 |
| OAuth/SSO | A implementar | 1 |
| Rate Limiting | A implementar | 3 |
| Backup/DR | A implementar | 2 |
| CI/CD | Parcial | 4 |

**Score Atual: 3/14 completos (21%)**
**Score pos-Onda 1: 7/14 (50%)**
**Score pos-Onda 4: 14/14 (100%)**

---

## 18. Investimento Estimado

### Equipe Minima (16 semanas)

| Role | Dedicacao | Custo/mes |
|---|---|---|
| Backend Senior (Python/FastAPI) | Full-time | R$ 18.000 |
| Frontend Senior (Next.js/React) | Full-time | R$ 16.000 |
| DevOps/SRE | Part-time | R$ 9.000 |
| Product Manager | Part-time | R$ 10.000 |
| **Total Equipe** | | **R$ 53.000/mes** |

### Infraestrutura

| Item | Custo/mes |
|---|---|
| Cloud (VPS, DB, Redis) | R$ 2.500 |
| OpenRouter (LLM tokens) | R$ 3.000 |
| LangSmith (tracing) | R$ 500 |
| Dominio + SSL | R$ 100 |
| Ferramentas Dev | R$ 1.000 |
| **Total Infra** | **R$ 7.100/mes** |

### Total 16 Semanas (4 Ondas)

| Item | Total |
|---|---|
| Equipe (4 meses) | R$ 212.000 |
| Infra (4 meses) | R$ 28.400 |
| Buffer (20%) | R$ 48.080 |
| **Total Investimento** | **R$ 288.480** |

**Break-even estimado:** 20 clientes Professional (R$ 1.497 x 20 = R$ 29.940 MRR)
**Timeline break-even:** ~12 meses pos-lancamento

---

## Anexo A: Design System Tokens (Obsidian v2.0)

Conforme documentado no HTML do Design System:

| Token | Valor | Uso |
|---|---|---|
| `obsidian-950` | `#050505` | Deep Void (fundo principal) |
| `obsidian-900` | `#0a0a0a` | Gradient end |
| `obsidian-800` | `#121212` | Surface |
| `brand-primary` | `#F97316` | Tech Orange (acao, energia) |
| `brand-secondary` | `#3B82F6` | Deep Blue (confianca, tech) |
| `brand-dark` | `#9a3412` | Orange profundo |
| `glass-panel` | `rgba(255,255,255,0.03)` | Glassmorphism V3 |
| `glow-brand` | `0 0 40px -10px rgba(249,115,22,0.4)` | Neon glow laranja |
| `glow-blue` | `0 0 40px -10px rgba(59,130,246,0.4)` | Neon glow azul |
| Font UI | `Inter` | 300-700 weights |
| Font Code | `JetBrains Mono` | 400-500 weights |

---

## Anexo B: Mapa de Evolucao de Arquivos

Arquivos existentes que precisam ser modificados:

| Arquivo | Modificacao |
|---|---|
| `sql/kb/11_users_table.sql` | Adicionar org_id, role, status, MFA fields |
| `core/auth.py` | Adicionar refresh token, OAuth2 providers |
| `core/database.py` | Adicionar `set_tenant_context()` para RLS |
| `api/middleware/auth.py` | Adicionar RBAC validation, rate limiting |
| `api/routes/auth.py` | Adicionar OAuth endpoints, invite flow |
| `api/routes/chat.py` | Integrar audit logging, ativar enable_itil |
| `core/agents/unified.py` | Implementar Confirmer + Reflector nodes |
| `core/config.py` | Adicionar settings de billing, audit, LGPD |
| `api/main.py` | Adicionar routers admin, billing, audit |
| `core/rag/ingestion.py` | Adicionar domain isolation filter |

Arquivos NOVOS necessarios:

| Arquivo | Funcao |
|---|---|
| `core/audit.py` | Audit service |
| `core/billing.py` | Billing engine |
| `core/quality.py` | Quality scorer |
| `api/routes/admin.py` | Admin panel endpoints |
| `api/routes/billing.py` | Billing endpoints |
| `api/routes/audit.py` | Audit endpoints |
| `api/models/admin.py` | Admin Pydantic models |
| `sql/kb/12_organizations.sql` | Multi-tenant schema |
| `sql/kb/13_audit_logs.sql` | Audit logs schema |
| `sql/kb/14_billing.sql` | Billing schema |
| `frontend/src/app/admin/` | Admin panel pages |

---

> **Documento vivo.** Atualizado conforme evolucao do produto.
> **Proximo passo:** Validar Onda 1 com stakeholders e iniciar sprint de fundacao.
