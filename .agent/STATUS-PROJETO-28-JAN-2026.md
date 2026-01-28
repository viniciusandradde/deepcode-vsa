# Status do Projeto DeepCode VSA - 28 Janeiro 2026

**Data:** 2026-01-28
**Branch:** main
**Último Commit:** 09bf0d4 - "refactor: Improve thread archiving and sidebar session management"

---

## 📊 Visão Geral

### Estatísticas do Código

| Categoria | Arquivos | Linhas |
|-----------|----------|--------|
| **Backend Python (core/api)** | 37 | 5,487 |
| **Frontend TypeScript/TSX** | 33 | 5,414 |
| **Total** | **70** | **10,901** |

### Dependências

- **Python:** 16 packages (requirements.txt)
- **Node.js:** 28 packages (frontend/package.json)

---

## 🏗️ Arquitetura Implementada

### Backend (FastAPI + LangGraph)

```
api/
├── main.py                 # FastAPI application + lifespan events
├── models/                 # Pydantic request/response models
│   ├── requests.py
│   └── responses.py
├── routes/                 # API endpoints
│   ├── chat.py            # Chat endpoints (sync + streaming)
│   ├── rag.py             # RAG search/ingestion
│   ├── agents.py          # Agent management
│   └── threads.py         # Thread/session management (NEW)
└── middleware/            # Middleware components

core/
├── agents/                # Agent implementations
│   ├── base.py            # BaseAgent abstract class
│   ├── simple.py          # SimpleAgent (LangChain create_agent)
│   ├── workflow.py        # WorkflowAgent (intent detection)
│   ├── unified.py         # UnifiedAgent (Router + ITIL + Planner)
│   └── vsa.py             # VSAAgent (deprecated - migrated to unified)
├── integrations/          # External API clients
│   ├── glpi_client.py     # ✅ GLPI REST API
│   ├── zabbix_client.py   # ✅ Zabbix JSON-RPC API
│   └── linear_client.py   # ✅ Linear.app GraphQL API
├── tools/                 # LangChain tools
│   ├── glpi.py            # ✅ GLPI tools (get_tickets, create_ticket)
│   ├── zabbix.py          # ✅ Zabbix tools (get_alerts, get_host)
│   ├── linear.py          # ✅ Linear tools (get_issues, create_issue)
│   └── search.py          # ✅ Tavily web search
├── rag/                   # RAG pipeline
│   ├── ingestion.py       # Document ingestion + chunking
│   ├── loaders.py         # Document loaders
│   └── tools.py           # RAG search tools
├── middleware/            # Dynamic middleware
│   └── dynamic.py         # DynamicSettingsMiddleware
└── checkpointing.py       # ✅ PostgreSQL checkpoint persistence (FIXED)
```

### Frontend (Next.js 15 + React 19)

```
frontend/src/
├── app/
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Main chat page
│   └── api/               # Next.js API routes (proxy to backend)
│       ├── models/        # Model list endpoint
│       └── threads/       # Thread management endpoints
├── components/
│   ├── app/               # Application components
│   │   ├── ChatPane.tsx   # Main chat interface
│   │   ├── Sidebar.tsx    # Session/model management
│   │   ├── SettingsPanel.tsx  # VSA/GLPI/Zabbix/Linear toggles
│   │   └── ...
│   └── ui/                # UI primitives (shadcn/ui)
│       ├── button.tsx
│       ├── switch.tsx
│       └── ...
├── state/
│   └── useGenesisUI.tsx   # ✅ Global state management (Context API)
└── lib/
    ├── config.ts          # API configuration
    └── storage.ts         # localStorage utilities
```

---

## ✅ Funcionalidades Implementadas

### 1. Chat Multi-Modelo
- ✅ Seleção de modelos via OpenRouter
- ✅ Streaming SSE (Server-Sent Events)
- ✅ Modelo padrão: `google/gemini-2.5-flash`
- ✅ Suporte a múltiplos modelos configuráveis

