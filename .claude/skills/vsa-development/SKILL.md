---
name: vsa-development
description: DeepCode VSA development patterns. Use this skill when building the Virtual Support Agent CLI, implementing LangGraph agents, creating API integrations for GLPI/Zabbix/Proxmox, or working with Python async patterns and Pydantic models.
---

# DeepCode VSA Development

## Project Overview

DeepCode VSA is a CLI agent for IT management using:

- **Architecture**: Planner-Executor-Reflector (LangGraph)
- **Stack**: Python 3.11+, Typer, Rich, httpx, Pydantic v2
- **Integrations**: GLPI, Zabbix, Proxmox, Cloud, ERP

## Before Implementing

Always read:

1. `CODEBASE.md` - Project overview
2. `docs/PRD.md` - Product requirements  
3. `docs/adr/` - Architecture decisions (ADR-001 to ADR-009)

## Core Patterns

### 1. Async-First

```python
# ✅ CORRECT
async def fetch_data(self) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# ❌ WRONG
def fetch_data(self):
    return requests.get(url).json()  # Blocks event loop
```

### 2. Pydantic Models

```python
from pydantic import BaseModel
from datetime import datetime

class Ticket(BaseModel):
    id: int
    title: str
    priority: int
    created_at: datetime
```

### 3. APITool Contract

```python
class APITool(ABC):
    @property
    def name(self) -> str: ...
    
    @property
    def description(self) -> str: ...
    
    async def read(self, operation: str, params: dict) -> ToolResult: ...
    async def write(self, operation: str, data: dict, dry_run: bool = True) -> ToolResult: ...
```

### 4. Governance Rules

| Operation | Behavior |
|-----------|----------|
| READ | Automatic |
| WRITE | dry_run=True first |
| DELETE | **BLOCKED** in v1 |

## LangGraph Agent Pattern

```python
from langgraph.graph import StateGraph, START, END

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    plan: Optional[list[str]]
    current_step: int
    results: dict

workflow = StateGraph(AgentState)
workflow.add_node("planner", planner_node)
workflow.add_node("executor", executor_node)
workflow.add_node("reflector", reflector_node)

workflow.add_edge(START, "planner")
workflow.add_edge("planner", "executor")
workflow.add_edge("executor", "reflector")
workflow.add_conditional_edges(
    "reflector",
    should_continue,
    {"planner": "planner", END: END}
)

agent = workflow.compile()
```

## Code Structure

```
src/deepcode_vsa/
├── cli/               # Typer + Rich
├── agent/             # LangGraph
│   ├── graph.py       # Main graph
│   ├── nodes/         # Planner, Executor, Reflector
│   └── state.py       # AgentState
├── integrations/      # API Tools
│   ├── base.py        # APITool ABC
│   ├── registry.py    # ToolRegistry
│   ├── glpi/
│   └── zabbix/
├── llm/               # OpenRouter client
└── governance/        # Permission decorators
```

## Checklist

- [ ] Use async/await for all I/O
- [ ] Define Pydantic models
- [ ] Follow APITool contract
- [ ] Apply governance decorators
- [ ] Read relevant ADRs
- [ ] Write pytest tests
