"""Root Cause Analysis (5 Whys).

Reference: .claude/skills/vsa-methodologies/SKILL.md
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class WhyEntry:
    """Single entry in the 5 Whys chain."""
    
    level: int
    question: str
    answer: str
    evidence: Optional[str] = None


@dataclass
class RCAResult:
    """Result of Root Cause Analysis.
    
    Contains the complete 5 Whys chain, 
    identified root cause, and preventive actions.
    """
    
    problem_statement: str
    whys: list[WhyEntry] = field(default_factory=list)
    root_cause: Optional[str] = None
    contributing_factors: list[str] = field(default_factory=list)
    immediate_actions: list[str] = field(default_factory=list)
    preventive_actions: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def add_why(self, question: str, answer: str, evidence: str = None) -> None:
        """Add a Why to the chain."""
        level = len(self.whys) + 1
        self.whys.append(WhyEntry(
            level=level,
            question=question,
            answer=answer,
            evidence=evidence
        ))
    
    def set_root_cause(self, cause: str) -> None:
        """Set the identified root cause."""
        self.root_cause = cause
    
    @property
    def is_complete(self) -> bool:
        """Check if RCA has identified root cause."""
        return self.root_cause is not None and len(self.whys) >= 3


def create_rca(problem: str) -> RCAResult:
    """Create a new RCA for a problem.
    
    Args:
        problem: Initial problem statement
        
    Returns:
        Empty RCAResult ready to be populated
    """
    return RCAResult(problem_statement=problem)


async def perform_rca(problem: str, llm_client=None) -> RCAResult:
    """Perform automated RCA using LLM.
    
    If no LLM client is provided, returns a template
    for manual completion.
    
    Args:
        problem: Problem to analyze
        llm_client: Optional LLM client for AI-assisted analysis
        
    Returns:
        RCAResult with analysis
    """
    rca = create_rca(problem)
    
    if llm_client is None:
        # Return template for manual RCA
        rca.add_why(
            question=f"Why is {problem}?",
            answer="[To be investigated]"
        )
        rca.add_why(
            question="Why? (Level 2)",
            answer="[To be investigated]"
        )
        rca.add_why(
            question="Why? (Level 3)",
            answer="[To be investigated]"
        )
        rca.add_why(
            question="Why? (Level 4)",
            answer="[To be investigated]"
        )
        rca.add_why(
            question="Why? (Level 5 - Root Cause)",
            answer="[To be identified]"
        )
        return rca
    
    # TODO: Implement LLM-assisted RCA
    # This would use the LLM to iteratively ask and answer
    # the 5 Whys and identify the root cause
    
    return rca


def format_rca_report(rca: RCAResult) -> str:
    """Format RCA as a text report."""
    lines = [
        "# Root Cause Analysis Report",
        "",
        f"**Problem:** {rca.problem_statement}",
        f"**Date:** {rca.timestamp}",
        "",
        "## 5 Whys Analysis",
        ""
    ]
    
    for why in rca.whys:
        lines.append(f"### Level {why.level}")
        lines.append(f"**Q:** {why.question}")
        lines.append(f"**A:** {why.answer}")
        if why.evidence:
            lines.append(f"**Evidence:** {why.evidence}")
        lines.append("")
    
    if rca.root_cause:
        lines.extend([
            "## Root Cause",
            "",
            f"🎯 {rca.root_cause}",
            ""
        ])
    
    if rca.preventive_actions:
        lines.extend([
            "## Preventive Actions",
            ""
        ])
        for i, action in enumerate(rca.preventive_actions, 1):
            lines.append(f"{i}. {action}")
    
    return "\n".join(lines)