### 2. Agentes LangGraph
- ✅ **SimpleAgent** - Agente básico com create_agent
- ✅ **WorkflowAgent** - Detecção de intenção
- ✅ **UnifiedAgent** - Router + Classifier + Planner + Executor
- ✅ Sistema de prompt ITIL em português

### 3. Integrações ITSM
- ✅ **GLPI** - Cliente + Tools (tickets, create)
- ✅ **Zabbix** - Cliente + Tools (alerts, hosts)
- ✅ **Linear.app** - Cliente + Tools (issues, teams)
- ✅ **Tavily** - Busca web com IA

### 4. Persistência PostgreSQL
- ✅ **PostgresSaver** (sync) com `row_factory=dict_row`
- ✅ **AsyncPostgresSaver** (async) para endpoints streaming
- ✅ Checkpoints salvos no banco de dados
- ✅ Lifespan events para inicialização correta
- ✅ Tabelas de checkpoint criadas automaticamente

### 5. Gerenciamento de Sessões
- ✅ Criação de sessões (threads)
- ✅ Seleção de sessões
- ✅ Deletar sessões
- ✅ **Recuperação de mensagens do PostgreSQL** (NEW)
- ✅ **Thread archiving** (NEW)
- ✅ Persistência em localStorage

### 6. Interface Web
- ✅ Chat interface com Markdown rendering
- ✅ Tabelas ITIL estruturadas
- ✅ Action Plan component
- ✅ Sidebar com gerenciamento de sessões
- ✅ Settings panel (VSA, GLPI, Zabbix, Linear toggles)
- ✅ Toggles persistem no localStorage (SSR hydration fix)
- ✅ Error translation (mensagens user-friendly)

### 7. Metodologias ITIL
- ✅ Classificação em português (INCIDENTE, PROBLEMA, MUDANÇA, REQUISIÇÃO, CONVERSA)
- ✅ Categorias (Infraestrutura, Rede, Software, Hardware, Segurança)
- ✅ GUT Score (Gravidade × Urgência × Tendência)
- ✅ Plano de ação estruturado
- ✅ Formato de resposta em tabelas Markdown

### 8. MCP Servers (NEW)
- ✅ **15 MCP servers configurados**
- ✅ PostgreSQL (3 databases: homologação, produção, analytics_health)
- ✅ Metabase, Grafana, n8n, Perplexity
- ✅ Supabase, Notion, Vercel, GitHub
- ✅ Context7, Memory server
- ✅ shadcn/ui components

---

## 🐳 Docker Containers

| Container | Status | Image | Porta |
|-----------|--------|-------|-------|
| ai_agent_backend | ✅ Running | deepcode-vsa-backend | 8000 |
| ai_agent_frontend | ✅ Running | deepcode-vsa-frontend | 3000 |
| ai_agent_postgres | ✅ Healthy | pgvector/pgvector:pg16 | 5433 |

**Uptime:** 24+ minutos (backend/postgres), 19+ minutos (frontend)

---

## 📝 Commits Recentes (últimos 20)

```
09bf0d4 refactor: Improve thread archiving and sidebar session management
13c7a7e feat: Adicionar configuração de 15 servidores MCP
2428c69 feat: Enhance Makefile and models.yaml with new commands and model updates
d62c665 refactor: Simplify session loading logic in GenesisUIProvider
93a8bc1 feat: Enhance FastAPI application with threads endpoint and error handling improvements
c7996db fix: Correção completa de persistência PostgreSQL checkpoint
cca28fa feat: Persist Tavily search setting in local storage
6004264 fix: Toggle persistence + MemorySaver (temp) + comprehensive analysis
84bd11e fix: VSA toggles persistence with SSR hydration fix
fb01208 docs: Add 27 Jan project status summary
3842c81 feat: persist VSA integration settings to localStorage
47ccfa6 feat: Add critical anti-hallucination rules to the chat prompt
29c06a5 Refactor: Introduce refs for draft, isLoading, and isSending
21a1e2c feat: Conditionally build router, classifier, and planner nodes
6f34f86 feat: introduce UnifiedAgent for comprehensive IT service management
6030bf5 checkpoint
e9fd68a feat: Translate ITIL terms and categories to Portuguese (Brazil)
cb81935 feat: Introduce Action Plan component and enhance Markdown table rendering
8d7b9d5 feat: Implement AI thinking indicator, structured responses
6a8901f feat: implement message cancellation and update ITIL status docs
```

