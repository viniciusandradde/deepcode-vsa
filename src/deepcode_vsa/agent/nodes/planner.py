"""Planner Node - Generates execution plan based on methodology.

Reference: .claude/skills/vsa-agent-state/SKILL.md
"""

from datetime import datetime
from typing import Any

from langchain_core.messages import AIMessage

from ..state import VSAAgentState, Methodology, TaskCategory


# Plan templates by category
ITIL_PLANS: dict[TaskCategory, list[str]] = {
    TaskCategory.INCIDENT: [
        "1. Identificar sistema/serviço afetado",
        "2. Verificar alertas no Zabbix relacionados",
        "3. Buscar tickets relacionados no GLPI",
        "4. Avaliar impacto e urgência",
        "5. Documentar findings iniciais",
        "6. Propor ações de restauração",
    ],
    TaskCategory.PROBLEM: [
        "1. Coletar histórico de incidentes",
        "2. Identificar padrões de ocorrência",
        "3. Realizar análise de causa raiz (RCA)",
        "4. Propor correção permanente",
        "5. Documentar erro conhecido",
    ],
    TaskCategory.CHANGE: [
        "1. Analisar requisitos da mudança",
        "2. Identificar sistemas impactados",
        "3. Avaliar riscos",
        "4. Definir plano de rollback",
        "5. Documentar RFC",
    ],
    TaskCategory.REQUEST: [
        "1. Validar requisição",
        "2. Verificar autorizações necessárias",
        "3. Executar solicitação",
        "4. Documentar atendimento",
    ],
}

RCA_PLAN = [
    "1. Coletar evidências do problema",
    "2. Aplicar técnica dos 5 Porquês",
    "3. Identificar causa raiz",
    "4. Definir ações preventivas",
    "5. Documentar análise",
]

GUT_PLAN = [
    "1. Listar itens a priorizar",
    "2. Avaliar Gravidade de cada item",
    "3. Avaliar Urgência de cada item",
    "4. Avaliar Tendência de cada item",
    "5. Calcular score GUT (G × U × T)",
    "6. Ordenar por prioridade",
    "7. Gerar relatório priorizado",
]

W5H2_PLAN = [
    "1. Definir O QUE (What)",
    "2. Definir POR QUE (Why)",
    "3. Definir ONDE (Where)",
    "4. Definir QUANDO (When)",
    "5. Definir QUEM (Who)",
    "6. Definir COMO (How)",
    "7. Definir QUANTO (How Much)",
    "8. Consolidar análise 5W2H",
]


def generate_plan(
    methodology: Methodology | None,
    category: TaskCategory | None,
    user_request: str
) -> list[str]:
    """Generate execution plan based on methodology and category."""
    
    if methodology == Methodology.RCA:
        return RCA_PLAN.copy()
    
    if methodology == Methodology.GUT:
        return GUT_PLAN.copy()
    
    if methodology == Methodology.W5H2:
        return W5H2_PLAN.copy()
    
    # Default: ITIL-based plan
    if category:
        return ITIL_PLANS.get(category, ITIL_PLANS[TaskCategory.REQUEST]).copy()
    
    return ITIL_PLANS[TaskCategory.REQUEST].copy()


async def run(state: VSAAgentState) -> dict[str, Any]:
    """Run planner node.
    
    Generates an execution plan based on methodology and task category.
    """
    methodology = state.get("methodology")
    category = state.get("task_category")
    user_request = state["user_request"]
    
    # Generate plan
    plan = generate_plan(methodology, category, user_request)
    
    # Create audit entry
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "node": "planner",
        "action": "planned",
        "user": None,
        "dry_run": state.get("dry_run", True),
        "success": True,
        "details": {
            "steps": len(plan),
            "methodology": methodology.value if methodology else "itil"
        }
    }
    
    # Create response message
    plan_text = "\n".join(plan)
    message = AIMessage(
        content=f"📋 **Plano gerado** ({len(plan)} passos):\n\n{plan_text}"
    )
    
    return {
        "plan": plan,
        "current_step": 0,
        "needs_replan": False,
        "audit_log": [audit_entry],
        "messages": [message],
    }
