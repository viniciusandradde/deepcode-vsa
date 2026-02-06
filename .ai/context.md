# DeepCode VSA - Contexto do Projeto

**Produto:** DeepCode VSA (Virtual Support Agent)
**Empresa:** VSA Tecnologia
**Versao do Contexto:** 2.0.0
**Ultima Atualizacao:** 2026-02-06

---

## 1. Visao Geral

O **DeepCode VSA** e um agente virtual inteligente para gestao de TI, com interface **Chat-First** (web). Conecta-se a multiplos sistemas de TI (GLPI, Zabbix, Linear) para analisar dados operacionais, correlacionar informacoes entre sistemas heterogeneos, priorizar demandas usando metodologias ITIL e apoiar decisoes estrategicas.

### Proposta de Valor
> Transformar dados dispersos de APIs em decisoes inteligentes de gestao, reduzindo o tempo de diagnostico e aumentando a maturidade operacional de TI.

### Publico-Alvo
- **Primario:** Gestores de TI, Coordenadores de Infra/NOC, Analistas de Service Desk
- **Secundario:** MSPs, TI Hospitalar, TI Educacional, TI Corporativa

### Status Atual (Fevereiro 2026)
- **Fase:** MVP v1.0 em desenvolvimento (Q1 2026)
- **Interface primaria:** Chat web (Next.js 15 + React 19)
- **Backend:** FastAPI com streaming SSE
- **Agente principal:** UnifiedAgent (Router-Classifier-Planner-Executor)

---

## 2. Arquitetura Atual

```
                    USUARIOS
    Gestores TI | Analistas NOC | Service Desk
                       |
                       v
    +------------------------------------------+
    |      Frontend (Next.js 15 + React 19)    |
    |  ChatPane | Sidebar | Settings | Planning |
    |  Automation Scheduler | Streaming SSE     |
    +--------------------+---------------------+
                         |
                         v
    +------------------------------------------+
    |         Backend (FastAPI + Python 3.11)   |
    |                                          |
    |  /api/v1/chat        - Chat sync         |
    |  /api/v1/chat/stream - Chat SSE          |
    |  /api/v1/rag/*       - RAG search/ingest |
    |  /api/v1/agents/*    - Agent management  |
    |  /api/v1/planning/*  - Project planning  |
    |  /api/v1/automation/*- Task scheduler    |
    +--------------------+---------------------+
                         |
                         v
    +------------------------------------------+
    |     UnifiedAgent (LangGraph StateGraph)   |
    |                                          |
    |  Router -> Classifier -> Planner ->       |
    |  Confirmer -> Executor                    |
    |                                          |
    |  Intents: CONVERSA_GERAL, IT_REQUEST,    |
    |           MULTI_ACTION                    |
    |                                          |
    |  ITIL: Incident, Problem, Change,        |
    |        Request, Chat                      |
    +----+-----------+------------+------------+
         |           |            |
         v           v            v
    +----------+ +----------+ +----------+
    |   GLPI   | |  Zabbix  | |  Linear  |
    |  Tickets | |  Alerts  | |  Issues  |
    |  REST    | |  JSONRPC | |  GraphQL |
    +----------+ +----------+ +----------+
         |           |            |
         v           v            v
    +------------------------------------------+
    |   PostgreSQL 16 + pgvector               |
    |   RAG | Checkpoints | Planning | Threads |
    +------------------------------------------+
```

---

## 3. Stack Tecnologico

### Backend
- **Runtime:** Python 3.11+
- **Framework:** FastAPI
- **IA/Agentes:** LangChain + LangGraph (StateGraph)
- **LLM:** Multi-model via OpenRouter
  - FAST: meta-llama/llama-3.3-70b-instruct
  - SMART: deepseek/deepseek-chat
  - PREMIUM: anthropic/claude-3.5-sonnet
  - CREATIVE: minimax/minimax-m2-her
- **RAG:** pgvector (hybrid search + HyDE + RRF)
- **Scheduler:** APScheduler + Celery

### Frontend
- **Framework:** Next.js 15 + React 19
- **Estado:** Context API (useGenesisUI)
- **UI:** Tailwind CSS
- **Streaming:** SSE (Server-Sent Events)

### Banco de Dados
- **PostgreSQL 16** + pgvector extension
- Schemas: RAG (kb_docs, kb_chunks), Planning, Threads, Automation
- 9 arquivos SQL em `sql/kb/` (01 a 09)

