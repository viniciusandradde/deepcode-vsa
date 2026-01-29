"""Linear report formatters: issues to markdown."""

from typing import Any


def _safe_get(obj: dict, key: str, default: Any = "") -> Any:
    """Get value from dict, including nested (e.g. state.name)."""
    val = obj.get(key, default)
    if val is None:
        return default
    return val


def _nested(obj: dict, path: str, default: Any = "") -> Any:
    """Get nested key like 'state.name'."""
    parts = path.split(".")
    cur = obj
    for p in parts:
        cur = cur.get(p) if isinstance(cur, dict) else None
        if cur is None:
            return default
    return cur


def format_issues_table(issues: list[dict], limit: int = 10) -> str:
    """Formata lista de issues Linear como tabela markdown."""
    if not issues:
        return "Nenhuma issue encontrada."

    lines = [
        "| ID | Título | Estado | Prioridade |",
        "|----|--------|--------|------------|",
    ]
    for i in issues[:limit]:
        ident = _safe_get(i, "identifier", _safe_get(i, "id", "?"))[:12]
        title = str(_safe_get(i, "title", "(sem título)"))[:45]
        state = _nested(i, "state.name") or _safe_get(i, "state", "?")
        if isinstance(state, dict):
            state = state.get("name", "?")
        priority = _safe_get(i, "priorityLabel") or _safe_get(i, "priority", "?")
        lines.append(f"| {ident} | {title} | {state} | {priority} |")

    return "\n".join(lines)


def format_linear_report(data: dict) -> str:
    """Relatório completo Linear a partir do dict retornado por linear_get_issues."""
    if data.get("error"):
        return f"**Erro ao consultar Linear:** {data['error']}"

    issues = data.get("issues") or []
    count = data.get("count", len(issues))

    by_state: dict[str, int] = {}
    for i in issues:
        s = _nested(i, "state.name") or _safe_get(i, "state", "?")
        if isinstance(s, dict):
            s = s.get("name", "?")
        by_state[str(s)] = by_state.get(str(s), 0) + 1

    backlog = by_state.get("Backlog", 0)
    in_progress = by_state.get("In Progress", 0) + by_state.get("Started", 0)
    done = by_state.get("Done", 0) + by_state.get("Canceled", 0)
    report = f"""### Linear - Issues

**Resumo:**

| Total | Backlog | Em andamento | Concluído |
|-------|---------|--------------|-----------|
| {count} | {backlog} | {in_progress} | {done} |

**Últimas issues:**

{format_issues_table(issues)}
"""
    return report
