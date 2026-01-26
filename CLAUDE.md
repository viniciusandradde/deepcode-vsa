# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**DeepCode VSA** (Virtual Support Agent) is an API-First intelligent CLI agent designed for IT management professionals. It acts as a **virtual analyst** that connects to multiple IT systems (GLPI, Zabbix, Proxmox, Cloud, ERP) to analyze operational data, correlate information across heterogeneous systems, prioritize demands using proven methodologies, and support strategic decision-making.

### Value Proposition
> Transform scattered API data into intelligent management decisions, reducing diagnostic time and increasing IT operational maturity.

### Target Audience
- **Primary**: IT Managers, Infrastructure/NOC Coordinators, Service Desk Analysts
- **Secondary**: MSPs, Healthcare IT, Educational IT, Corporate IT

### Product Goals
- Reduce diagnostic time by 60% (from 45min to 15min average)
- Standardize analyses with 100% adherence to ITIL methodologies
- Support 5+ API integrations in v1.0
- Enable correlation across 2+ data sources

**Status:** MVP v1.0 in development (Q1 2026) - Architecture defined, core implementations ongoing

## Product Interface - CRITICAL UPDATE (Jan 2026)

**⚠️ MAJOR PIVOT: PRD has been revised from CLI-First to Chat-First**

See `docs/PRD-REVISADO.md` for complete details.

### Primary Interface: Chat Web (Next.js)

The **primary product interface** is now the web chat application:

- ✅ **Fully functional** Next.js 15 + React 19 chat interface
- ✅ **Streaming SSE** for real-time responses
- ✅ **Session management** with localStorage + API persistence
- ✅ **Multi-model support** via OpenRouter
- 🟡 **VSA Agent integration** in progress (add ITIL methodologies)

**Location:** `frontend/` directory

### Secondary Interface: FastAPI Backend

The FastAPI server (`api/`) provides REST API endpoints:

- `/api/v1/chat` - Synchronous chat
- `/api/v1/chat/stream` - Streaming chat with SSE
- `/api/v1/rag/*` - RAG search and ingestion
- `/api/v1/agents/*` - Agent management

### CLI (Planned for v2.0)

The original CLI concept has been **deferred to v2.0**:

```bash
# Future CLI commands (planned, not implemented in v1.0)
deepcode-vsa analyze "avaliar riscos operacionais"
```

**Note**: The CLI entry point `vsa = "deepcode_vsa.cli.main:app"` in `pyproject.toml` does NOT exist yet. The package structure `src/deepcode_vsa/` is not created.

## Development Commands

### Installation & Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -e ".[dev]"

# Setup database (requires PostgreSQL with pgvector)
make setup-db

# Install frontend dependencies
make install-frontend
```

### Running the Application
```bash
# Start FastAPI server (port 8000)
make dev
# or
uvicorn api.main:app --reload --port 8000

# Start LangGraph Studio for visual debugging
make studio
# or
cd backend && langgraph dev

# Start Next.js frontend (port 3000)
make frontend
# or
cd frontend && npm run dev
```

### Testing
```bash
# Run all tests
make test
# or
pytest tests/ -v

# Run specific test suites
pytest tests/unit/ -v              # Unit tests only
pytest tests/integration/ -v       # Integration tests (requires real APIs)

# Run single test file
pytest tests/unit/test_agent.py -v

# Run with coverage
pytest tests/ --cov=core --cov=api -v
```

### Code Quality
```bash
# Lint with ruff
ruff check .

# Format with ruff
ruff format .