### Integracoes Ativas
| Integracao | Status | Protocolo | Uso |
|------------|--------|-----------|-----|
| GLPI | Pendente (falta User Token) | REST API | Tickets ITSM |
| Zabbix | Funcionando | JSON-RPC | Alertas/Monitoramento |
| Linear | Funcionando | GraphQL | Issues/Projetos |
| OpenRouter | Funcionando | REST | Multi-LLM |

---

## 4. Componentes Implementados

### 4.1 Chat Web (Interface Primaria)
- Chat com streaming SSE em tempo real
- Gerenciamento de sessoes (localStorage + API)
- Sidebar com historico de conversas
- Painel de configuracoes (toggles de integracoes)
- Suporte multi-modelo via OpenRouter
- Componentes: ChatPane, MessageItem, MessageInput, Sidebar, SettingsPanel

### 4.2 Agentes
- **UnifiedAgent** (`core/agents/unified.py`): Agente principal em uso
  - Router: classificacao de intent (conversa_geral, it_request, multi_action)
  - Classifier: categorizacao ITIL (Incident, Problem, Change, Request, Chat)
  - Planner: planejamento multi-step com LLM
  - Confirmer: confirmacao para operacoes WRITE
  - Executor: execucao de tools
- **SimpleAgent** (`core/agents/simple.py`): Agente basico funcional
- **PlanningAgent** (`core/agents/planning.py`): Analise de documentos (estilo NotebookLM)
- **VSAAgent** (`core/agents/vsa.py`): Implementado mas nao integrado ao chat

### 4.3 Tools (LangChain)
- `core/tools/glpi.py` - get_tickets, get_ticket_details, create_ticket
- `core/tools/zabbix.py` - get_alerts, get_host
- `core/tools/linear.py` - get/create issues, get_teams, add_comment, create_project
- `core/tools/planning.py` - Tools de planejamento para chat
- `core/tools/search.py` - RAG search

### 4.4 Planning (NotebookLM-like)
- CRUD de projetos com upload de documentos (PDF, MD, TXT)
- Analise com IA (Gemini)
- Etapas e orcamento sugeridos
- Sincronizacao com Linear
- Frontend: `/planning` e `/planning/[id]`

### 4.5 Automation Scheduler
- Agendamento de tarefas com CRON
- Execucao imediata
- Monitoramento de tasks
- Frontend: `/automation`
- APScheduler + Celery no backend

### 4.6 RAG Pipeline
- 3 estrategias de chunking: fixed-size, markdown-aware, semantic
- Hybrid search: vector + text + RRF
- HyDE (Hypothetical Document Embeddings)
- Multi-tenancy via tenant_id/empresa
- Reranking opcional (Cohere)

---

## 5. Estrutura de Diretorios (Real)

```
deepcode-vsa/
├── .agent/                    # Skills, agents, workflows (40 skills, 21 agents)
│   ├── rules/GEMINI.md        # Master config Antigravity
│   ├── agents/                # 21 agent definitions
│   ├── skills/                # 40 skills com SKILL.md
│   ├── workflows/             # 12 workflows
│   └── scripts/               # Automacao (verify, checklist)
│
├── .ai/                       # Contexto multi-IDE (ESTE DIRETORIO)
│   ├── context.md             # Este arquivo
│   ├── progress.md            # Log de sessoes
│   ├── handoff.md             # Passagem de bastao
│   ├── orchestration.md       # Protocolo multi-IDE
│   ├── skills/                # 8 skills hospital-especificas
│   ├── agents/                # 8 agentes hospitalares
│   └── ide-configs/           # Configs por IDE
│
├── api/                       # FastAPI REST API
│   ├── main.py                # Entry point
│   ├── routes/
│   │   ├── chat.py            # Chat (sync + streaming SSE)
│   │   ├── rag.py             # RAG search/ingestion
│   │   ├── agents.py          # Agent management
│   │   ├── planning.py        # Project planning
│   │   ├── automation.py      # Task scheduler
│   │   ├── threads.py         # Thread management
│   │   └── reports.py         # Reports
│   └── models/                # Pydantic models
│
├── core/                      # Business logic
│   ├── agents/
│   │   ├── unified.py         # UnifiedAgent (PRINCIPAL)
│   │   ├── simple.py          # SimpleAgent
│   │   ├── planning.py        # PlanningAgent
│   │   └── vsa.py             # VSAAgent (nao integrado)
│   ├── integrations/
│   │   ├── glpi_client.py     # GLPI REST
│   │   ├── zabbix_client.py   # Zabbix JSON-RPC
│   │   └── linear_client.py   # Linear GraphQL
│   ├── tools/                 # LangChain tools
│   ├── rag/                   # RAG pipeline
│   ├── middleware/             # Dynamic config
│   └── config.py              # Pydantic settings
│
├── frontend/                  # Next.js 15 + React 19
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx           # Chat principal
│   │   │   ├── planning/          # Modulo planejamento
│   │   │   ├── automation/        # Modulo scheduler
│   │   │   └── api/               # Route handlers
│   │   ├── components/app/        # 20+ componentes
│   │   └── state/useGenesisUI.tsx # State management
│   └── next.config.ts
│
├── backend/                   # LangGraph Studio config
│   └── langgraph.json
│
├── sql/kb/                    # Database schemas (01-09)
├── docs/                      # Documentacao (projeto/, status/, RAG/, setup/)
├── CLAUDE.md                  # Instrucoes Claude Code
├── Makefile                   # Comandos de desenvolvimento
└── pyproject.toml             # Python project metadata
```

