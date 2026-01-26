"""Classifier Node - Classifies request using ITIL and GUT.

Reference: .claude/skills/vsa-methodologies/SKILL.md
"""

from datetime import datetime
from typing import Any

from langchain_core.messages import AIMessage

from ..state import VSAAgentState, Methodology, TaskCategory, Priority


# Classification patterns
CLASSIFICATION_PATTERNS: dict[TaskCategory, list[str]] = {
    TaskCategory.INCIDENT: [
        "down", "offline", "failing", "error", "not working",
        "outage", "broken", "crashed", "unavailable", "slow",
        "timeout", "connection refused", "500", "503"
    ],
    TaskCategory.PROBLEM: [
        "recurring", "keeps failing", "intermittent", "pattern",
        "root cause", "why does", "investigate", "repeated",
        "chronic", "persistent"
    ],
    TaskCategory.CHANGE: [
        "migrate", "upgrade", "install", "deploy", "update",
        "modify", "configure", "replace", "implement", "rollout"
    ],
    TaskCategory.REQUEST: [
        "create user", "reset password", "access", "permissions",
        "setup", "provision", "new account", "onboarding"
    ],
}

# Severity patterns for GUT estimation
SEVERITY_PATTERNS: dict[int, list[str]] = {
    5: ["production down", "data loss", "security breach", "critical", "p1", "emergency"],
    4: ["major impact", "many users", "revenue", "core system", "p2"],
    3: ["moderate impact", "some users", "workaround exists"],
    2: ["minor impact", "few users", "cosmetic", "p4"],
    1: ["no impact", "enhancement", "nice to have", "p5"],
}


def classify_task(description: str) -> TaskCategory:
    """Classify task into ITIL category."""
    text = description.lower()
    
    for category, patterns in CLASSIFICATION_PATTERNS.items():
        if any(p in text for p in patterns):
            return category
    
    return TaskCategory.REQUEST  # Default


def estimate_gut(description: str) -> tuple[int, int, int, int]:
    """Estimate GUT score from description.
    
    Returns:
        (gravidade, urgencia, tendencia, score)
    """
    text = description.lower()
    
    # Estimate gravity (G)
    gravidade = 3
    for score, patterns in SEVERITY_PATTERNS.items():
        if any(p in text for p in patterns):
            gravidade = score
            break
    
    # Estimate urgency (U)
    urgencia = 3
    if any(w in text for w in ["immediately", "asap", "urgent", "agora", "now"]):
        urgencia = 5
    elif any(w in text for w in ["today", "hoje", "critical"]):
        urgencia = 4
    elif any(w in text for w in ["can wait", "quando puder"]):
        urgencia = 2
    
    # Estimate tendency (T)
    tendencia = 3
    if any(w in text for w in ["getting worse", "piorando", "spreading", "recurring"]):
        tendencia = 5
    elif any(w in text for w in ["stable", "estável"]):
        tendencia = 2
    
    score = gravidade * urgencia * tendencia
    return gravidade, urgencia, tendencia, score


def determine_priority(gut_score: int) -> Priority:
    """Determine priority from GUT score."""
    if gut_score >= 100:
        return Priority.CRITICAL
    elif gut_score >= 60:
        return Priority.HIGH
    elif gut_score >= 30:
        return Priority.MEDIUM
    return Priority.LOW


def select_methodology(category: TaskCategory, description: str) -> Methodology:
    """Select best methodology for the task."""
    text = description.lower()
    
    # Problem always needs RCA
    if category == TaskCategory.PROBLEM:
        return Methodology.RCA
    
    # Explicit prioritization request
    if any(w in text for w in ["priorit", "rank", "ordenar", "gut"]):
        return Methodology.GUT
    
    # Analysis request
    if any(w in text for w in ["5w2h", "análise", "analysis"]):
        return Methodology.W5H2
    
    # Default to ITIL
    return Methodology.ITIL


async def run(state: VSAAgentState) -> dict[str, Any]:
    """Run classifier node.
    
    Classifies the user request and determines:
    - Task category (ITIL)
    - Priority (GUT)
    - Methodology to use
    """
    user_request = state["user_request"]
    
    # Classify
    category = classify_task(user_request)
    g, u, t, gut_score = estimate_gut(user_request)
    priority = determine_priority(gut_score)
    methodology = select_methodology(category, user_request)
    
    # Create audit entry
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "node": "classifier",
        "action": "classified",
        "user": None,
        "dry_run": state.get("dry_run", True),
        "success": True,
        "details": {
            "category": category.value,
            "priority": priority.value,
            "methodology": methodology.value,
            "gut": {"G": g, "U": u, "T": t, "score": gut_score}
        }
    }
    
    # Create response message
    message = AIMessage(
        content=f"📊 Classificado como **{category.value.upper()}** "
                f"(Prioridade: {priority.value.upper()}, GUT: {gut_score}) "
                f"usando metodologia **{methodology.value.upper()}**"
    )
    
    return {
        "task_category": category,
        "priority": priority,
        "gut_score": gut_score,
        "methodology": methodology,
        "audit_log": [audit_entry],
        "messages": [message],
    }