---

## 🔧 Correções Recentes (28 Jan 2026)

### ✅ Persistência PostgreSQL Checkpoint

**Problema:** Checkpoints não eram salvos devido a:
1. Falta de `row_factory=dict_row` (obrigatório segundo doc oficial)
2. Checkpointer obtido antes da inicialização
3. Uso de sync checkpointer em contexto async

**Solução:**
- ✅ Adicionado `row_factory=dict_row` em conexões sync e async
- ✅ Movido `get_checkpointer()` para dentro das funções
- ✅ Alterado para `get_async_checkpointer()` em endpoints async
- ✅ Logs confirmam: "✅ Sync/Async PostgresSaver initialized with dict_row factory"

**Commit:** c7996db

**Documentação:**
- `.agent/CORRECAO-PERSISTENCIA-POSTGRESQL.md`
- `.agent/RESUMO-EXECUTIVO-PERSISTENCIA.md`
- `.agent/GUIA-TESTE-PERSISTENCIA.md`

### ✅ Recuperação de Mensagens (Thread Management)

**Problema:** Mensagens eram salvas no banco mas não recuperadas ao selecionar sessão

**Solução:**
- ✅ Endpoint `/api/v1/threads` implementado
- ✅ Endpoint `/api/v1/threads/{thread_id}/messages` implementado
- ✅ Frontend carrega mensagens do backend via API
- ✅ Thread archiving implementado

**Commit:** 09bf0d4, 93a8bc1

### ✅ Toggle Persistence (SSR Hydration Fix)

**Problema:** Toggles (VSA, GLPI, Zabbix, Linear, Tavily) perdiam estado ao recarregar página

**Solução:**
- ✅ Refatorado `useLocalStorageState` para lidar com SSR
- ✅ Hidratação de localStorage em `useEffect` (client-only)
- ✅ Adicionado `preventDefault` em todos os switches

**Commits:** 84bd11e, cca28fa

---

## 🚀 Próximas Tarefas

### Prioridade Alta (MVP v1.0)

1. **Testar Persistência Completa**
   - [ ] Atualizar `OPENROUTER_API_KEY` com chave válida
   - [ ] Executar testes do guia `.agent/GUIA-TESTE-PERSISTENCIA.md`
   - [ ] Validar recuperação de contexto entre sessões
   - [ ] Validar persistência após restart do backend

2. **Integrar GLPI/Zabbix ao Chat**
   - [ ] Testar queries GLPI via chat
   - [ ] Testar queries Zabbix via chat
   - [ ] Validar formato ITIL nas respostas

3. **Implementar Planner Node**
   - [ ] UnifiedAgent.planner retorna plano vazio (linha 442)
   - [ ] Implementar lógica de planejamento baseada em ITIL

4. **Implementar Confirmation Node**
   - [ ] Adicionar confirmação para operações WRITE
   - [ ] Validar dry_run mode

### Prioridade Média (v1.1)

5. **Correlação GLPI ↔ Zabbix**
   - [ ] Implementar análise de correlação automática
   - [ ] Timeline de eventos integrada

6. **RCA (Root Cause Analysis)**
   - [ ] Implementar técnica 5 Whys
   - [ ] Gerar relatórios de análise de causa raiz

7. **Otimizar Performance**
   - [ ] Router adiciona 500-800ms de latência (considerar remover para VSA)
   - [ ] Simplificar UnifiedAgentState (remover campos não usados)

