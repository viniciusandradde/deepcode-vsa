---
name: vsa-audit-compliance
description: Audit logging and compliance patterns for VSA. Use when implementing audit trails, compliance checks, LGPD validation, or generating audit reports.
---

# VSA Audit & Compliance Patterns

## Audit Log Structure

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any
from enum import Enum

class AuditAction(str, Enum):
    CLASSIFIED = "classified"
    PLANNED = "planned"
    EXECUTED = "executed"
    ANALYZED = "analyzed"
    INTEGRATED = "integrated"
    APPROVED = "approved"
    REJECTED = "rejected"
    ERROR = "error"

class AuditEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: str
    node: str
    action: AuditAction
    user: Optional[str] = None
    dry_run: bool = True
    details: Optional[dict] = None
    success: bool = True
    error_message: Optional[str] = None

class AuditLog:
    def __init__(self, session_id: str, user: str = None):
        self.session_id = session_id
        self.user = user or os.getenv("USER", "unknown")
        self.entries: list[AuditEntry] = []
    
    def log(
        self,
        node: str,
        action: AuditAction,
        dry_run: bool = True,
        details: dict = None,
        success: bool = True,
        error_message: str = None
    ) -> AuditEntry:
        entry = AuditEntry(
            session_id=self.session_id,
            node=node,
            action=action,
            user=self.user,
            dry_run=dry_run,
            details=details,
            success=success,
            error_message=error_message
        )
        self.entries.append(entry)
        return entry
    
    def to_dict(self) -> list[dict]:
        return [e.model_dump() for e in self.entries]
```

---

## Compliance Rules

```python
from dataclasses import dataclass
from typing import Callable

@dataclass
class ComplianceRule:
    name: str
    description: str
    check: Callable[[dict], bool]
    severity: str  # critical, warning, info

COMPLIANCE_RULES = [
    ComplianceRule(
        name="dry_run_for_write",
        description="Write operations must have dry_run before execution",
        check=lambda state: all(
            tc.get("dry_run_first", True) 
            for tc in state.get("tool_calls", [])
            if tc.get("type") == "write"
        ),
        severity="critical"
    ),
    ComplianceRule(
        name="no_delete_operations",
        description="DELETE operations are blocked in v1",
        check=lambda state: not any(
            tc.get("type") == "delete"
            for tc in state.get("tool_calls", [])
        ),
        severity="critical"
    ),
    ComplianceRule(
        name="audit_complete",
        description="All nodes must have audit entries",
        check=lambda state: len(state.get("audit_log", [])) >= 4,
        severity="warning"
    ),
    ComplianceRule(
        name="methodology_applied",
        description="A methodology must be selected and applied",
        check=lambda state: state.get("methodology") is not None,
        severity="warning"
    ),
    ComplianceRule(
        name="lgpd_data_access",
        description="Personal data access must be logged",
        check=lambda state: _check_lgpd_compliance(state),
        severity="critical"
    )
]

def _check_lgpd_compliance(state: dict) -> bool:
    """Check if personal data access is properly logged."""
    personal_data_accessed = state.get("personal_data_accessed", False)
    if not personal_data_accessed:
        return True  # No personal data = compliant
    
    # Must have explicit log entry for personal data access
    return any(
        entry.get("details", {}).get("data_type") == "personal"
        for entry in state.get("audit_log", [])
    )
```

---

## Compliance Checker

```python
@dataclass
class ComplianceResult:
    passed: bool
    violations: list[dict]
    warnings: list[dict]
    score: float  # 0-100

class ComplianceChecker:
    def __init__(self, rules: list[ComplianceRule] = None):
        self.rules = rules or COMPLIANCE_RULES
    
    def check(self, state: dict) -> ComplianceResult:
        violations = []
        warnings = []
        
        for rule in self.rules:
            try:
                passed = rule.check(state)
                if not passed:
                    entry = {
                        "rule": rule.name,
                        "description": rule.description,
                        "severity": rule.severity
                    }
                    if rule.severity == "critical":
                        violations.append(entry)
                    else:
                        warnings.append(entry)
            except Exception as e:
                violations.append({
                    "rule": rule.name,
                    "description": f"Check failed: {e}",
                    "severity": "error"
                })
        
        # Calculate score
        total_rules = len(self.rules)
        passed_rules = total_rules - len(violations) - len(warnings) * 0.5
        score = (passed_rules / total_rules) * 100
        
        return ComplianceResult(
            passed=len(violations) == 0,
            violations=violations,
            warnings=warnings,
            score=score
        )
```

---

## Audit Report Generator

```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

