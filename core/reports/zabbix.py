"""Zabbix report formatters: problems/alerts to markdown."""

from typing import Any

SEVERITY_LABELS = {
    0: "Não classificado",
    1: "Informação",
    2: "Atenção",
    3: "Média",
    4: "Alta",
    5: "Desastre",
}


def _safe_get(obj: dict, key: str, default: Any = "") -> Any:
    """Get value from dict."""
    val = obj.get(key, default)
    if val is None:
        return default
    return val


def format_alerts_table(problems: list[dict], limit: int = 10) -> str:
    """Formata lista de problemas Zabbix como tabela markdown."""
    if not problems:
        return "Nenhum alerta ativo encontrado."

    lines = [
        "| Severidade | Host | Nome / Descrição |",
        "|------------|------|------------------|",
    ]
    for p in problems[:limit]:
        sev_id = int(_safe_get(p, "severity", 0))
        severity = SEVERITY_LABELS.get(sev_id, str(sev_id))
        name = str(_safe_get(p, "name", _safe_get(p, "clock", "?")))[:60]
        # Zabbix problem may have 'hosts' array or 'name' as problem name
        host = ""
        if "hosts" in p and p["hosts"]:
            host = _safe_get(p["hosts"][0], "name", "") if isinstance(p.get("hosts"), list) else ""
        if not host and "host" in p:
            host = str(p["host"])[:30]
        lines.append(f"| {severity} | {host} | {name} |")

    return "\n".join(lines)


def format_zabbix_report(data: dict) -> str:
    """Relatório completo Zabbix a partir do dict retornado por zabbix_get_alerts."""
    if data.get("error"):
        return f"**Erro ao consultar Zabbix:** {data['error']}"

    problems = data.get("problems") or []
    count = data.get("count", len(problems))
    min_severity = data.get("min_severity", 3)

    by_severity: dict[int, int] = {}
    for p in problems:
        sev = int(p.get("severity", 0))
        by_severity[sev] = by_severity.get(sev, 0) + 1

    report = f"""### Zabbix - Alertas

**Resumo:**

| Total | Média | Alta | Crítico |
|-------|-------|------|---------|
| {count} | {by_severity.get(3, 0)} | {by_severity.get(4, 0)} | {by_severity.get(5, 0)} |

**Alertas ativos (severidade >= {min_severity}):**

{format_alerts_table(problems)}
"""
    return report