### Prioridade Baixa (v2.0)

8. **CLI Interface**
   - [ ] Implementar `deepcode-vsa` CLI (planejado, não iniciado)
   - [ ] Criar package structure `src/deepcode_vsa/`

9. **Auditoria e Compliance**
   - [ ] Dashboard de auditoria no frontend
   - [ ] Export de audit trails
   - [ ] LGPD compliance features

---

## 🗄️ Banco de Dados

### Schemas Criados

```sql
sql/kb/
├── 01_embeddings_schema.sql      # Tabelas kb_docs, kb_chunks (pgvector)
├── 02_search_functions.sql       # Funções hybrid_search, rerank
├── 03_checkpoints_schema.sql     # Tabelas checkpoints, writes (LangGraph)
└── 04_archived_threads.sql       # Tabela archived_threads (NEW)
```

### Tabelas Principais

| Tabela | Descrição | Status |
|--------|-----------|--------|
| `kb_docs` | Documentos RAG | ✅ Criada |
| `kb_chunks` | Chunks com embeddings (pgvector) | ✅ Criada |
| `checkpoints` | Checkpoints LangGraph | ✅ Criada |
| `writes` | Writes LangGraph | ✅ Criada |
| `archived_threads` | Threads arquivadas | ✅ Criada |

---

## 🔐 Segurança e Credenciais

### Arquivos Protegidos (.gitignore)

- ✅ `.env` (credenciais backend)
- ✅ `.claude/mcp.json` (credenciais MCP servers)
- ✅ `.claude/settings.local.json`

### Templates Públicos

- ✅ `.env.example` (template sem credenciais)
- ✅ `.claude/mcp.json.example` (template MCP sem credenciais)

### Credenciais Configuradas

| Sistema | Status | Localização |
|---------|--------|-------------|
| OpenRouter API | ⚠️ Requer atualização | `.env` → `OPENROUTER_API_KEY` |
| PostgreSQL | ✅ Configurado | Docker Compose |
| GLPI | ⚠️ Falta User Token | `.env` → `GLPI_USER_TOKEN` |
| Zabbix | ✅ Configurado | `.env` → `ZABBIX_API_TOKEN` |
| Linear.app | ✅ Configurado | `.env` → `LINEAR_API_KEY` |
| Tavily | ✅ Configurado | `.env` → `TAVILY_API_KEY` |

**Ações necessárias:**
1. Atualizar `OPENROUTER_API_KEY` (chave atual retorna 401)
2. Obter `GLPI_USER_TOKEN` válido (ver `STATUS-INTEGRACOES.md`)

---

## 📚 Documentação Gerada

### Documentação Técnica

| Arquivo | Descrição |
|---------|-----------|
| `CLAUDE.md` | Instruções para Claude Code (projeto overview) |
| `.agent/CORRECAO-PERSISTENCIA-POSTGRESQL.md` | Correção completa de persistência (477 linhas) |
| `.agent/RESUMO-EXECUTIVO-PERSISTENCIA.md` | Resumo executivo para gestão |
| `.agent/GUIA-TESTE-PERSISTENCIA.md` | Guia passo a passo para testes |
| `.agent/MCP-SERVERS-CONFIGURADOS.md` | Documentação dos 15 MCP servers |
| `.agent/ANALISE-UNIFIED-AGENT-PERFORMANCE.md` | Análise de desempenho do UnifiedAgent |
| `STATUS-INTEGRACOES.md` | Status das integrações (GLPI, Zabbix, Linear) |
| `docs/PRD-REVISADO.md` | PRD revisado (Chat-First approach) |
| `docs/INTEGRACAO-METODOLOGIAS-CHAT.md` | Guia de integração ITIL |

### Skills (Claude Code)