---

## 6. Governanca e Seguranca

### Execucao Segura (ADR-007)
- `dry_run=True` por padrao para TODAS as operacoes WRITE
- Confirmacao explicita necessaria para criacao/modificacao
- DELETE bloqueado na v1.0
- READ automatico com credenciais validas

### Audit Trail
Todas as operacoes logadas em JSON estruturado com:
timestamp, user, operation, target, data, dry_run, result, explanation

### Modelo de Permissao
| Operacao | Comportamento | Requisitos |
|----------|---------------|------------|
| READ | Execucao automatica | Credenciais API validas |
| WRITE | Requer confirmacao | dry_run + aprovacao explicita |
| DELETE | Bloqueado v1.0 | Nao disponivel |

---

## 7. Variaveis de Ambiente

```env
# PostgreSQL (pgvector)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=deepcode_vsa
DB_USER=postgres
DB_PASSWORD=

# LLM (OpenRouter)
OPENROUTER_API_KEY=sk-or-...

# GLPI
GLPI_ENABLED=true
GLPI_BASE_URL=https://your-glpi.com/apirest.php
GLPI_APP_TOKEN=
GLPI_USER_TOKEN=          # PENDENTE

# Zabbix
ZABBIX_ENABLED=true
ZABBIX_BASE_URL=https://your-zabbix.com/api_jsonrpc.php
ZABBIX_API_TOKEN=

# Linear
LINEAR_ENABLED=true
LINEAR_API_KEY=lin_api_...

# LangSmith (opcional)
LANGCHAIN_API_KEY=
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=deepcode-vsa
```

---

## 8. Comandos de Desenvolvimento

```bash
# Backend
make dev                    # FastAPI na porta 8000
uvicorn api.main:app --reload --port 8000

# Frontend
make frontend               # Next.js na porta 3000
cd frontend && npm run dev

# LangGraph Studio
make studio                 # Debug visual de agentes
cd backend && langgraph dev

# Testes
make test                   # Todos os testes
pytest tests/unit/ -v       # Unit tests
pytest tests/integration/ -v # Integration tests

# Qualidade
ruff check .                # Lint
ruff format .               # Format
mypy core/ api/             # Type checking

# Database
make setup-db               # Setup PostgreSQL + pgvector
make setup-planning-db      # Schema de planning
```

---

## 9. Relacao .ai/ e .agent/

Este diretorio (`.ai/`) contem contexto de alto nivel para coordenacao multi-IDE.
O diretorio `.agent/` contem a base de skills e agents operacionais.

| Diretorio | Proposito | Conteudo |
|-----------|-----------|----------|
| `.ai/` | Contexto multi-IDE, orquestracao | context, progress, handoff, orchestration |
| `.ai/skills/` | Skills hospital-especificas (VSA Analytics Health) | 8 skills |
| `.ai/agents/` | Agentes hospitalares (WhatsApp, triagem) | 8 agents |
| `.agent/` | Skills/agents de desenvolvimento (Antigravity native) | 40 skills, 21 agents |
| `.agent/rules/` | Master config (GEMINI.md) | Tier 0/1/2, routing |
| `.agent/workflows/` | Workflows orquestrados | 12 workflows |

**Fonte da verdade para desenvolvimento:** `.agent/`
**Fonte da verdade para contexto do projeto:** `.ai/context.md` (este arquivo)
