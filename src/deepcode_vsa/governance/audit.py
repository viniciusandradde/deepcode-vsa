"""Audit Logging for compliance.

Reference: .claude/skills/vsa-audit-compliance/SKILL.md
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import json


class AuditAction(str, Enum):
    """Audit action types."""
    
    STARTED = "started"
    CLASSIFIED = "classified"
    PLANNED = "planned"
    EXECUTED = "executed"
    ANALYZED = "analyzed"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class AuditEntry:
    """Single audit log entry."""
    
    timestamp: str
    session_id: str
    node: str
    action: AuditAction
    user: Optional[str] = None
    dry_run: bool = True
    success: bool = True
    details: Optional[dict] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "node": self.node,
            "action": self.action.value,
            "user": self.user,
            "dry_run": self.dry_run,
            "success": self.success,
            "details": self.details,
            "error_message": self.error_message,
        }


class AuditLog:
    """Audit log manager.
    
    Maintains a log of all agent actions for compliance
    and debugging purposes.
    """
    
    def __init__(self, session_id: str, user: str = None):
        self.session_id = session_id
        self.user = user
        self.entries: list[AuditEntry] = []
    
    def log(
        self,
        node: str,
        action: AuditAction,
        dry_run: bool = True,
        success: bool = True,
        details: dict = None,
        error_message: str = None
    ) -> AuditEntry:
        """Add new audit entry.
        
        Args:
            node: Node/component that performed the action
            action: Type of action
            dry_run: Whether this was a dry run
            success: Whether action succeeded
            details: Additional details
            error_message: Error message if failed
            
        Returns:
            Created AuditEntry
        """
        entry = AuditEntry(
            timestamp=datetime.utcnow().isoformat(),
            session_id=self.session_id,
            node=node,
            action=action,
            user=self.user,
            dry_run=dry_run,
            success=success,
            details=details,
            error_message=error_message
        )
        self.entries.append(entry)
        return entry
    
    def to_json(self) -> str:
        """Export log as JSON."""
        return json.dumps(
            [e.to_dict() for e in self.entries],
            indent=2,
            default=str
        )
    
    def get_summary(self) -> dict:
        """Get audit summary."""
        return {
            "session_id": self.session_id,
            "user": self.user,
            "total_entries": len(self.entries),
            "successful": sum(1 for e in self.entries if e.success),
            "failed": sum(1 for e in self.entries if not e.success),
            "dry_run_count": sum(1 for e in self.entries if e.dry_run),
        }