| Skill | Descrição |
|-------|-----------|
| `vsa-development` | Patterns gerais de desenvolvimento VSA |
| `vsa-agent-state` | State management patterns |
| `vsa-methodologies` | ITIL, GUT, RCA, 5W2H |
| `vsa-llm-config` | Hybrid LLM model selection |
| `vsa-safety-tools` | Computer Use safety patterns |
| `vsa-external-integrations` | Linear, Telegram integrations |
| `glpi-integration` | GLPI ITSM patterns |
| `zabbix-integration` | Zabbix monitoring patterns |
| `langgraph-agent` | LangGraph orchestration |
| `api-patterns` | Python async API patterns |
| `python-async` | Async/await best practices |

---

## 🌐 Repositório Git

### Status Atual

- **Branch:** main
- **Remote:** ⚠️ Nenhum remote configurado
- **Commits:** 20+ commits recentes
- **Working Tree:** ✅ Clean (nada para commitar)

### Configurar Repositório GitHub

Para adicionar repositório remoto:

```bash
# 1. Criar repositório no GitHub
# 2. Adicionar remote
git remote add origin https://github.com/USER/deepcode-vsa.git

# 3. Push inicial
git push -u origin main

# 4. Configurar branch tracking
git branch --set-upstream-to=origin/main main
```

---

## 🎯 Métricas de Progresso

### MVP v1.0 (Target: Q1 2026)

| Feature | Status | Progresso |
|---------|--------|-----------|
| Chat Multi-Modelo | ✅ Completo | 100% |
| Streaming SSE | ✅ Completo | 100% |
| Persistência PostgreSQL | ✅ Completo | 100% |
| GLPI Integration | ✅ Implementado | 90% (falta User Token) |
| Zabbix Integration | ✅ Implementado | 100% |
| Linear Integration | ✅ Implementado | 100% |
| ITIL Classification | ✅ Implementado | 100% |
| GUT Prioritization | 🟡 Parcial | 60% (no prompt, falta cálculo) |
| Planner Node | ❌ Vazio | 10% |
| Confirmation Node | ❌ Não iniciado | 0% |
| GLPI ↔ Zabbix Correlation | ❌ Não iniciado | 0% |
| RCA (5 Whys) | ❌ Não iniciado | 0% |

**Progresso Geral MVP v1.0:** ~65%

---

## 🔥 Issues Conhecidos

### 1. OpenRouter API Key Inválida

**Sintoma:** `Error code: 401 - {'error': {'message': 'User not found.', 'code': 401}}`

**Solução:** Atualizar `OPENROUTER_API_KEY` no `.env`

**Prioridade:** 🔴 ALTA (bloqueia testes)

### 2. GLPI User Token Faltando

**Sintoma:** GLPI tools podem falhar se User Token não estiver configurado

**Solução:** Obter token em https://glpi.hospitalevangelico.com.br

**Prioridade:** 🟡 MÉDIA

### 3. Planner Node Retorna Plano Vazio

**Arquivo:** `core/agents/unified.py:442`

**Sintoma:** Planner sempre retorna `{"plan": [], "current_step": 0}`

**Solução:** Implementar lógica de planejamento

**Prioridade:** 🟡 MÉDIA

### 4. Router Adiciona Latência

**Sintoma:** Router node adiciona 500-800ms de latência desnecessária para VSA

**Solução:** Considerar bypass do router quando `enable_vsa=True`

**Prioridade:** 🟢 BAIXA (otimização)

---

## 📞 Suporte e Contato

**Projeto:** DeepCode VSA (Virtual Support Agent)
**Equipe:** VSA Tecnologia
**Instituição:** Hospital Evangélico

**Documentação:**
- Projeto: `/home/projects/agentes-ai/deepcode-vsa/`
- Status: `.agent/STATUS-PROJETO-28-JAN-2026.md` (este arquivo)
- PRD: `docs/PRD-REVISADO.md`

**Recursos:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- PostgreSQL: localhost:5433

---

**Última atualização:** 2026-01-28 12:50 UTC
**Próxima revisão:** Após resolver OpenRouter API Key e completar testes de persistência
