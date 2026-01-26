"""VSA Agent State definition.

Reference: .claude/skills/vsa-agent-state/SKILL.md
"""

from datetime import datetime
from enum import Enum
from typing import Annotated, Optional, TypedDict

from langgraph.graph.message import add_messages


class Methodology(str, Enum):
    """IT management methodologies."""
    
    ITIL = "itil"
    GUT = "gut"
    RCA = "rca"
    W5H2 = "5w2h"
    PDCA = "pdca"


class TaskCategory(str, Enum):
    """ITIL task categories."""
    
    INCIDENT = "incident"   # Service restoration (SLA: 4h)
    PROBLEM = "problem"     # Root cause (RCA needed)
    CHANGE = "change"       # Planned modification
    REQUEST = "request"     # Standard service request


class Priority(str, Enum):
    """Task priority levels."""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AuditEntry(TypedDict):
    """Audit log entry structure."""
    
    timestamp: str
    node: str
    action: str
    user: Optional[str]
    dry_run: bool
    success: bool
    details: Optional[dict]


class VSAAgentState(TypedDict):
    """Complete VSA Agent State for LangGraph.
    
    Extends base agent state with VSA-specific fields:
    - Methodology selection (ITIL, GUT, RCA, 5W2H)
    - Task classification and prioritization
    - Integration contexts (GLPI, Zabbix)
    - Audit and compliance tracking
    """
    
    # Base fields (LangGraph)
    messages: Annotated[list, add_messages]
    
    # User request
    user_request: str
    
    # Planning
    plan: Optional[list[str]]
    current_step: int
    
    # Methodology & Classification
    methodology: Optional[Methodology]
    task_category: Optional[TaskCategory]
    priority: Optional[Priority]
    gut_score: Optional[int]
    
    # Tool execution
    tool_calls: list[dict]
    tool_results: list[dict]
    
    # Integration contexts
    glpi_context: Optional[dict]
    zabbix_context: Optional[dict]
    
    # Control flow
    should_continue: bool
    needs_replan: bool
    error: Optional[str]
    
    # Audit & Compliance
    audit_log: list[AuditEntry]
    compliance_checked: bool
    dry_run: bool
    
    # Session
    session_id: str
    started_at: str


def create_initial_state(
    user_request: str,
    session_id: str,
    dry_run: bool = True
) -> VSAAgentState:
    """Create initial agent state."""
    return VSAAgentState(
        messages=[],
        user_request=user_request,
        plan=None,
        current_step=0,
        methodology=None,
        task_category=None,
        priority=None,
        gut_score=None,
        tool_calls=[],
        tool_results=[],
        glpi_context=None,
        zabbix_context=None,
        should_continue=True,
        needs_replan=False,
        error=None,
        audit_log=[],
        compliance_checked=False,
        dry_run=dry_run,
        session_id=session_id,
        started_at=datetime.utcnow().isoformat(),
    )