# Type checking with mypy
mypy core/ api/
```

## Architecture & Key Concepts

### Multi-Layer Architecture

The codebase is organized in three main layers:

1. **`core/`** - Business logic and agent implementations
   - `core/agents/` - Agent implementations (BaseAgent, SimpleAgent, WorkflowAgent, VSAAgent)
   - `core/integrations/` - External API clients (GLPI, Zabbix)
   - `core/tools/` - LangChain tools for agent usage
   - `core/rag/` - RAG pipeline (ingestion, chunking, search)
   - `core/middleware/` - Dynamic configuration middleware
   - `core/config.py` - Pydantic settings with environment variables

2. **`api/`** - FastAPI REST API layer
   - `api/routes/chat.py` - Chat endpoints (sync + streaming)
   - `api/routes/rag.py` - RAG search and ingestion
   - `api/routes/agents.py` - Agent management
   - `api/models/` - Pydantic request/response models

3. **`backend/`** - LangGraph Studio configuration
   - Used for visual debugging of agent workflows
   - Configuration in `backend/langgraph.json`

### VSA Agent Architecture (LangGraph)

The VSA agent implements a **5-node workflow** using LangGraph state graphs (see `core/agents/vsa.py`):

```
START → Classifier → Planner → Executor → Reflector → Integrator → END
                        ↑                      ↓
                        └──── (replan loop) ────┘
```

**Node Functions:**

1. **Classifier**: Categorizes requests into ITIL types (Incident, Problem, Change, Request, Chat) and calculates initial GUT score (Gravidade, Urgência, Tendência)

2. **Planner**: Creates step-by-step execution plan following ITIL methodology. For CHAT, provides simple response plan. For INCIDENT/PROBLEM, includes diagnosis and resolution steps.

3. **Executor**: Executes planned API calls and tool usage with controlled permissions. All WRITE operations respect dry_run flag.

4. **Reflector**: Validates execution results, checks if goals were met, decides whether replanning is needed (loops back to Planner) or proceeds to integration.

5. **Integrator**: Synthesizes final response with executive summary, audit trail, methodology justification, and next recommended actions.

State is defined in `VSAAgentState` (TypedDict) and includes:
- `messages`, `plan`, `methodology`, `task_category`, `priority`
- `gut_score` (Gravidade, Urgência, Tendência prioritization)
- `tool_results`, `glpi_context`, `zabbix_context`
- `dry_run` flag for safe execution

### LLM Configuration (Hybrid Model Strategy)

The system uses a tiered model approach (see `core/config.py`):

- **FAST tier**: Classification, GUT scoring → `meta-llama/llama-3.3-70b-instruct`
- **SMART tier**: RCA, planning, analysis → `deepseek/deepseek-chat`
- **PREMIUM tier**: Critical tasks, fallback → `anthropic/claude-3.5-sonnet`
- **CREATIVE tier**: Reports, summaries → `minimax/minimax-m2-her`

All models accessed via OpenRouter. Configure with `LLM_API_KEY` or `OPENROUTER_API_KEY` env var.

### Integration Patterns

All API integrations follow a standard contract pattern defined in the PRD:

```python
# Conceptual contract (Protocol pattern)
class APITool(Protocol):
    """Standard contract for API tools."""
    name: str
    description: str
    operations: List[Operation]

    def read(self, query: Query) -> Result:
        """Read operation (automatic, requires valid credentials)."""
        ...

    def write(self, data: WriteData, dry_run: bool = True) -> Result:
        """Write operation (controlled, requires explicit confirmation)."""
        ...
