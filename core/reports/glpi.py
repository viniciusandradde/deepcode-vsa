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