def generate_audit_report(
    audit_log: AuditLog,
    compliance: ComplianceResult,
    output_format: str = "rich"
) -> str:
    """Generate formatted audit report."""
    
    if output_format == "rich":
        console = Console(record=True)
        
        # Header
        console.print(Panel(
            "[bold cyan]VSA DeepCode - Audit Report[/]",
            border_style="cyan"
        ))
        
        # Session Info
        info_table = Table(show_header=False)
        info_table.add_column("Key", style="cyan")
        info_table.add_column("Value")
        info_table.add_row("Session ID", audit_log.session_id)
        info_table.add_row("User", audit_log.user)
        info_table.add_row("Entries", str(len(audit_log.entries)))
        info_table.add_row("Timestamp", datetime.utcnow().isoformat())
        console.print(info_table)
        
        # Audit Trail
        console.print("\n[bold]📋 Audit Trail:[/]")
        trail_table = Table(show_header=True)
        trail_table.add_column("Time", width=12)
        trail_table.add_column("Node", width=12)
        trail_table.add_column("Action", width=12)
        trail_table.add_column("Dry Run", width=8)
        trail_table.add_column("Status", width=8)
        
        for entry in audit_log.entries:
            status = "[green]✓[/]" if entry.success else "[red]✗[/]"
            dry = "[yellow]Yes[/]" if entry.dry_run else "[green]No[/]"
            trail_table.add_row(
                entry.timestamp.strftime("%H:%M:%S"),
                entry.node,
                entry.action.value,
                dry,
                status
            )
        console.print(trail_table)
        
        # Compliance
        console.print("\n[bold]🛡️ Compliance:[/]")
        status = "[bold green]✅ PASSED[/]" if compliance.passed else "[bold red]❌ FAILED[/]"
        console.print(f"Status: {status}")
        console.print(f"Score: {compliance.score:.0f}/100")
        
        if compliance.violations:
            console.print("\n[bold red]Violations:[/]")
            for v in compliance.violations:
                console.print(f"  • {v['rule']}: {v['description']}")
        
        if compliance.warnings:
            console.print("\n[bold yellow]Warnings:[/]")
            for w in compliance.warnings:
                console.print(f"  • {w['rule']}: {w['description']}")
        
        return console.export_text()
    
    elif output_format == "json":
        return json.dumps({
            "session_id": audit_log.session_id,
            "user": audit_log.user,
            "entries": audit_log.to_dict(),
            "compliance": {
                "passed": compliance.passed,
                "score": compliance.score,
                "violations": compliance.violations,
                "warnings": compliance.warnings
            }
        }, indent=2, default=str)
    
    elif output_format == "markdown":
        return f"""
# VSA Audit Report

**Session:** {audit_log.session_id}  
**User:** {audit_log.user}  
**Timestamp:** {datetime.utcnow().isoformat()}

## Compliance Status

- **Status:** {'✅ PASSED' if compliance.passed else '❌ FAILED'}
- **Score:** {compliance.score:.0f}/100

## Audit Trail

| Time | Node | Action | Dry Run | Status |
|------|------|--------|---------|--------|
{chr(10).join(f"| {e.timestamp.strftime('%H:%M:%S')} | {e.node} | {e.action.value} | {'Yes' if e.dry_run else 'No'} | {'✓' if e.success else '✗'} |" for e in audit_log.entries)}

## Violations

{chr(10).join(f"- **{v['rule']}**: {v['description']}" for v in compliance.violations) if compliance.violations else "None"}

## Warnings

{chr(10).join(f"- **{w['rule']}**: {w['description']}" for w in compliance.warnings) if compliance.warnings else "None"}
"""
```

---

## Usage in Agent

```python
class VSAAgent:
    def __init__(self, user: str = None, dry_run: bool = True):
        self.session_id = str(uuid.uuid4())[:8]
        self.dry_run = dry_run
        self.audit = AuditLog(self.session_id, user)
        self.compliance = ComplianceChecker()
    
    async def run(self, request: str) -> dict:
        # Log start
        self.audit.log("main", AuditAction.STARTED, dry_run=self.dry_run)
        
        try:
            # Run agent workflow
            result = await self._run_workflow(request)
            
            # Check compliance
            state = self._get_final_state()
            compliance_result = self.compliance.check(state)
            
            # Log completion
            self.audit.log(
                "main",
                AuditAction.COMPLETED,
                dry_run=self.dry_run,
                details={"compliance_passed": compliance_result.passed}
            )
            
            # Generate report
            report = generate_audit_report(
                self.audit,
                compliance_result,
                output_format="rich"
            )
            
            return {
                "result": result,
                "audit_report": report,
                "compliance": compliance_result
            }
            
        except Exception as e:
            self.audit.log(
                "main",
                AuditAction.ERROR,
                success=False,
                error_message=str(e)
            )
            raise
```
