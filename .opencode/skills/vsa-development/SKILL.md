---
name: vsa-development
description: DeepCode VSA development patterns. LangGraph agents, API integrations, Python async, Pydantic models, governance patterns.
license: MIT
compatibility: opencode
metadata:
  project: deepcode-vsa
  stack: python-langgraph
---

# VSA Development Skill

Specialized patterns for developing the DeepCode VSA agent.

## Architecture

The DeepCode VSA uses a **Planner-Executor-Reflector** pattern orchestrated by LangGraph:

```
Input → [Planner] → [Executor] → [Reflector] → Output
              ↑                        ↓
              └────── Loop ────────────┘
```

## LangGraph Patterns

### State Definition

```python
from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """State shared between all nodes."""
    messages: Annotated[list, add_messages]
    plan: Optional[list[str]]
    current_step: int
    results: dict
    should_continue: bool
    error: Optional[str]
```

### Graph Construction

```python
from langgraph.graph import StateGraph, END, START

workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("planner", planner_node)
workflow.add_node("executor", executor_node)
workflow.add_node("reflector", reflector_node)

# Add edges
workflow.add_edge(START, "planner")
workflow.add_edge("planner", "executor")
workflow.add_edge("executor", "reflector")

# Conditional edge for loop
workflow.add_conditional_edges(
    "reflector",
    should_continue,
    {"planner": "planner", END: END}
)

agent = workflow.compile()
```

### Node Pattern

```python
async def planner_node(state: AgentState) -> dict:
    """Node that creates the execution plan."""
    messages = state["messages"]
    
    # Create plan from last message
    plan = await create_plan(messages[-1].content)
    
    return {
        "plan": plan,
        "current_step": 0,
        "messages": [AIMessage(content=f"Plan: {plan}")]
    }
```

## API Integration Patterns

### APITool Contract

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel

class ToolResult(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None

class APITool(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...
    
    @property
    @abstractmethod
    def description(self) -> str: ...
    
    @abstractmethod
    async def read(self, operation: str, params: dict) -> ToolResult: ...
    
    @abstractmethod
    async def write(self, operation: str, data: dict, dry_run: bool = True) -> ToolResult: ...
```

### Tool Registry

```python
class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, APITool] = {}
    
    def register(self, tool: APITool) -> None:
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> APITool:
        return self._tools[name]
    
    def list_tools(self) -> list[APITool]:
        return list(self._tools.values())
```

## Governance Patterns

### Permission Decorator

```python
from enum import Enum
from functools import wraps

class OperationType(Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"

def governed_operation(op_type: OperationType):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, dry_run: bool = True, **kwargs):
            if op_type == OperationType.DELETE:
                raise PermissionError("DELETE blocked in v1")
            
            if op_type == OperationType.READ:
                return await func(self, *args, **kwargs)
            
            if op_type == OperationType.WRITE:
                if dry_run:
                    return await self._preview(func.__name__, *args, **kwargs)
                result = await func(self, *args, **kwargs)
                await self._audit_log(func.__name__, result)
                return result
        return wrapper
    return decorator
```

## Async HTTP Patterns

### httpx Client

```python
import httpx

class AsyncAPIClient:
    def __init__(self, base_url: str, headers: dict):
        self.base_url = base_url
        self.headers = headers
    
    async def get(self, endpoint: str, params: dict = None) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{endpoint}",
                params=params,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def post(self, endpoint: str, data: dict) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{endpoint}",
                json=data,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
```

## Testing Patterns

### Async Test

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_tickets():
    # Arrange
    tool = GLPITool(config)
    
    # Act
    result = await tool.read("get_tickets", {"status": "open"})
    
    # Assert
    assert result.success
    assert isinstance(result.data, list)
```

### Mock API

```python
import respx

@respx.mock
@pytest.mark.asyncio
async def test_create_ticket_dry_run():
    # Mock API response
    respx.post("https://glpi.example.com/apirest.php/Ticket").mock(
        return_value=httpx.Response(200, json={"id": 123})
    )
    
    tool = GLPITool(config)
    result = await tool.write("create_ticket", data, dry_run=True)
    
    # Should return preview, not execute
    assert "preview" in result.data
```

## Checklist

Before implementing:

- [ ] Read relevant ADRs in `docs/adr/`
- [ ] Check `CODEBASE.md` for structure
- [ ] Use async/await for all I/O
- [ ] Define Pydantic models
- [ ] Follow APITool contract
- [ ] Apply governance decorators
- [ ] Write tests with pytest-asyncio
