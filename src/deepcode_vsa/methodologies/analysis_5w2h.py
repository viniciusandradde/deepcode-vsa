"""5W2H Analysis.

Reference: .claude/skills/vsa-methodologies/SKILL.md
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Analysis5W2H:
    """5W2H Analysis structure.
    
    Answers the 7 fundamental questions:
    - What: What is the problem/task?
    - Why: Why is it important?
    - Where: Where does it occur/apply?
    - When: When should it be done?
    - Who: Who is responsible?
    - How: How will it be done?
    - How Much: What are the costs/resources?
    """
    
    title: str
    
    # 5W
    what: Optional[str] = None
    why: Optional[str] = None
    where: Optional[str] = None
    when: Optional[str] = None
    who: Optional[str] = None
    
    # 2H
    how: Optional[str] = None
    how_much: Optional[str] = None
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    notes: list[str] = field(default_factory=list)
    
    @property
    def is_complete(self) -> bool:
        """Check if all 7 questions are answered."""
        return all([
            self.what,
            self.why,
            self.where,
            self.when,
            self.who,
            self.how,
            self.how_much
        ])
    
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        fields = [self.what, self.why, self.where, self.when, 
                  self.who, self.how, self.how_much]
        answered = sum(1 for f in fields if f)
        return (answered / 7) * 100


def create_5w2h(title: str) -> Analysis5W2H:
    """Create a new 5W2H analysis.
    
    Args:
        title: Title/subject of the analysis
        
    Returns:
        Empty Analysis5W2H ready to be populated
    """
    return Analysis5W2H(title=title)


def format_5w2h_report(analysis: Analysis5W2H) -> str:
    """Format 5W2H as a text report."""
    lines = [
        f"# 5W2H Analysis: {analysis.title}",
        "",
        f"**Created:** {analysis.created_at}",
        f"**Completion:** {analysis.completion_percentage:.0f}%",
        "",
        "## Questions & Answers",
        "",
        f"### What? (O quê?)",
        analysis.what or "_Not answered_",
        "",
        f"### Why? (Por quê?)",
        analysis.why or "_Not answered_",
        "",
        f"### Where? (Onde?)",
        analysis.where or "_Not answered_",
        "",
        f"### When? (Quando?)",
        analysis.when or "_Not answered_",
        "",
        f"### Who? (Quem?)",
        analysis.who or "_Not answered_",
        "",
        f"### How? (Como?)",
        analysis.how or "_Not answered_",
        "",
        f"### How Much? (Quanto?)",
        analysis.how_much or "_Not answered_",
    ]
    
    if analysis.notes:
        lines.extend([
            "",
            "## Notes",
            ""
        ])
        for note in analysis.notes:
            lines.append(f"- {note}")
    
    return "\n".join(lines)
