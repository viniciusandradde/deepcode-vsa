# CODEBASE.md - DeepCode VSA

> Quick reference for AI assistants and developers

---

## 📍 Project Identity

| Field | Value |
|-------|-------|
| **Name** | DeepCode VSA (Virtual Support Agent) |
| **Version** | 4.0 |
| **Type** | AI Chat for IT Management |
| **Language** | Python 3.11+ (backend), TypeScript (frontend) |
| **Framework** | FastAPI + LangGraph + Next.js 15 |

---

## 🏗️ Core Files Map

### API Layer (`api/`)

```
api/
├── main.py                  # FastAPI app, CORS, routers
├── routes/
│   ├── chat.py              # POST /api/v1/chat, /stream
│   ├── rag.py               # RAG endpoints
│   └── agents.py            # Agent endpoints
└── models/
    └── requests.py          # ChatRequest (enable_glpi, enable_zabbix, etc.)
```

### Business Logic (`core/`)

```
core/
├── config.py                # Pydantic Settings (GLPI, Zabbix, Linear configs)
├── agents/
│   ├── simple.py            # SimpleAgent - Main agent (active)
│   ├── vsa.py               # VSAAgent - ITIL agent logic
│   ├── unified.py           # UnifiedAgent - Main orchestrator (active)
│   └── workflow.py          # WorkflowAgent - Multi-intent logic
├── tools/
│   ├── glpi.py              # glpi_get_tickets, glpi_create_ticket
│   ├── zabbix.py            # zabbix_get_alerts, zabbix_get_host
│   ├── linear.py            # linear_get_issues, linear_create_issue
│   └── search.py            # tavily_search
└── integrations/
    ├── glpi_client.py       # GLPIClient (Basic Auth)
    ├── zabbix_client.py     # ZabbixClient (JSON-RPC)
    └── linear_client.py     # LinearClient (GraphQL)
```

### Frontend (`frontend/src/`)

```
frontend/src/
├── app/
│   └── api/threads/[threadId]/messages/stream/route.ts  # Proxy to backend
├── components/app/
│   ├── ChatPane.tsx         # Main chat UI
│   ├── SettingsPanel.tsx    # VSA toggles (GLPI, Zabbix, Linear)
│   └── Sidebar.tsx          # Session management
└── state/
    └── useGenesisUI.tsx     # Global state (enableGLPI, enableZabbix, etc.)
```

---

## 🔌 Active Integrations

| Integration | Client | Tools | Auth |
|-------------|--------|-------|------|
| **GLPI** | `GLPIClient` | `glpi_get_tickets`, `glpi_create_ticket`, `glpi_get_ticket_details` | Basic Auth |
| **Zabbix** | `ZabbixClient` | `zabbix_get_alerts`, `zabbix_get_host` | API Token |
| **Linear** | `LinearClient` | `linear_get_issues`, `linear_get_issue`, `linear_create_issue`, `linear_get_teams` | API Key |
| **Tavily** | Built-in | `tavily_search` | API Key |

---

## 🔧 Key Configuration

### Environment (`.env`)

```
OPENROUTER_API_KEY=...
DEFAULT_MODEL_NAME=x-ai/grok-4.1-fast

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
```

### Docker Services

```yaml
services:
  backend:   # FastAPI on :8000
  frontend:  # Next.js on :3000 (proxy to backend:8000)
  postgres:  # PostgreSQL on :5432
```

---

### 📉 Fluxo de Dados

```
Mensagem do Usuário
    ↓
Frontend (Next.js)
    ↓ POST /api/threads/{id}/messages/stream
Next.js Route Handler
    ↓ POST /api/v1/chat/stream
Backend (FastAPI)
    ↓
    ├─ UnifiedAgent.astream() (VSA Habilitado) ─▶ Router → Classifier → Planner → Executor
    └─ SimpleAgent.astream() (VSA Desabilitado) ─▶ Tools
    ↓
LLM Resposta (SSE Stream)
    ↓
Frontend (ChatPane)
```

---

## 🚀 Commands

```bash
# Development
docker compose up -d
docker compose logs -f backend

# Test integrations
.venv/bin/python scripts/test_integrations.py --all

# Access
# Chat: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

---

## 📝 Implementation Status

- [x] Phase 1: Basic Chat with Integrations
- [/] Phase 2: ITIL Methodologies (UnifiedAgent, Classifier) [EM PROGRESSO]
- [ ] Phase 3: Cross-system Correlation
- [ ] Phase 4: Governance & Audit

---

## 🔗 References

- `.agent/ARCHITECTURE.md` - Full architecture details
- `docs/PRD-REVISADO.md` - Product requirements
- `docs/INTEGRACAO-METODOLOGIAS-CHAT.md` - Integration guide