```

**Implementation layers:**
- **Clients** in `core/integrations/` - Raw API communication (e.g., `glpi_client.py`, `zabbix_client.py`)
- **Tools** in `core/tools/` - LangChain tool wrappers for agent usage
- Tools expose `name`, `description`, and callable interface
- All WRITE operations require explicit confirmation (dry_run by default)

**Integration phases (from PRD):**
- v1.0: GLPI, Zabbix (High priority)
- v1.1: Proxmox, AWS (Medium priority)
- v1.2: Azure, GCP, ERP (Medium priority)
- v2.0: Custom APIs via marketplace (Low priority)

### RAG Pipeline Architecture

The RAG system (in `core/rag/`) supports:
- **3 chunking strategies**: fixed-size, markdown-aware, semantic
- **Hybrid search**: vector + text + RRF (Reciprocal Rank Fusion)
- **HyDE**: Hypothetical Document Embeddings for better retrieval
- **Multi-tenancy**: Tenant isolation via `tenant_id` / `empresa` field
- **Optional reranking**: Cohere reranker integration

Schema in `sql/kb/`:
- `kb_docs` - Document staging table
- `kb_chunks` - Embeddings storage with pgvector
- Native PostgreSQL functions for search (`kb_hybrid_search`, etc.)

### IT Management Methodologies

The agent supports established IT management frameworks (see `.agent/skills/vsa-methodologies/`):

**ITIL v4 Practices:**
- **Incident Management**: Complete support - classify, prioritize, diagnose, resolve
- **Problem Management**: Complete support - RCA (5 Whys), pattern identification
- **Change Management**: Partial support - risk assessment, impact analysis
- **Asset Management**: Partial support - inventory queries, correlation

**Prioritization Frameworks:**
- **GUT Matrix** (Gravidade, Urgência, Tendência): Automated scoring for tickets and alerts
- **5W2H**: Structured analysis (What, Why, Where, When, Who, How, How much)
- **PDCA**: Continuous improvement cycle
- **RCA (Root Cause Analysis)**: 5 Whys technique for problem diagnosis
- **Kanban**: Backlog management principles

### Governance & Safety

**Execution Safety** (ADR-007):
- `dry_run=True` by default for all WRITE operations
- Explicit confirmation required for data creation/modification
- DELETE operations blocked in v1.0 (security)
- READ operations automatic with valid credentials

**Audit Trail Format:**
All operations must be logged in structured JSON format:
```json
{
  "timestamp": "2026-01-22T10:30:00Z",
  "user": "admin",
  "operation": "write",
  "target": "glpi.ticket",
  "data": { "title": "Server down", "priority": 3 },
  "dry_run": false,
  "result": "success",
  "explanation": "Ticket created based on criticality analysis using GUT matrix"
}
```

**Permission Model:**
| Operation | Behavior | Requirements |
|-----------|----------|--------------|
| READ | Automatic execution | Valid API credentials |
| WRITE | Requires confirmation | dry_run + explicit approval |
| DELETE | Blocked in v1.0 | Not available |

## Configuration

### Required Environment Variables

**✅ Status das Integrações - Hospital Evangélico**

| Integração | Status | Notas |
|------------|--------|-------|
| Linear.app | ✅ **FUNCIONANDO** | Team VSA Tecnologia conectado |
| Zabbix | ✅ **FUNCIONANDO** | API validada, monitoramento OK |
| GLPI | ⚠️ **PENDENTE** | Falta User Token válido |

**Como obter GLPI User Token:**
1. Acesse: https://glpi.hospitalevangelico.com.br
2. Login → Meu Perfil → Configurações Remotas → Tokens de API
3. Gere um novo token e adicione ao `.env` como `GLPI_USER_TOKEN`

**⚠️ IMPORTANTE:** Veja `STATUS-INTEGRACOES.md` para detalhes e `docs/SEGURANCA-CREDENCIAIS.md` para regras de segurança.

Para outras instalações, use `.env.example` como template:

```bash
# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=deepcode_vsa
DB_USER=postgres
DB_PASSWORD=your_password

# LLM Provider (OpenRouter)
OPENROUTER_API_KEY=sk-or-...
# or use alternative name
LLM_API_KEY=sk-or-...

# GLPI Integration
GLPI_ENABLED=true
GLPI_BASE_URL=https://your-glpi.com/apirest.php
GLPI_APP_TOKEN=your_app_token
GLPI_USER_TOKEN=your_user_token

# Zabbix Integration
ZABBIX_ENABLED=true
ZABBIX_BASE_URL=https://your-zabbix.com/api_jsonrpc.php
ZABBIX_API_TOKEN=your_api_token

# Linear.app Integration (NEW)
LINEAR_ENABLED=true
LINEAR_API_KEY=lin_api_your_key_here

