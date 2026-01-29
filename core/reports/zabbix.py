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

# Tamanho máximo da descrição do evento na tabela
EVENT_DESC_MAX_LEN = 55


def _safe_get(obj: dict, key: str, default: Any = "") -> Any:
    """Get value from dict."""
    val = obj.get(key, default)
    if val is None:
        return default
    return val


def _zabbix_frontend_base(base_url: str | None) -> str:
    """Remove /api_jsonrpc.php da URL da API para obter a base do frontend."""
    if not base_url or not base_url.strip():
        return ""
    base = base_url.rstrip("/")
    if base.endswith("/api_jsonrpc.php"):
        return base[: -len("/api_jsonrpc.php")]
    return base


def _summarize_event_name(name: str, max_len: int = EVENT_DESC_MAX_LEN) -> str:
    """Resume a descrição do evento: trunca e remove sufixos repetitivos."""
    if not name:
        return "?"
    s = name.strip()
    # Remove sufixos comuns longos entre parênteses no final
    for suffix in (" (Serviço do Google Update)", " (Serviço interno", " (Clipboard User Service", " (Serviço Microsoft Edge Update"):
        if suffix in s and s.index(suffix) >= 20:
            s = s.split(suffix)[0].strip()
    if len(s) > max_len:
        s = s[: max_len - 1].rstrip() + "…"
    return s or "?"


def format_alerts_table(
    problems: list[dict],
    limit: int = 10,
    zabbix_base_url: str | None = None,
) -> str:
    """Formata lista de problemas Zabbix como tabela markdown (host, descrição resumida, link)."""
    if not problems:
        return "Nenhum alerta ativo encontrado."

    base = _zabbix_frontend_base(zabbix_base_url)
    has_link = bool(base)

    header = "| Severidade | Host | Nome / Descrição |"
    if has_link:
        header += " Link |"
    lines = [header, "|------------|------|------------------|" + ("--------|" if has_link else "")]

    for p in problems[:limit]:
        sev_id = int(_safe_get(p, "severity", 0))
        severity = SEVERITY_LABELS.get(sev_id, str(sev_id))
        host_src = _safe_get(p, "host_name", "")
        if not host_src and isinstance(p.get("hosts"), list) and p["hosts"]:
            host_src = _safe_get(p["hosts"][0], "name", "")
        if not host_src:
            host_src = _safe_get(p, "host", "")
        host = str(host_src)[:30]
        raw_name = str(_safe_get(p, "name", _safe_get(p, "clock", "?")))
        name = _summarize_event_name(raw_name)
        row = f"| {severity} | {host} | {name} |"
        if has_link:
            objectid = p.get("objectid")
            eventid = p.get("eventid")
            if objectid and eventid:
                url = f"{base}/tr_events.php?triggerid={objectid}&eventid={eventid}"
                row += f" [Abrir]({url}) |"
            else:
                row += " |"
        lines.append(row)

    return "\n".join(lines)


def format_zabbix_report(data: dict, zabbix_base_url: str | None = None) -> str:
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

{format_alerts_table(problems, zabbix_base_url=zabbix_base_url)}
"""
    return report
