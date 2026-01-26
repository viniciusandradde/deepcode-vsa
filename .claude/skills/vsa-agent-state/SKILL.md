---
name: vsa-agent-state
description: VSA Agent state management patterns. Use when implementing the VSAAgentState, LangGraph nodes (Classifier, Planner, Executor, Analyzer, Integrator, Auditor), or the complete agent workflow.
---

# VSA Agent State & Nodes

## VSAAgentState Definition

```python
from typing import TypedDict, Annotated, Optional, Any
from enum import Enum
from langgraph.graph.message import add_messages

class Methodology(str, Enum):
    ITIL = "itil"
    GUT = "gut"
    RCA = "rca"
    W5H2 = "5w2h"
    PDCA = "pdca"

class TaskCategory(str, Enum):
    INCIDENT = "incident"
    PROBLEM = "problem"
    CHANGE = "change"
    REQUEST = "request"

class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class VSAAgentState(TypedDict):
    # OpenCode base fields
    messages: Annotated[list, add_messages]
    user_request: str
    plan: Optional[list[str]]
    current_step: int
    tool_calls: list[dict]
    file_context: dict
    
    # VSA extensions
    methodology: Optional[Methodology]
    task_category: Optional[TaskCategory]
    priority: Optional[Priority]
    gut_score: Optional[int]
    
    # System contexts
    glpi_context: Optional[dict]
    zabbix_context: Optional[dict]
    linear_context: Optional[dict]
    
    # Control flow
    should_continue: bool
    needs_replan: bool
    error: Optional[str]
    
    # Audit & compliance
    audit_log: list[dict]
    compliance_checked: bool
    dry_run: bool
```

---

## Node: Classifier

```python
from datetime import datetime

async def classifier_node(state: VSAAgentState) -> dict:
    """
    Classifies the request and determines methodology.
    First node in the agent workflow.
    """
    user_request = state["user_request"]
    
    # Classify task category (ITIL)
    category = classify_task(user_request)
    
    # Estimate priority (GUT if not explicit)
    gut = estimate_gut(user_request)
    priority = Priority[gut.priority]
    
    # Determine best methodology
    methodology = _select_methodology(category, user_request)
    
    # Log classification
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "node": "classifier",
        "action": "classified",
        "category": category.value,
        "priority": priority.value,
        "methodology": methodology.value
    }
    
    return {
        "task_category": category,
        "priority": priority,
        "methodology": methodology,
        "gut_score": gut.score,
        "audit_log": [audit_entry],
        "messages": [AIMessage(content=f"Classified as {category.value} ({priority.value}) using {methodology.value}")]
    }

def _select_methodology(category: TaskCategory, request: str) -> Methodology:
    if category == TaskCategory.PROBLEM:
        return Methodology.RCA  # Problems need root cause
    if "priorit" in request.lower() or "rank" in request.lower():
        return Methodology.GUT  # Prioritization requested
    return Methodology.ITIL  # Default
```

---

## Node: Planner

```python
async def planner_node(state: VSAAgentState) -> dict:
    """
    Generates execution plan based on methodology.
    """
    methodology = state["methodology"]
    category = state["task_category"]
    user_request = state["user_request"]
    
    # Generate methodology-specific plan
    if methodology == Methodology.RCA:
        plan = _generate_rca_plan(user_request)
    elif methodology == Methodology.GUT:
        plan = _generate_gut_plan(user_request)
    else:
        plan = _generate_itil_plan(category, user_request)
    
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "node": "planner",
        "action": "planned",
        "steps": len(plan)
    }
    
    return {
        "plan": plan,
        "current_step": 0,
        "audit_log": [audit_entry],
        "messages": [AIMessage(content=f"Plan generated with {len(plan)} steps")]
    }

def _generate_itil_plan(category: TaskCategory, request: str) -> list[str]:
    if category == TaskCategory.INCIDENT:
        return [
            "1. Identify affected service/system",
            "2. Check Zabbix for related alerts",
            "3. Query GLPI for related tickets",
            "4. Assess impact and urgency",
            "5. Document initial findings",
            "6. Propose restoration steps"
        ]
    elif category == TaskCategory.PROBLEM:
        return [
            "1. Gather incident history",
            "2. Identify patterns",
            "3. Perform root cause analysis",
            "4. Propose permanent fix",
            "5. Document known error"
        ]
    # ... more categories
```

---

## Node: Executor

