---
name: langgraph-patterns
description: LangGraph agent orchestration patterns. State machines, graphs, nodes, conditional edges, checkpoints. For building AI agents.
license: MIT
compatibility: opencode
metadata:
  framework: langgraph
  version: "0.x"
---

# LangGraph Patterns Skill

Patterns for building AI agents with LangGraph.

## Core Concepts

| Concept | Purpose |
|---------|---------|
| **State** | Shared data between nodes |
| **Node** | Function that transforms state |
| **Edge** | Connection between nodes |
| **Conditional Edge** | Branch based on state |
| **Graph** | Complete agent workflow |

## State Definition

### Basic State

```python
from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # Messages with append reducer
    messages: Annotated[list, add_messages]
    
    # Workflow data
    plan: Optional[list[str]]
    current_step: int
    results: dict
    
    # Control flags
    should_continue: bool
    error: Optional[str]
```

### Custom Reducers

```python
from operator import add

class State(TypedDict):
    # Append new items to list
    logs: Annotated[list[str], add]
    
    # Always use latest value (default)
    counter: int
    
    # Custom merge logic
    data: Annotated[dict, lambda old, new: {**old, **new}]
```

## Node Patterns

### Sync Node

```python
def process_node(state: AgentState) -> dict:
    """Process and return state updates."""
    data = state["results"]
    processed = transform(data)
    
    return {
        "results": processed,
        "current_step": state["current_step"] + 1
    }
```

### Async Node

```python
async def fetch_node(state: AgentState) -> dict:
    """Async node for I/O operations."""
    async with httpx.AsyncClient() as client:
        response = await client.get(state["url"])
    
    return {
        "results": response.json(),
        "messages": [AIMessage(content="Data fetched")]
    }
```

### Tool Node

```python
from langgraph.prebuilt import ToolNode

tools = [search_tool, calculator_tool, api_tool]
tool_node = ToolNode(tools)
```

## Graph Construction

### Basic Graph

```python
from langgraph.graph import StateGraph, END, START

# Create graph with state type
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("planner", planner_node)
workflow.add_node("executor", executor_node)
workflow.add_node("reflector", reflector_node)

# Add edges
workflow.add_edge(START, "planner")
workflow.add_edge("planner", "executor")
workflow.add_edge("executor", "reflector")
workflow.add_edge("reflector", END)

# Compile
app = workflow.compile()
```

### Conditional Edges

```python
def route_decision(state: AgentState) -> str:
    """Decide next node based on state."""
    if state.get("error"):
        return "error_handler"
    if state["current_step"] >= len(state["plan"]):
        return "complete"
    return "continue"

workflow.add_conditional_edges(
    "executor",           # Source node
    route_decision,       # Decision function
    {
        "continue": "executor",      # Loop
        "complete": "reflector",     # Next stage
        "error_handler": "error"     # Error handling
    }
)
```

### Loop Pattern (Reflection)

```python
def should_replan(state: AgentState) -> str:
    """Check if replanning is needed."""
    if state.get("needs_replan"):
        return "replan"
    return "done"

workflow.add_conditional_edges(
    "reflector",
    should_replan,
    {
        "replan": "planner",  # Loop back
        "done": END
    }
)
```

## Memory & Checkpoints

### In-Memory

```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# Use with thread_id for persistence
config = {"configurable": {"thread_id": "session-123"}}
result = await app.ainvoke(initial_state, config)
```

### SQLite Persistence

```python
from langgraph.checkpoint.sqlite import SqliteSaver

with SqliteSaver.from_conn_string("./checkpoints.db") as memory:
    app = workflow.compile(checkpointer=memory)
```

## Streaming

### Stream Events

```python
async for event in app.astream(initial_state):
    node_name = list(event.keys())[0]
    output = event[node_name]
    print(f"[{node_name}] {output}")
```

### Stream Tokens

```python
async for event in app.astream_events(initial_state, version="v2"):
    if event["event"] == "on_chat_model_stream":
        token = event["data"]["chunk"].content
        print(token, end="", flush=True)
```

## Error Handling

### Error Node

```python
def error_handler(state: AgentState) -> dict:
    """Handle errors and decide recovery."""
    error = state.get("error")
    retry_count = state.get("retry_count", 0)
    
    if retry_count < 3:
        return {
            "error": None,
            "retry_count": retry_count + 1,
            "messages": [AIMessage(content=f"Retrying... ({retry_count + 1}/3)")]
        }
    
    return {
        "should_continue": False,
        "messages": [AIMessage(content=f"Failed after 3 retries: {error}")]
    }
```

### Try-Catch in Nodes

```python
async def safe_node(state: AgentState) -> dict:
    try:
        result = await risky_operation(state)
        return {"results": result}
    except Exception as e:
        return {
            "error": str(e),
            "messages": [AIMessage(content=f"Error: {e}")]
        }
```

## Common Patterns

### Planner-Executor-Reflector

```
START ─► Planner ─► Executor ─► Reflector ─► END
              ▲          │            │
              └──────────┴────────────┘
                    (retry/replan)
```

### Tool Calling Loop

```
START ─► Agent ─┬─► Tool Node ─► Agent
                │
                └─► END (when done)
```

### Parallel Execution

```python
from langgraph.graph import StateGraph

# Parallel branches merge at a common node
workflow.add_edge("start", "branch_a")
workflow.add_edge("start", "branch_b")
workflow.add_edge("branch_a", "merge")
workflow.add_edge("branch_b", "merge")
```

## Testing

### Unit Test Node

```python
import pytest

def test_planner_creates_plan():
    state = {
        "messages": [HumanMessage(content="Analyze risks")],
        "plan": None
    }
    
    result = planner_node(state)
    
    assert "plan" in result
    assert len(result["plan"]) > 0
```

### Integration Test Graph

```python
@pytest.mark.asyncio
async def test_full_workflow():
    initial = {
        "messages": [HumanMessage(content="Test query")],
        "plan": None,
        "results": {},
        "current_step": 0
    }
    
    result = await app.ainvoke(initial)
    
    assert result["should_continue"] == False
    assert "error" not in result or result["error"] is None
```

## Best Practices

1. **Immutable state updates** - Return new dicts, don't mutate
2. **Type all state** - Use TypedDict strictly
3. **Clear routing logic** - Decision functions should be simple
4. **Handle errors** - Always have error paths
5. **Limit loops** - Set max iterations
6. **Log transitions** - Add observability

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangGraph Tutorials](https://langchain-ai.github.io/langgraph/tutorials/)
- [LangGraph Examples](https://github.com/langchain-ai/langgraph/tree/main/examples)
