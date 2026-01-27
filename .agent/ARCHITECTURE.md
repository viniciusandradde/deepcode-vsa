# DeepCode VSA - Architecture & Checkpoint

> **Checkpoint Date:** 27/01/2026
> **Version:** 4.0
> **Status:** ✅ All Integrations Operational

---

## 🎯 Current Project: DeepCode VSA

**Virtual Support Agent** - Agente de Chat Inteligente para Gestão de TI

| Aspecto | Detalhe |
|---------|---------|
| **Stack** | Python 3.11+, FastAPI, LangGraph, Next.js 15, OpenRouter |
| **Arquitetura** | SimpleAgent → VSAAgent (futuro: Planner-Executor-Reflector) |
| **Integrações** | GLPI ✅, Zabbix ✅, Linear ✅ |
| **Modelo Padrão** | `x-ai/grok-4.1-fast` |
| **Deploy** | Docker Compose (backend + frontend + postgres) |

---

## 📁 Project Structure

```plaintext
deepcode-vsa/
├── .agent/                    # Agent configs, skills, workflows
├── api/                       # FastAPI REST API
│   ├── main.py               # App entry point
│   ├── routes/
│   │   ├── chat.py           # /api/v1/chat + /stream ⭐
│   │   ├── rag.py            # /api/v1/rag
│   │   └── agents.py         # /api/v1/agents
│   └── models/
│       ├── requests.py       # ChatRequest (w/ VSA flags)
│       └── responses.py      # ChatResponse
├── core/                      # Business logic
│   ├── agents/
│   │   ├── simple.py         # SimpleAgent (active)
│   │   ├── vsa.py            # VSAAgent (Phase 2)
│   │   └── workflow.py       # WorkflowAgent
│   ├── tools/                # LangChain Tools
│   │   ├── glpi.py           # glpi_get_tickets, glpi_create_ticket
│   │   ├── zabbix.py         # zabbix_get_alerts, zabbix_get_host
│   │   ├── linear.py         # linear_get_issues, linear_create_issue
│   │   └── search.py         # tavily_search
│   ├── integrations/          # API Clients
│   │   ├── glpi_client.py    # GLPIClient (Basic Auth)
│   │   ├── zabbix_client.py  # ZabbixClient (API Token)
│   │   └── linear_client.py  # LinearClient (API Key)
│   └── config.py             # Settings (Pydantic)
├── frontend/                  # Next.js 15 App
│   ├── src/
│   │   ├── app/              # App Router
│   │   │   └── api/threads/  # API Routes (proxy to backend)
│   │   ├── components/app/
│   │   │   ├── ChatPane.tsx  # Main chat component
│   │   │   ├── SettingsPanel.tsx # VSA toggles ⭐
│   │   │   └── Sidebar.tsx   # Session management
│   │   └── state/
│   │       └── useGenesisUI.tsx # Global state (VSA flags)
│   └── models.yaml           # Available models
├── docs/                      # Documentation
│   ├── PRD-REVISADO.md       # Product Requirements
│   ├── INTEGRACAO-METODOLOGIAS-CHAT.md # Integration guide
│   └── adr/                  # Architecture Decision Records
├── scripts/                   # Utility scripts
│   └── test_integrations.py  # Integration test script
└── docker-compose.yml        # Docker deployment
```

---

## 🔧 Current Implementation Status

### Phase 1: Chat with Integrations ✅

| Task | Status | Description |
|------|--------|-------------|
| 1.1 | ✅ | Dynamic tools in chat.py |
| 1.2 | ✅ | GLPI toggle in SettingsPanel |
| 1.3 | ✅ | Zabbix toggle in SettingsPanel |
| 1.4 | ✅ | Test GLPI queries |
| 1.5 | ✅ | Test Zabbix queries |

### Phase 2: ITIL Methodologies (Pending)

| Task | Status | Description |
|------|--------|-------------|
| 2.1 | 🔲 | VSAAgent integration |
| 2.2 | 🔲 | Classifier Node |
| 2.3 | 🔲 | ITILBadge.tsx |
| 2.4 | 🔲 | GUT Score calculation |

### Phase 3-4: Correlation & Governance (Future)

---

## 🔌 Integration Details

### GLPI - IT Service Management

- **URL:** `https://glpi.hospitalevangelico.com.br/glpi/apirest.php`
- **Auth:** Basic Auth (Username + Password)
- **App Token:** Configured in `.env`
- **Tools:** `glpi_get_tickets`, `glpi_get_ticket_details`, `glpi_create_ticket`

### Zabbix - Monitoring

- **URL:** `https://zabbix.hospitalevangelico.com.br`
- **Auth:** API Token
- **Tools:** `zabbix_get_alerts`, `zabbix_get_host`

### Linear - Project Management

