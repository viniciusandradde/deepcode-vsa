"""Executor Node - Executes plan steps with tools.

Reference: .claude/skills/vsa-agent-state/SKILL.md
"""

from datetime import datetime
from typing import Any

from langchain_core.messages import AIMessage

from ..state import VSAAgentState


async def run(state: VSAAgentState) -> dict[str, Any]:
    """Run executor node.
    
    Executes the current step in the plan.
    In dry_run mode, simulates execution without side effects.
    """
    plan = state.get("plan") or []
    current_step = state.get("current_step", 0)
    dry_run = state.get("dry_run", True)
    
    # Check if we have steps to execute
    if current_step >= len(plan):
        return {
            "should_continue": False,
            "messages": [AIMessage(content="✅ Todos os passos foram executados.")],
        }
    
    # Get current step
    step = plan[current_step]
    step_number = current_step + 1
    
    # TODO: Implement actual tool execution
    # For now, simulate execution
    result = {
        "step": step_number,
        "description": step,
        "executed": True,
        "dry_run": dry_run,
        "output": f"[{'DRY RUN' if dry_run else 'EXECUTED'}] {step}"
    }
    
    # Create audit entry
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "node": "executor",
        "action": "executed",
        "user": None,
        "dry_run": dry_run,
        "success": True,
        "details": {
            "step": step_number,
            "description": step,
        }
    }
    
    # Update message
    status_icon = "🔍" if dry_run else "✅"
    message = AIMessage(
        content=f"{status_icon} **Passo {step_number}**: {step}"
    )
    
    return {
        "current_step": current_step + 1,
        "tool_results": [result],
        "should_continue": True,
        "audit_log": [audit_entry],
        "messages": [message],
    }