# Optional: LangSmith Tracing
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=deepcode-vsa
```

### Model Configuration

Models can be configured in `models.yaml` or via environment variables:

```yaml
llm:
  provider: openrouter
  fast_model: meta-llama/llama-3.3-70b-instruct
  smart_model: deepseek/deepseek-chat
  premium_model: anthropic/claude-3.5-sonnet
  creative_model: minimax/minimax-m2-her
  default_tier: smart
```

## Product Requirements (from PRD)

### Functional Requirements (High Priority)
- **FR-01**: Execute analyses via CLI with natural language
- **FR-02**: Query multiple APIs (target: 5+ in v1.0)
- **FR-03**: Create data via API with explicit confirmation
- **FR-04**: Correlate information across 2+ data sources
- **FR-06**: Generate executive-level response summaries
- **FR-08**: Operate with external LLM (OpenRouter)
- **FR-09**: Dry-run mode for safe operation

### Non-Functional Requirements
- **NFR-01**: Local execution (no external server dependency for core functionality)
- **NFR-02**: Modular architecture (independent components)
- **NFR-03**: Plugin-based extensibility for new APIs
- **NFR-04**: Secure credential storage (environment variables, future: Vault)
- **NFR-05**: Cost-effective LLM usage (hybrid model strategy)
- **NFR-06**: Explainability (justification for all decisions)
- **NFR-07**: Performance target: < 30s for simple queries
- **NFR-08**: Partial offline operation capability

### Success Metrics (v1.0 Targets)
- Diagnostic time reduction: -60% (45min → 15min)
- Response clarity: NPS > 8
- ITIL adherence: 100%
- API integrations: 5+
- Agent uptime: 99%

## Key Architectural Decisions (ADRs)

See `docs/adr/` for complete decision records:

- **ADR-001**: CLI-first application (local execution, no server dependency)
- **ADR-002**: Python 3.11+ as primary language
- **ADR-003**: Intelligent agent architecture (Planner-Executor-Reflector)
- **ADR-004**: LangGraph for orchestration (explicit state graphs)
- **ADR-005**: API-First architecture (integration via APIs, not databases)
- **ADR-006**: Dynamic API Tool Registry (plugin-style integrations)
- **ADR-007**: Safe execution with dry-run and audit logs
- **ADR-008**: OpenRouter for multi-LLM access
- **ADR-009**: Initial focus on diagnostics over automation

## Important Files & Entry Points

### Core Application
- `api/main.py` - FastAPI application entry point
- `api/routes/chat.py` - Chat endpoints (sync + streaming)
- `core/agents/vsa.py` - VSA agent with ITIL methodologies (not yet integrated)
- `core/agents/simple.py` - Simple agent (currently used in chat)
- `core/agents/workflow.py` - Workflow agent with intent detection
- `core/config.py` - Application settings and configuration

### Integrations
- `core/integrations/glpi_client.py` - GLPI REST API client (✅ functional)
- `core/integrations/zabbix_client.py` - Zabbix JSON-RPC client (✅ functional)
- `core/tools/glpi.py` - LangChain tools for GLPI (✅ ready)
- `core/tools/zabbix.py` - LangChain tools for Zabbix (✅ ready)

### Frontend
- `frontend/src/components/app/ChatPane.tsx` - Main chat interface
- `frontend/src/state/useGenesisUI.tsx` - State management (Context API)
- `frontend/src/components/app/Sidebar.tsx` - Session management sidebar

### Documentation
- `docs/PRD.md` - Original PRD (CLI-focused, **outdated**)
- `docs/PRD-REVISADO.md` - **Revised PRD** (Chat-First approach) ⭐
- `docs/INTEGRACAO-METODOLOGIAS-CHAT.md` - Implementation guide for ITIL integration ⭐
- `pyproject.toml` - Python project metadata and dependencies
- `backend/langgraph.json` - LangGraph Studio configuration
- `Makefile` - Common development commands

## Skills and Patterns

This project includes custom Claude Code skills in `.agent/skills/`:

- **vsa-agent-state** - VSA agent state management patterns
- **vsa-cli-patterns** - CLI patterns with Typer and Rich
- **vsa-development** - DeepCode VSA development patterns
- **vsa-llm-config** - Hybrid LLM model selection
- **vsa-methodologies** - IT methodologies (ITIL, GUT, RCA, 5W2H)
- **vsa-safety-tools** - Computer Use safety patterns
- **api-patterns** - Python async API patterns
- **glpi-integration** - GLPI ITSM integration patterns
- **zabbix-integration** - Zabbix monitoring integration patterns
- **langgraph-agent** - LangGraph orchestration patterns
- **python-async** - Async/await best practices

Use these skills when working on related features by invoking them via the Skill tool.

## Project Structure Notes

- **No `src/deepcode_vsa/` yet**: The project uses direct imports from `core/`, `api/`, `backend/` at the root level. The `pyproject.toml` references `src/deepcode_vsa` but this directory doesn't exist yet - this is planned for CLI package distribution.

- **README vs PRD divergence**: The `README.md` describes a generic "AI Agent + RAG Template" but the **PRD defines the actual product**: DeepCode VSA for IT Management. The PRD is the source of truth for product requirements. The RAG capabilities (in `core/rag/`) are supporting features, not the primary product focus.

- **Template origins**: This codebase evolved from an AI agent + RAG template. Some references to "template" and generic agent examples remain in comments. When in doubt, follow the PRD's IT management focus.

- **Frontend**: Next.js 15 frontend in `frontend/` with React 19, Tailwind CSS, and state management via Context API. This is a supporting interface; the main product is the CLI.

- **Database**: PostgreSQL 16+ with pgvector extension required. Schema files in `sql/kb/` must be executed in order (01, 02, 03). The RAG database is used for knowledge base queries, not the primary VSA functionality.

## Testing Strategy

- **Unit tests** (`tests/unit/`) - Mock external dependencies, test business logic
- **Integration tests** (`tests/integration/`) - Require real API keys and database
- Use `conftest.py` for shared fixtures
- Mark integration tests that need real APIs appropriately

## Development Principles

**Follow the PRD, not the template**: The codebase contains remnants of a generic AI agent + RAG template, but development should be guided by `docs/PRD.md` which defines the actual product: an IT management CLI agent. When making decisions:

1. Prioritize IT management use cases (GLPI, Zabbix, incident analysis)
2. Focus on CLI as the primary interface
3. Ensure ITIL methodology compliance
4. Maintain audit trails and explainability
5. Default to safe execution (dry_run=True)

## Working with Existing Integrations

### GLPI Integration (✅ Ready)

**Client:** `core/integrations/glpi_client.py`
- `init_session()` - Authenticate with GLPI
- `get_tickets(status, limit)` - List tickets
- `get_ticket(ticket_id)` - Get ticket details
- `create_ticket(name, content, urgency, priority, dry_run)` - Create ticket

**Tools:** `core/tools/glpi.py`
- `glpi_get_tickets` - LangChain tool wrapper
- `glpi_get_ticket_details` - LangChain tool wrapper
- `glpi_create_ticket` - LangChain tool wrapper (respects dry_run)

**Configuration:** Set in `.env`
```bash
GLPI_ENABLED=true
GLPI_BASE_URL=https://your-glpi.com/apirest.php
GLPI_APP_TOKEN=your_app_token
GLPI_USER_TOKEN=your_user_token
```

**To integrate into chat:**
1. Import tools in `api/routes/chat.py`
2. Add to agent's tools list
3. Test with: "Liste os últimos 5 tickets do GLPI"

### Zabbix Integration (✅ Ready)

**Client:** `core/integrations/zabbix_client.py`
- `get_problems(limit, severity)` - Get active alerts
- `get_host(name)` - Get host details
- `get_items(host_id)` - Get host items/metrics

**Tools:** `core/tools/zabbix.py`
- `zabbix_get_alerts` - LangChain tool wrapper
- `zabbix_get_host` - LangChain tool wrapper

**Configuration:** Set in `.env`
```bash
ZABBIX_ENABLED=true
ZABBIX_BASE_URL=https://your-zabbix.com
ZABBIX_API_TOKEN=your_api_token
```

**To integrate into chat:**
1. Import tools in `api/routes/chat.py`
2. Add to agent's tools list
3. Test with: "Quais alertas críticos no Zabbix?"

### Linear.app Integration (✅ Ready) **NEW**

**Client:** `core/integrations/linear_client.py`
- `get_issues(team_id, state, limit)` - List issues
- `get_issue(issue_id)` - Get issue details
- `create_issue(team_id, title, description, priority, dry_run)` - Create issue
- `get_teams()` - List teams
- `add_comment(issue_id, body, dry_run)` - Add comment

**Tools:** `core/tools/linear.py`
- `linear_get_issues` - LangChain tool wrapper
- `linear_get_issue` - LangChain tool wrapper
- `linear_create_issue` - LangChain tool wrapper (respects dry_run)
- `linear_get_teams` - LangChain tool wrapper
- `linear_add_comment` - LangChain tool wrapper

**Configuration:** Set in `.env`
```bash
LINEAR_ENABLED=true
LINEAR_API_KEY=lin_api_your_key_here
```

**Use Cases:**
- **Alternative to GLPI**: Modern project management for IT teams
- **Change Management**: Track planned changes with Linear issues
- **Dev/Ops Bridge**: Connect infrastructure problems with dev tasks
- **Incident Escalation**: Escalate GLPI tickets to Linear for developer attention

**To integrate into chat:**
1. Get API key from https://linear.app/settings/api
2. Import tools in `api/routes/chat.py`
3. Add to agent's tools list
4. Test with: "Liste issues do Linear", "Criar issue no time de infra"

**See detailed examples:** `docs/EXEMPLOS-LINEAR-INTEGRACAO.md`

### Integration Architecture Pattern

All integrations follow this pattern:

```
User Message → Chat Endpoint → Agent (with tools) → Tool Call → Client → External API
                                                          ↓
                                                     Tool Result
                                                          ↓
                                                   Agent processes
                                                          ↓
                                                  Response to User
