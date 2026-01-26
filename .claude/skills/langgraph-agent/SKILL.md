---
name: langgraph-agent
description: LangGraph agent orchestration patterns. Use this skill when building AI agents with state machines, graphs, nodes, conditional edges, checkpoints, and streaming. Covers Planner-Executor-Reflector pattern.
---

# LangGraph Agent Patterns

## Core Concepts

| Concept | Purpose |
|---------|---------|
| State | Shared data between nodes |
| Node | Function that transforms state |
| Edge | Connection between nodes |
| Conditional Edge | Branch based on state |

## State Definition

```python
from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    plan: Optional[list[str]]
    current_step: int
    results: dict
    should_continue: bool
    error: Optional[str]
```

## Graph Construction

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

## Node Pattern

```python
async def planner_node(state: AgentState) -> dict:
    """Node that creates the execution plan."""
    messages = state["messages"]
    plan = await create_plan(messages[-1].content)
    
    return {
        "plan": plan,
        "current_step": 0,
        "messages": [AIMessage(content=f"Plan: {plan}")]
    }
```

## Conditional Routing

```python
def should_continue(state: AgentState) -> str:
    if state.get("error"):
        return "error_handler"
    if state["current_step"] >= len(state["plan"]):
        return END
    return "executor"
```

## Memory & Checkpoints

```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "session-123"}}
result = await app.ainvoke(initial_state, config)
```

## Streaming

```python
async for event in app.astream(initial_state):
    node_name = list(event.keys())[0]
    output = event[node_name]
    print(f"[{node_name}] {output}")
```

## Planner-Executor-Reflector Pattern

```
START ─► Planner ─► Executor ─► Reflector ─► END
              ▲          │            │
              └──────────┴────────────┘
                    (retry/replan)
```

## Best Practices

1. **Immutable state updates** - Return new dicts, don't mutate
2. **Type all state** - Use TypedDict strictly
3. **Clear routing logic** - Decision functions should be simple
4. **Handle errors** - Always have error paths
5. **Limit loops** - Set max iterations
