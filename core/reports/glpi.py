"""GLPI report formatters: tickets to markdown."""

from typing import Any


# GLPI status IDs -> label (common mapping)
STATUS_LABELS = {
    1: "Novo",
    2: "Processando",
    3: "Planejado",
    4: "Pendente",
    5: "Resolvido",
    6: "Fechado",
}

PRIORITY_LABELS = {
    1: "Muito baixa",
    2: "Baixa",
    3: "Média",
    4: "Alta",
    5: "Muito alta",
    6: "Crítica",
}


def _safe_get(obj: dict, key: str, default: Any = "") -> Any:
    """Get value from dict, handling nested keys."""
    val = obj.get(key, default)
    if val is None:
        return default
    return val


def format_tickets_table(tickets: list[dict], limit: int = 10) -> str:
    """Formata lista de tickets como tabela markdown."""
    if not tickets:
        return "Nenhum ticket encontrado."

    lines = [
        "| ID | Título | Status | Prioridade |",
        "|-----|--------|--------|------------|",
    ]
    for t in tickets[:limit]:
        tid = _safe_get(t, "id", "?")
        name = str(_safe_get(t, "name", "(sem título)"))[:50]
        status_id = _safe_get(t, "status")
        priority_id = _safe_get(t, "priority")
        status = STATUS_LABELS.get(status_id, str(status_id)) if status_id else "?"
        priority = PRIORITY_LABELS.get(priority_id, str(priority_id)) if priority_id else "?"
        lines.append(f"| #{tid} | {name} | {status} | {priority} |")

    return "\n".join(lines)


def format_glpi_report(data: dict) -> str:
    """Relatório completo GLPI a partir do dict retornado por glpi_get_tickets."""
    if data.get("error"):
        return f"**Erro ao consultar GLPI:** {data['error']}"

    tickets = data.get("tickets") or []
    count = data.get("count", len(tickets))

    by_status: dict[Any, int] = {}
    for t in tickets:
        s = t.get("status")
        by_status[s] = by_status.get(s, 0) + 1

    report = f"""### GLPI - Tickets

**Resumo:**

| Total | Novo | Processando | Resolvido |
|-------|------|-------------|-----------|
| {count} | {by_status.get(1, 0)} | {by_status.get(2, 0)} | {by_status.get(5, 0)} |

**Últimos tickets:**

{format_tickets_table(tickets)}
"""
    return report


def format_tickets_table_with_date(tickets: list[dict], limit: int = 15) -> str:
    """Formata lista de tickets como tabela markdown incluindo data de criação."""
    if not tickets:
        return "Nenhum ticket encontrado."

    lines = [
        "| ID | Título | Criado em | Prioridade |",
        "|-----|--------|-----------|------------|",
    ]
    for t in tickets[:limit]:
        tid = _safe_get(t, "id", "?")
        name = str(_safe_get(t, "name", "(sem título)"))[:45]
        date_str = _safe_get(t, "date") or _safe_get(t, "date_creation", "?")
        # Format date to DD/MM/YYYY HH:MM
        if date_str and date_str != "?":
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(date_str.replace(" ", "T"))
                date_str = dt.strftime("%d/%m/%Y %H:%M")
            except (ValueError, TypeError):
                pass
        priority_id = _safe_get(t, "priority")
        priority = PRIORITY_LABELS.get(priority_id, str(priority_id)) if priority_id else "?"
        lines.append(f"| #{tid} | {name} | {date_str} | {priority} |")

    return "\n".join(lines)


def format_new_unassigned_report(data: dict) -> str:
    """Relatório de tickets novos sem atribuição há mais de 24h."""
    if data.get("error"):
        return f"**Erro ao consultar GLPI:** {data['error']}"

    tickets = data.get("tickets") or []
    count = data.get("count", len(tickets))
    total_found = data.get("total_found", count)
    min_hours = data.get("min_age_hours", 24)

    if count == 0:
        return f"""### Chamados Novos sem Atribuição

Nenhum chamado novo sem atribuição há mais de {min_hours}h.

**Situação:** Todos os chamados novos estão atribuídos ou foram criados recentemente.
"""

    report = f"""### Chamados Novos sem Atribuição (> {min_hours}h)

**Atenção:** {total_found} chamado(s) aguardando atribuição!

{format_tickets_table_with_date(tickets)}

**Ação recomendada:** Atribuir técnico responsável para cada chamado listado acima.
"""
    return report


def format_pending_old_report(data: dict) -> str:
    """Relatório de tickets pendentes há mais de 7 dias."""
    if data.get("error"):
        return f"**Erro ao consultar GLPI:** {data['error']}"

    tickets = data.get("tickets") or []
    count = data.get("count", len(tickets))
    total_found = data.get("total_found", count)
    min_days = data.get("min_age_days", 7)

    if count == 0:
        return f"""### Chamados Pendentes Antigos

Nenhum chamado pendente há mais de {min_days} dias.

**Situação:** Todos os chamados pendentes foram atualizados recentemente.
"""

    report = f"""### Chamados Pendentes há mais de {min_days} dias

**Atenção:** {total_found} chamado(s) parado(s) há muito tempo!

{format_tickets_table_with_date(tickets)}

**Ação recomendada:** 
- Verificar se há bloqueio ou dependência externa
- Considerar escalonamento se necessário
- Atualizar o chamado com informações de status
"""
    return report