- **URL:** GraphQL API
- **Auth:** API Key
- **Team:** VSA Tecnologia
- **Tools:** `linear_get_issues`, `linear_get_issue`, `linear_create_issue`, `linear_get_teams`

---

## 🔄 Data Flow

```
User → Frontend (Next.js)
         ↓
    /api/threads/{id}/messages/stream
         ↓
    Backend (FastAPI) /api/v1/chat/stream
         ↓
    SimpleAgent (LangGraph)
         ↓
    ┌─────────────────────────┐
    │ Dynamic Tools Selection │
    │ ├─ GLPI (if enabled)    │
    │ ├─ Zabbix (if enabled)  │
    │ ├─ Linear (if enabled)  │
    │ └─ Tavily (if enabled)  │
    └─────────────────────────┘
         ↓
    LLM (OpenRouter: x-ai/grok-4.1-fast)
         ↓
    SSE Stream → Frontend
```

---

## 🔐 Environment Variables

```bash
# OpenRouter
OPENROUTER_API_KEY=sk-or-...

# GLPI
GLPI_BASE_URL=https://glpi.hospitalevangelico.com.br/glpi/apirest.php
GLPI_APP_TOKEN=...
GLPI_USERNAME=...
GLPI_PASSWORD=...

# Zabbix
ZABBIX_BASE_URL=https://zabbix.hospitalevangelico.com.br
ZABBIX_API_TOKEN=...

# Linear
LINEAR_API_KEY=lin_api_...

# Model
DEFAULT_MODEL_NAME=x-ai/grok-4.1-fast
```

---

## 🤖 Agent System (.agent/)

### Agents (21)

| Agent | Focus | Primary Skills |
|-------|-------|----------------|
| `vsa-developer` | DeepCode VSA | python-patterns, langgraph-agent |
| `orchestrator` | Multi-agent | parallel-agents |
| `project-planner` | Planning | brainstorming, plan-writing |
| `frontend-specialist` | Web UI | frontend-design, nextjs-react-expert |
| `backend-specialist` | API | api-patterns, python-patterns |
| `debugger` | Troubleshooting | systematic-debugging |

### Key Skills (37)

| Skill | Description |
|-------|-------------|
| `langgraph-agent` | LangGraph patterns for VSA |
| `python-patterns` | Python best practices |
| `api-patterns` | REST/GraphQL API design |
| `clean-code` | Coding standards (global) |
| `brainstorming` | Socratic questioning |

### Workflows (12)

| Command | Description |
|---------|-------------|
| `/vsa` | VSA development workflow |
| `/create` | Create new features |
| `/debug` | Systematic debugging |
| `/plan` | Task planning |

---

## 📊 Statistics

| Metric | Value |
|--------|-------|
| Total Python Files | 25+ |
| Total TSX Components | 15+ |
| Lines of Code (core/) | ~2500 |
| Lines of Code (frontend/) | ~5000 |
| Docker Services | 3 (backend, frontend, postgres) |
| Integrations | 3 (GLPI, Zabbix, Linear) |
| LangChain Tools | 10 |

---

## 🚀 Quick Start

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f backend frontend

# Test integrations
.venv/bin/python scripts/test_integrations.py --all

# Access
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

---

## 📝 Recent Changes (27/01/2026)

1. ✅ **Phase 1 Complete**: GLPI, Zabbix, Linear tools integrated into chat
2. ✅ **VSA Toggles**: Frontend settings panel with integration toggles
3. ✅ **Dynamic Tools**: Chat loads tools based on user preferences
4. ✅ **Default Model**: Changed to `x-ai/grok-4.1-fast`
5. ✅ **Security**: Removed sensitive files from git history
6. ✅ **Zabbix Fix**: Corrected parameter name in `zabbix_get_alerts`
7. ✅ **Tests Passed**: GLPI query (5 tickets), Zabbix query (1 alert)

---

## 🧪 Phase 1 Test Results (27/01/2026 12:30 UTC)

**GLPI Query Test:**

```
Query: "Liste os últimos 5 tickets do GLPI"
Result: ✅ Success - Returned 5 tickets (IDs: 23597, 23596, 23595, 23594, 23593)
```

**Zabbix Query Test:**

```
Query: "Quais alertas críticos estão ativos no Zabbix?"
Result: ✅ Success - Returned 1 alert (Event ID: 2170626, Severity: High)
```

---

## 🔗 Documentation References

- `docs/PRD-REVISADO.md` - Full product requirements
- `docs/INTEGRACAO-METODOLOGIAS-CHAT.md` - Integration implementation guide
- `CLAUDE.md` / `GEMINI.md` - AI assistant configuration
- `STACK.md` - Complete technical documentation

---

**Last Updated:** 27/01/2026 12:30 UTC
**Maintainer:** VSA Tecnologia
