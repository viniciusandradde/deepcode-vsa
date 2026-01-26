"""GUT Matrix Prioritization.

Reference: .claude/skills/vsa-methodologies/SKILL.md
"""

from dataclasses import dataclass
from enum import Enum


class Priority(str, Enum):
    """Priority levels based on GUT score."""
    
    CRITICAL = "critical"  # Score >= 100
    HIGH = "high"          # Score >= 60
    MEDIUM = "medium"      # Score >= 30
    LOW = "low"            # Score < 30


@dataclass
class GUTScore:
    """GUT Matrix score.
    
    G - Gravidade (Gravity): How severe is the impact?
    U - Urgência (Urgency): How soon must it be resolved?
    T - Tendência (Tendency): Will it get worse over time?
    
    Each factor is rated 1-5:
        1 = Very low
        2 = Low
        3 = Medium
        4 = High
        5 = Very high
    """
    
    gravidade: int  # 1-5
    urgencia: int   # 1-5
    tendencia: int  # 1-5
    
    def __post_init__(self):
        # Validate ranges
        for attr in ('gravidade', 'urgencia', 'tendencia'):
            value = getattr(self, attr)
            if not 1 <= value <= 5:
                raise ValueError(f"{attr} must be between 1 and 5")
    
    @property
    def score(self) -> int:
        """Calculate GUT score (G × U × T)."""
        return self.gravidade * self.urgencia * self.tendencia
    
    @property
    def priority(self) -> Priority:
        """Determine priority from score."""
        if self.score >= 100:
            return Priority.CRITICAL
        elif self.score >= 60:
            return Priority.HIGH
        elif self.score >= 30:
            return Priority.MEDIUM
        return Priority.LOW


# Estimation patterns
GRAVITY_PATTERNS: dict[int, list[str]] = {
    5: ["production down", "data loss", "security breach", "critical", "p1", "emergency", "produção parada"],
    4: ["major impact", "many users", "revenue", "core system", "p2", "importante"],
    3: ["moderate impact", "some users", "workaround exists", "moderado"],
    2: ["minor impact", "few users", "cosmetic", "p4", "baixo impacto"],
    1: ["no impact", "enhancement", "nice to have", "p5", "melhoria"],
}

URGENCY_PATTERNS: dict[int, list[str]] = {
    5: ["immediately", "asap", "urgent", "agora", "now", "imediato"],
    4: ["today", "hoje", "critical", "end of day"],
    3: ["this week", "esta semana", "soon"],
    2: ["can wait", "quando puder", "low priority"],
    1: ["no rush", "sem pressa", "whenever"],
}

TENDENCY_PATTERNS: dict[int, list[str]] = {
    5: ["getting worse", "piorando", "spreading", "escalating"],
    4: ["deteriorating", "increasing", "growing"],
    3: ["stable", "estável", "unchanged"],
    2: ["improving", "melhorando", "decreasing"],
    1: ["resolving", "resolvendo", "going away"],
}


def estimate_gut(description: str) -> GUTScore:
    """Estimate GUT score from description text.
    
    Args:
        description: Problem description
        
    Returns:
        GUTScore with estimated values
    """
    text = description.lower()
    
    # Estimate each factor
    gravidade = _estimate_factor(text, GRAVITY_PATTERNS, default=3)
    urgencia = _estimate_factor(text, URGENCY_PATTERNS, default=3)
    tendencia = _estimate_factor(text, TENDENCY_PATTERNS, default=3)
    
    return GUTScore(gravidade=gravidade, urgencia=urgencia, tendencia=tendencia)


def _estimate_factor(text: str, patterns: dict[int, list[str]], default: int) -> int:
    """Estimate a single GUT factor from text patterns."""
    for score, keywords in sorted(patterns.items(), reverse=True):
        if any(k in text for k in keywords):
            return score
    return default


def calculate_priority(score: int) -> Priority:
    """Calculate priority from raw GUT score."""
    if score >= 100:
        return Priority.CRITICAL
    elif score >= 60:
        return Priority.HIGH
    elif score >= 30:
        return Priority.MEDIUM
    return Priority.LOW
