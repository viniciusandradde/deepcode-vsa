"""Linear report formatters: issues and project plan preview to markdown."""

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


def format_project_plan_preview(plan: dict, team_name: str = "") -> str:
    """Formata preview do plano de projeto para confirmação do usuário.

    Retorna markdown com dados do projeto, milestones em tabela, tarefas
    agrupadas por milestone e instrução para confirmar criação no Linear.
    Inclui marcador especial para o frontend exibir botão de confirmação.
    """
    proj = plan.get("project") or {}
    milestones = plan.get("milestones") or []
    tasks = plan.get("tasks") or []

    priority_labels = {0: "Nenhuma", 1: "Urgente", 2: "Alta", 3: "Normal", 4: "Baixa"}
    proj_priority = proj.get("priority", 0)
    proj_priority_str = priority_labels.get(proj_priority, str(proj_priority))

    lines = [
        "## Preview do Projeto (Linear)",
        "",
        "Revise o escopo abaixo. Para criar no Linear, **confirme** usando o botão ou digite **confirmar**.",
        "",
        "### Projeto",
        f"- **Nome:** {proj.get('name', '(sem nome)')}",
        f"- **Resumo:** {proj.get('summary') or '(não informado)'}",
        f"- **Prioridade:** {proj_priority_str}",
        f"- **Início:** {proj.get('startDate') or '(não definido)'}",
        f"- **Conclusão:** {proj.get('targetDate') or '(não definido)'}",
        "",
    ]
    if team_name:
        lines.append(f"- **Time:** {team_name}")
        lines.append("")

    if milestones:
        lines.append("### Milestones (fases)")
        lines.append("| Fase | Data alvo |")
        lines.append("|------|-----------|")
        for m in milestones:
            name = m.get("name", "?")
            target = m.get("targetDate") or "-"
            lines.append(f"| {name} | {target} |")
        lines.append("")

    if tasks:
        lines.append("### Tarefas por milestone")
        by_milestone: dict[str, list[dict]] = {}
        for t in tasks:
            m = t.get("milestone") or "(sem fase)"
            by_milestone.setdefault(m, []).append(t)
        for m_name in [m.get("name") for m in milestones] or list(by_milestone.keys()):
            if m_name not in by_milestone:
                continue
            lines.append(f"**{m_name}**")
            for t in by_milestone[m_name]:
                title = t.get("title", "?")
                pri = t.get("priority", 3)
                lines.append(f"- {title} (prioridade {pri})")
            lines.append("")

    lines.append("---")
    lines.append("*Para criar este projeto no Linear, confirme a ação.*")
    lines.append("")
    lines.append("<!-- VSA_PROJECT_PREVIEW_CONFIRM -->")

    return "\n".join(lines)


def format_project_plan_preview_from_tool_output(tool_output: dict, team_name: str = "") -> str:
    """Formata preview a partir do retorno da tool linear_create_full_project (dry_run=True)."""
    preview = tool_output.get("preview") or {}
    plan = {
        "project": preview.get("project") or {},
        "milestones": preview.get("milestones") or [],
        "tasks": preview.get("tasks") or [],
    }
    return format_project_plan_preview(plan, team_name=team_name)
