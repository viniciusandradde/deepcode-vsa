"""ITIL Task Classification.

Reference: .claude/skills/vsa-methodologies/SKILL.md
"""

from enum import Enum


class TaskCategory(str, Enum):
    """ITIL task categories with SLA guidance."""
    
    INCIDENT = "incident"   # Unplanned service interruption (SLA: 4h)
    PROBLEM = "problem"     # Root cause of incidents (SLA: 48h)
    CHANGE = "change"       # Planned modification (SLA: varies)
    REQUEST = "request"     # Standard service request (SLA: 24h)


# Classification patterns
PATTERNS: dict[TaskCategory, list[str]] = {
    TaskCategory.INCIDENT: [
        "down", "offline", "failing", "error", "not working",
        "outage", "broken", "crashed", "unavailable", "slow",
        "timeout", "connection refused", "500", "503", "502",
        "caiu", "parou", "não funciona", "erro", "lento"
    ],
    TaskCategory.PROBLEM: [
        "recurring", "keeps failing", "intermittent", "pattern",
        "root cause", "why does", "investigate", "repeated",
        "chronic", "persistent", "recorrente", "causa raiz"
    ],
    TaskCategory.CHANGE: [
        "migrate", "upgrade", "install", "deploy", "update",
        "modify", "configure", "replace", "implement", "rollout",
        "migrar", "atualizar", "instalar", "implantar"
    ],
    TaskCategory.REQUEST: [
        "create user", "reset password", "access", "permissions",
        "setup", "provision", "new account", "onboarding",
        "criar usuário", "resetar senha", "acesso", "permissão"
    ],
}


def classify_task(description: str) -> TaskCategory:
    """Classify task into ITIL category based on description.
    
    Args:
        description: Task description text
        
    Returns:
        TaskCategory matching the description
    """
    text = description.lower()
    
    for category, patterns in PATTERNS.items():
        if any(p in text for p in patterns):
            return category
    
    # Default to request
    return TaskCategory.REQUEST


def get_sla_hours(category: TaskCategory) -> int:
    """Get default SLA hours for category."""
    sla_map = {
        TaskCategory.INCIDENT: 4,
        TaskCategory.PROBLEM: 48,
        TaskCategory.CHANGE: 72,
        TaskCategory.REQUEST: 24,
    }
    return sla_map.get(category, 24)