```python
async def executor_node(state: VSAAgentState) -> dict:
    """
    Executes current step in the plan.
    Loops until all steps complete.
    """
    plan = state["plan"]
    current_step = state["current_step"]
    dry_run = state["dry_run"]
    
    if current_step >= len(plan):
        return {"should_continue": False}
    
    step = plan[current_step]
    
    # Determine tool to use
    tool_name, tool_params = _parse_step(step)
    
    # Execute with safety
    result = await execute_tool(
        tool_name,
        tool_params,
        dry_run=dry_run
    )
    
    # Log execution
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "node": "executor",
        "action": "executed",
        "step": current_step + 1,
        "tool": tool_name,
        "dry_run": dry_run,
        "success": result.success
    }
    
    return {
        "current_step": current_step + 1,
        "tool_calls": [{"step": current_step + 1, "tool": tool_name, "result": result}],
        "audit_log": [audit_entry],
        "should_continue": True
    }
```

---

## Node: Analyzer

```python
async def analyzer_node(state: VSAAgentState) -> dict:
    """
    Analyzes execution results using methodology.
    Decides if replanning is needed.
    """
    methodology = state["methodology"]
    tool_calls = state["tool_calls"]
    plan = state["plan"]
    
    # Analyze results with methodology
    if methodology == Methodology.RCA:
        analysis = await _analyze_rca(tool_calls)
    elif methodology == Methodology.GUT:
        analysis = await _analyze_gut(tool_calls)
    else:
        analysis = await _analyze_general(tool_calls)
    
    # Check if we need to replan
    needs_replan = analysis.get("needs_replan", False)
    
    # Check if all steps executed
    all_done = state["current_step"] >= len(plan)
    
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "node": "analyzer",
        "action": "analyzed",
        "needs_replan": needs_replan,
        "all_done": all_done
    }
    
    return {
        "needs_replan": needs_replan,
        "should_continue": not all_done and not needs_replan,
        "audit_log": [audit_entry],
        "messages": [AIMessage(content=analysis.get("summary", "Analysis complete"))]
    }
```

---

## Node: Integrator

```python
async def integrator_node(state: VSAAgentState) -> dict:
    """
    Integrates with external systems (Linear, Telegram).
    Only runs after successful completion.
    """
    priority = state["priority"]
    task_category = state["task_category"]
    
    integrations = []
    
    # Create Linear issue for high priority
    if priority in [Priority.CRITICAL, Priority.HIGH]:
        if state.get("linear_context"):
            issue = await create_linear_issue(state)
            integrations.append({"type": "linear", "result": issue})
    
    # Send Telegram notification
    if priority == Priority.CRITICAL:
        notification = await send_telegram_notification(state)
        integrations.append({"type": "telegram", "result": notification})
    
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "node": "integrator",
        "action": "integrated",
        "integrations": [i["type"] for i in integrations]
    }
    
    return {
        "linear_context": integrations,
        "audit_log": [audit_entry]
    }
```

---

## Node: Auditor

```python
async def auditor_node(state: VSAAgentState) -> dict:
    """
    Final node - generates audit trail and compliance report.
    """
    audit_log = state["audit_log"]
    dry_run = state["dry_run"]
    
    # Generate compliance report
    compliance = {
        "total_steps": len(state["plan"]),
        "executed_steps": state["current_step"],
        "dry_run_mode": dry_run,
        "methodology_used": state["methodology"].value,
        "priority": state["priority"].value,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Check compliance rules
    compliance_passed = _check_compliance_rules(state)
    
    final_audit = {
        "timestamp": datetime.utcnow().isoformat(),
        "node": "auditor",
        "action": "audit_complete",
        "compliance_passed": compliance_passed,
        "summary": compliance
    }
    
    return {
        "audit_log": [final_audit],
        "compliance_checked": compliance_passed,
        "messages": [AIMessage(content=f"Audit complete. Compliance: {'✅' if compliance_passed else '❌'}")]
    }
```

---

## Complete Workflow

```python
from langgraph.graph import StateGraph, START, END

def create_vsa_agent() -> StateGraph:
    workflow = StateGraph(VSAAgentState)
    
    # Add nodes
    workflow.add_node("classifier", classifier_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("analyzer", analyzer_node)
    workflow.add_node("integrator", integrator_node)
    workflow.add_node("auditor", auditor_node)
    
    # Define flow
    workflow.add_edge(START, "classifier")
    workflow.add_edge("classifier", "planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "analyzer")
    
    # Conditional: continue executing or move to integration
    workflow.add_conditional_edges(
        "analyzer",
        _route_after_analysis,
        {
            "executor": "executor",      # More steps to execute
            "planner": "planner",        # Needs replanning
            "integrator": "integrator"   # All done
        }
    )
    
    workflow.add_edge("integrator", "auditor")
    workflow.add_edge("auditor", END)
    
    return workflow.compile()

def _route_after_analysis(state: VSAAgentState) -> str:
    if state["needs_replan"]:
        return "planner"
    if state["should_continue"]:
        return "executor"
    return "integrator"
```
