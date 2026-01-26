---
name: vsa-methodologies
description: IT management methodologies for VSA. Use when classifying tasks (ITIL), prioritizing problems (GUT Matrix), performing root cause analysis (RCA/5 Whys), or structuring analysis (5W2H).
---

# VSA Methodologies

## ITIL v4 Task Classification

### Task Categories

```python
from enum import Enum

class TaskCategory(Enum):
    INCIDENT = "incident"      # Service restoration (SLA: 4h)
    PROBLEM = "problem"        # Root cause (RCA needed)
    CHANGE = "change"          # Planned modification
    REQUEST = "request"        # Standard service request
```

### Auto-Classification Rules

```python
CLASSIFICATION_PATTERNS = {
    TaskCategory.INCIDENT: [
        "down", "offline", "failing", "error", "not working",
        "outage", "broken", "crashed", "unavailable"
    ],
    TaskCategory.PROBLEM: [
        "recurring", "keeps failing", "intermittent",
        "pattern", "root cause", "why does", "investigate"
    ],
    TaskCategory.CHANGE: [
        "migrate", "upgrade", "install", "deploy",
        "update", "modify", "configure", "replace"
    ],
    TaskCategory.REQUEST: [
        "create user", "reset password", "access",
        "permissions", "setup", "provision"
    ]
}

def classify_task(description: str) -> TaskCategory:
    text = description.lower()
    for category, patterns in CLASSIFICATION_PATTERNS.items():
        if any(p in text for p in patterns):
            return category
    return TaskCategory.REQUEST
```

---

## GUT Matrix (Prioritization)

### Calculation

```python
from dataclasses import dataclass

@dataclass
class GUTScore:
    gravidade: int      # 1-5: Impact severity
    urgencia: int       # 1-5: Time sensitivity
    tendencia: int      # 1-5: Will it get worse?
    
    @property
    def score(self) -> int:
        return self.gravidade * self.urgencia * self.tendencia
    
    @property
    def priority(self) -> str:
        if self.score >= 100:
            return "CRITICAL"  # G×U×T = 5×5×4+
        elif self.score >= 60:
            return "HIGH"
        elif self.score >= 30:
            return "MEDIUM"
        return "LOW"
```

### Scale Definitions

| Score | Gravidade | Urgência | Tendência |
|-------|-----------|----------|-----------|
| 5 | Extremely serious | Immediate action | Gets much worse quickly |
| 4 | Very serious | Urgent | Gets worse short-term |
| 3 | Serious | Soon as possible | Gets worse medium-term |
| 2 | Little serious | Can wait | Gets worse long-term |
| 1 | Not serious | No rush | Does not get worse |

### Auto-Scoring Patterns

```python
SEVERITY_PATTERNS = {
    5: ["production down", "data loss", "security breach", "critical"],
    4: ["major impact", "many users", "revenue", "core system"],
    3: ["moderate impact", "some users", "workaround exists"],
    2: ["minor impact", "few users", "cosmetic"],
    1: ["no impact", "enhancement", "nice to have"]
}

def estimate_gut(description: str, affected_users: int = 0) -> GUTScore:
    text = description.lower()
    
    # Estimate gravity
    gravidade = 3
    for score, patterns in SEVERITY_PATTERNS.items():
        if any(p in text for p in patterns):
            gravidade = score
            break
    
    # Estimate urgency based on keywords
    urgencia = 3
    if any(w in text for w in ["immediately", "asap", "urgent", "now"]):
        urgencia = 5
    elif any(w in text for w in ["today", "critical"]):
        urgencia = 4
    
    # Estimate tendency
    tendencia = 3
    if any(w in text for w in ["recurring", "getting worse", "spreading"]):
        tendencia = 5
    
    return GUTScore(gravidade, urgencia, tendencia)
```

---

## RCA - Root Cause Analysis (5 Whys)

### Process

```python
from pydantic import BaseModel
from typing import Optional

class RCAStep(BaseModel):
    question: str
    answer: str
    evidence: Optional[str] = None

class RCAResult(BaseModel):
    initial_problem: str
    whys: list[RCAStep]
    root_cause: str
    preventive_actions: list[str]

async def perform_rca(problem: str, llm_client) -> RCAResult:
    """Perform 5 Whys analysis with LLM assistance."""
    whys = []
    current_answer = problem
    
    for i in range(5):
        question = f"Why {i+1}: Why is '{current_answer}' happening?"
        
        # Get answer from LLM or investigation
        answer = await llm_client.ask(
            f"Given the problem chain:\n{format_chain(whys)}\n\n"
            f"Answer: {question}"
        )
        
        whys.append(RCAStep(
            question=question,
            answer=answer
        ))
        
        current_answer = answer
        
        # Stop if we found actionable root cause
        if is_actionable(answer):
            break
    
    return RCAResult(
        initial_problem=problem,
        whys=whys,
        root_cause=current_answer,
        preventive_actions=generate_actions(current_answer)
    )
```

### Example RCA Flow

```
Problem: "Backup failing for 3 days"

WHY 1: Why is backup failing?
→ pg_dump: connection refused

WHY 2: Why connection refused?
→ PostgreSQL not responding to new connections

WHY 3: Why not responding?
→ Max connections limit reached (100/100)

WHY 4: Why max connections reached?
→ Connection pool not releasing connections

WHY 5: Why pool not releasing?
→ pgbouncer misconfigured (max_client_conn too low)

ROOT CAUSE: pgbouncer configuration error
ACTIONS:
  1. Increase max_client_conn in pgbouncer.ini
  2. Restart pgbouncer service
  3. Add Zabbix alert for connection usage > 80%
  4. Document in runbook
```

---

## 5W2H Analysis

### Structure

```python
@dataclass
class Analysis5W2H:
    what: str        # What is the problem/situation?
    why: str         # Why is it happening?
    where: str       # Where is it occurring?
    when: str        # When did it start/happen?
    who: str         # Who is affected/responsible?
    how: str         # How to solve/implement?
    how_much: str    # How much will it cost/impact?

def format_5w2h(analysis: Analysis5W2H) -> str:
    return f"""
## 5W2H Analysis

| Question | Answer |
|----------|--------|
| **WHAT** | {analysis.what} |
| **WHY** | {analysis.why} |
| **WHERE** | {analysis.where} |
| **WHEN** | {analysis.when} |
| **WHO** | {analysis.who} |
| **HOW** | {analysis.how} |
| **HOW MUCH** | {analysis.how_much} |
"""
```

---

## Integration in VSA Agent

```python
class MethodologyMixin:
    async def apply_methodology(
        self, 
        methodology: Methodology,
        context: dict
    ) -> dict:
        if methodology == Methodology.ITIL:
            return await self._apply_itil(context)
        elif methodology == Methodology.GUT:
            return await self._apply_gut(context)
        elif methodology == Methodology.RCA:
            return await self._apply_rca(context)
        elif methodology == Methodology.W5H2:
            return await self._apply_5w2h(context)
    
    async def _apply_itil(self, context: dict) -> dict:
        category = classify_task(context["description"])
        return {
            "category": category,
            "sla": SLA_BY_CATEGORY[category],
            "workflow": WORKFLOW_BY_CATEGORY[category]
        }
    
    async def _apply_gut(self, context: dict) -> dict:
        score = estimate_gut(
            context["description"],
            context.get("affected_users", 0)
        )
        return {
            "gut_score": score.score,
            "priority": score.priority,
            "details": {
                "G": score.gravidade,
                "U": score.urgencia,
                "T": score.tendencia
            }
        }
```
