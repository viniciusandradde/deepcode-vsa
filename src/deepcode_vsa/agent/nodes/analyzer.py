"""Analyzer Node - Analyzes execution results.

Reference: .claude/skills/vsa-agent-state/SKILL.md
"""

from datetime import datetime
from typing import Any

from langchain_core.messages import AIMessage

from ..state import VSAAgentState


async def run(state: VSAAgentState) -> dict[str, Any]:
    """Run analyzer node.
    
    Analyzes execution results and determines:
    - If all steps are complete
    - If replanning is needed
    - Summary of findings
    """
    plan = state.get("plan") or []
    current_step = state.get("current_step", 0)
    tool_results = state.get("tool_results") or []
    methodology = state.get("methodology")
    
    # Check if all steps are complete
    all_done = current_step >= len(plan)
    
    # Check for errors that require replanning
    has_errors = any(
        not r.get("success", True) 
        for r in tool_results
    )
    needs_replan = has_errors and current_step < len(plan)
    
    # Create audit entry
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "node": "analyzer",
        "action": "analyzed",
        "user": None,
        "dry_run": state.get("dry_run", True),
        "success": True,
        "details": {
            "all_done": all_done,
            "needs_replan": needs_replan,
            "steps_completed": current_step,
            "total_steps": len(plan),
        }
    }
    
    # Generate summary message
    if all_done:
        methodology_name = methodology.value.upper() if methodology else "ITIL"
        message = AIMessage(
            content=f"📊 **Análise concluída** usando metodologia {methodology_name}.\n\n"
                    f"✅ {current_step} passos executados com sucesso."
        )
        should_continue = False
    elif needs_replan:
        message = AIMessage(
            content="⚠️ Erros detectados. Necessário replanejamento."
        )
        should_continue = False
    else:
        remaining = len(plan) - current_step
        message = AIMessage(
            content=f"▶️ Continuando execução... ({remaining} passos restantes)"
        )
        should_continue = True
    
    return {
        "should_continue": should_continue,
        "needs_replan": needs_replan,
        "audit_log": [audit_entry],
        "messages": [message],
    }
