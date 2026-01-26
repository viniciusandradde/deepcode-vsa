# DeepCode VSA - Agent Instructions

> This file is automatically read by OpenCode to understand project context.

## Project Overview

**DeepCode VSA** (Virtual Support Agent) is an intelligent CLI agent for IT management that connects to multiple APIs (GLPI, Zabbix, Proxmox, Cloud, ERP).

| Aspect | Detail |
|--------|--------|
| **Type** | CLI Application (Linux) |
| **Language** | Python 3.11+ |
| **Architecture** | Planner-Executor-Reflector (LangGraph) |
| **LLM** | OpenRouter (multi-provider) |
| **Focus** | Diagnosis and decision support (not automation) |

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                         DeepCode VSA                                │
├────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐                                                  │
│  │   CLI Layer  │  Typer + Rich                                    │
│  └──────┬───────┘                                                  │
│         │                                                          │
│         ▼                                                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    Agent Core (LangGraph)                     │ │
│  │  ┌─────────┐    ┌──────────┐    ┌───────────┐               │ │
│  │  │ Planner │───▶│ Executor │───▶│ Reflector │               │ │
│  │  └─────────┘    └──────────┘    └───────────┘               │ │
│  └──────────────────────────────────────────────────────────────┘ │
│         │                                                          │
│         ▼                                                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                   API Tool Registry                           │ │
│  │  ┌──────┐ ┌──────┐ ┌─────────┐ ┌───────┐ ┌─────┐           │ │
│  │  │ GLPI │ │Zabbix│ │ Proxmox │ │ Cloud │ │ ERP │  ...      │ │
│  │  └──────┘ └──────┘ └─────────┘ └───────┘ └─────┘           │ │
│  └──────────────────────────────────────────────────────────────┘ │
│         │                                                          │
│         ▼                                                          │
│  ┌──────────────┐                                                  │
│  │  LLM Layer   │  OpenRouter (GPT-4, Claude, Llama, etc.)        │
│  └──────────────┘                                                  │
└────────────────────────────────────────────────────────────────────┘
```

---

## Key Decisions (ADRs)

| ADR | Decision | Impact |
|-----|----------|--------|
| ADR-001 | CLI Local | Linux-first, Python |
| ADR-003 | Planner-Executor-Reflector | Explainability |
| ADR-004 | LangGraph | State machine orchestration |
| ADR-005 | API-First (no MCP) | Direct API connections |
| ADR-006 | Tool Registry | Dynamic API management |
| ADR-007 | Governance | READ=auto, WRITE=controlled, DELETE=blocked |
| ADR-008 | OpenRouter | Multi-LLM provider |

---

## Code Structure

```
src/deepcode_vsa/
├── cli/               # Typer + Rich CLI
├── agent/             # LangGraph (graph, nodes, state)
│   ├── graph.py       # Main graph definition
│   ├── nodes/         # Planner, Executor, Reflector
│   └── state.py       # AgentState TypedDict
├── integrations/      # API Tools
│   ├── base.py        # APITool abstract class
│   ├── registry.py    # ToolRegistry
│   ├── glpi/          # GLPI integration
│   └── zabbix/        # Zabbix integration
├── llm/               # OpenRouter client
├── governance/        # Permission decorators
└── methodologies/     # ITIL, GUT, 5W2H
```

---

## Mandatory Patterns

### 1. Async-First

All I/O operations MUST be async:

```python
# ✅ CORRECT
async def fetch_tickets(self, filters: dict) -> list[Ticket]:
    async with httpx.AsyncClient() as client:
        response = await client.get(...)

# ❌ WRONG - blocks event loop
def fetch_tickets(self, filters: dict):
    response = requests.get(...)
```

### 2. Pydantic Models

All data MUST use Pydantic:

```python
# ✅ CORRECT
class Ticket(BaseModel):
    id: int
    title: str
    priority: Priority
    created_at: datetime

# ❌ WRONG - no validation
ticket = {"id": 1, "title": "..."}
```

### 3. APITool Contract

All integrations follow this contract:

```python
class APITool(ABC):
    @property
    def name(self) -> str: ...
    
    @property
    def description(self) -> str: ...
    
    @property
    def operations(self) -> list[Operation]: ...
    
    async def read(self, operation: str, params: dict) -> ToolResult: ...
    
    async def write(self, operation: str, data: dict, dry_run: bool = True) -> ToolResult: ...
```

### 4. Governance

```python
# READ: Automatic execution
@governed_operation(OperationType.READ)
async def get_tickets(self, filters: dict) -> ToolResult: ...

# WRITE: Requires dry_run=True first
@governed_operation(OperationType.WRITE)
async def create_ticket(self, data: dict, dry_run: bool = True) -> ToolResult:
    if dry_run:
        return self._preview(data)
    # Execute with audit log
```

### 5. LangGraph State

```python
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    plan: Optional[list[str]]
    current_step: int
    results: dict
    should_continue: bool
```

---

## Important Files

| File | Purpose |
|------|---------|
| `CODEBASE.md` | Complete project reference |
| `docs/PRD.md` | Product requirements |
| `docs/adr/` | Architecture decisions |
| `.agent/` | Antigravity Kit agents/skills |

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| CLI | Typer + Rich |
| Agent | LangGraph |
| LLM | OpenRouter |
| HTTP | httpx (async) |
| Validation | Pydantic v2 |
| Testing | pytest + pytest-asyncio |
| Linting | Ruff |

---

## Rules

1. **Never implement DELETE operations** - blocked in v1
2. **Always use async/await** for I/O
3. **Always use Pydantic** for data models
4. **Follow APITool contract** for integrations
5. **WRITE operations need dry_run first**
6. **Read ADRs before implementing**
7. **Document with Google-style docstrings**
8. **Test with pytest and AAA pattern**

---

## Specialized Agents

Use `@agent-name` to invoke specialized help:

| Agent | Purpose |
|-------|---------|
| `@vsa` | General VSA development |
| `@glpi` | GLPI API integration |
| `@zabbix` | Zabbix API integration |
| `@security` | Security review |

---

*Generated for DeepCode VSA - January 2026*