```

## Development Workflow

1. When adding new API integrations:
   - Create client in `core/integrations/`
   - Create tool wrapper in `core/tools/`
   - Register in API Tool Registry pattern
   - Add configuration to `core/config.py`
   - Write tests in `tests/unit/` and `tests/integration/`

2. When modifying agents:
   - Update state definitions if needed
   - Modify node functions (classifier, planner, executor, reflector)
   - Test with LangGraph Studio (`make studio`)
   - Ensure dry_run safety is maintained

3. When adding RAG features:
   - Update database schema in `sql/kb/`
   - Modify ingestion pipeline in `core/rag/ingestion.py`
   - Update search functions if needed
   - Test with various chunk strategies

## Roadmap & Implementation Status (REVISED)

**⚠️ Major Change:** Pivoted from CLI-First to Chat-First approach based on stable template.

### Current Status (January 2026)

**✅ Working Components:**
- Chat web interface (Next.js 15 + React 19)
- FastAPI backend with streaming SSE
- SimpleAgent and WorkflowAgent (functional)
- GLPI Client + Tools (ready, not integrated to chat)
- Zabbix Client + Tools (ready, not integrated to chat)
- PostgreSQL + pgvector for RAG
- Multi-model support via OpenRouter

**🟡 In Progress:**
- VSAAgent (implemented, needs chat integration)
- ITIL methodologies application (designed, not implemented)

**❌ Not Started:**
- CLI interface (deferred to v2.0)
- VSA integration in chat
- Automatic GLPI/Zabbix correlation
- GUT score calculation in chat flow

### Phase 1: Chat with Basic Integrations (Weeks 1-4)

**Goal:** Enable natural language queries to GLPI and Zabbix via chat

- [ ] Week 1-2: Integrate GLPI tools to chat endpoint
- [ ] Week 1-2: Integrate Zabbix tools to chat endpoint
- [ ] Week 3-4: Implement intent detection (WorkflowAgent adaptation)
- [ ] Week 3-4: Add visual feedback for tool calls in frontend

**Deliverable:** Chat can query GLPI and Zabbix when requested

### Phase 2: ITIL Methodologies in Chat (Weeks 5-8)

**Goal:** Apply ITIL classification and GUT prioritization

- [ ] Week 5-6: Integrate VSAAgent to chat
- [ ] Week 5-6: Implement automatic ITIL classification
- [ ] Week 7-8: Implement Planner with methodology-based plans
- [ ] Week 7-8: Add confirmation flow for WRITE operations

**Deliverable:** Chat applies ITIL frameworks automatically

### Phase 3: Correlation and Analysis (Weeks 9-12)

**Goal:** Correlate data across systems and generate insights

- [ ] Week 9-10: Implement GLPI ↔ Zabbix correlation
- [ ] Week 9-10: Add timeline visualization
- [ ] Week 11-12: Implement RCA (5 Whys) analysis
- [ ] Week 11-12: Generate executive reports (5W2H format)

**Deliverable:** Chat provides multi-system analysis

### Phase 4: Governance and Audit (Weeks 13-14)

**Goal:** Complete audit trail and governance

- [ ] Week 13-14: Structured audit logging
- [ ] Week 13-14: Audit dashboard in frontend
- [ ] Week 13-14: Export capabilities
- [ ] Week 13-14: LGPD compliance features

**Deliverable:** Full governance and auditability

### Phase 2: Expansion (v1.x) - Q2 2026
- [ ] Proxmox integration (READ VMs, resources)
- [ ] Cloud integrations (AWS/Azure - READ instances, costs)
- [ ] Enhanced Reflector with learning capabilities
- [ ] CLI audit dashboard

### Phase 3: Product Maturity (v2.0) - Q3-Q4 2026
- [ ] HTTP API for external integrations
- [ ] Optional Web UI
- [ ] Multi-tenancy support
- [ ] Integration marketplace

### Out of Scope (v1.0)
- Graphical UI (CLI-first approach)
- Automatic destructive execution (operational risk)
- DELETE operations via API (security)
- Mobile applications

## Glossary (from PRD)

Understanding domain-specific terminology:

| Term | Definition |
|------|-----------|
| **API-First** | Architecture prioritizing integration via APIs over direct database access |
| **GUT** | Gravidade, Urgência, Tendência - Brazilian prioritization matrix (Gravity, Urgency, Trend) |
| **ITIL** | Information Technology Infrastructure Library - IT service management framework |
| **ITSM** | IT Service Management - practices for delivering IT services |
| **MSP** | Managed Service Provider - companies providing outsourced IT management |
| **NOC** | Network Operations Center - centralized location for monitoring infrastructure |
| **RCA** | Root Cause Analysis - method to identify underlying causes of problems |
| **SLA** | Service Level Agreement - commitment between service provider and client |
| **VSA** | Virtual Support Agent - AI agent that acts as virtual IT analyst |

## Common Pitfalls

- **CLI not yet implemented**: The `vsa` CLI entry point in `pyproject.toml` points to `deepcode_vsa.cli.main:app` which doesn't exist yet. The package structure needs to be created.
- Always use `dry_run=True` by default for WRITE operations
- Import from `core.config` using `get_settings()` for cached config
- LangGraph state must be TypedDict with proper annotations
- PostgreSQL connection strings need URL encoding for special chars
- Frontend and backend run on different ports (3000 and 8000)
- LangSmith tracing is auto-enabled if `LANGCHAIN_API_KEY` is set
- **API vs CLI focus**: Remember this is primarily a CLI tool. The FastAPI server is a supporting component, not the main product interface.
