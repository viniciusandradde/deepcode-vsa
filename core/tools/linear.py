"""Linear.app Integration Tools."""

import json
import re
from typing import Optional, List
from langchain.tools import tool


def _normalize_project_plan_json(raw: str) -> str:
    """Extract and normalize JSON string from project_plan (handles empty and markdown-wrapped)."""
    if raw is None:
        return ""
    s = (raw or "").strip()
    if not s:
        return ""
    # Extract from markdown code block if present (LLM sometimes returns ```json ... ```)
    code_block = re.search(r"```(?:json)?\s*([\s\S]*?)```", s)
    if code_block:
        s = code_block.group(1).strip()
    return s

from ..integrations.linear_client import LinearClient
from ..config import get_settings

_client: Optional[LinearClient] = None

def get_client() -> LinearClient:
    """Get or create Linear client singleton."""
    global _client
    if not _client:
        settings = get_settings()
        # Linear API key from environment
        api_key = settings.linear.api_key if hasattr(settings, 'linear') else None
        if not api_key:
            import os
            api_key = os.getenv("LINEAR_API_KEY", "")

        if not api_key:
            raise ValueError("LINEAR_API_KEY not configured")

        _client = LinearClient(api_key)
    return _client


@tool
async def linear_get_issues(
    team_id: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 10
) -> dict:
    """Get issues from Linear.

    Args:
        team_id: Optional team ID to filter (use linear_get_teams to find IDs)
        state: Optional state name to filter (e.g., "In Progress", "Backlog", "Done")
        limit: Max number of issues to return (default 10)

    Returns:
        Dictionary with 'issues' list and 'count'
    """
    client = get_client()
    result = await client.get_issues(team_id=team_id, state=state, limit=limit)

    if not result.success:
        return {"error": result.error}

    return result.output


@tool
async def linear_get_issue(issue_id: str) -> dict:
    """Get full details of a specific Linear issue.

    Args:
        issue_id: Issue ID (UUID) or identifier (e.g., 'ENG-123')

    Returns:
        Dictionary with 'issue' details including comments, labels, assignee
    """
    client = get_client()
    result = await client.get_issue(issue_id)

    if not result.success:
        return {"error": result.error}

    return result.output


@tool
async def linear_create_issue(
    team_id: str,
    title: str,
    description: str,
    priority: int = 3,
    dry_run: bool = True
) -> dict:
    """Create a new issue in Linear.

    Args:
        team_id: Team ID where issue will be created (use linear_get_teams to find)
        title: Issue title (brief summary)
        description: Detailed description (supports Markdown)
        priority: Priority level (0=No priority, 1=Urgent, 2=High, 3=Normal, 4=Low)
        dry_run: If True (default), simulates creation and returns preview

    Returns:
        If dry_run=True: preview of what would be created
        If dry_run=False: created issue details with ID and URL
    """
    client = get_client()
    result = await client.create_issue(
        team_id=team_id,
        title=title,
        description=description,
        priority=priority,
        dry_run=dry_run
    )

    if not result.success:
        return {"error": result.error}

    return result.output


@tool
async def linear_get_teams() -> dict:
    """Get all teams in the Linear organization.

    Use this to find team IDs before creating issues.

    Returns:
        Dictionary with 'teams' list containing id, name, key for each team
    """
    client = get_client()
    result = await client.get_teams()

    if not result.success:
        return {"error": result.error}

    return result.output


@tool
async def linear_add_comment(
    issue_id: str,
    comment: str,
    dry_run: bool = True
) -> dict:
    """Add a comment to a Linear issue.

    Args:
        issue_id: Issue ID or identifier (e.g., 'ENG-123')
        comment: Comment text (supports Markdown)
        dry_run: If True (default), simulates adding comment

    Returns:
        Success status and comment details
    """
    client = get_client()
    result = await client.add_comment(issue_id, comment, dry_run)

    if not result.success:
        return {"error": result.error}

    return result.output


@tool
async def linear_create_project(
    team_id: str,
    name: str,
    description: str = "",
    summary: str = "",
    start_date: Optional[str] = None,
    target_date: Optional[str] = None,
    priority: int = 0,
    dry_run: bool = True
) -> dict:
    """Create a new project in Linear.

    Args:
        team_id: Team ID where project will be created (use linear_get_teams to find)
        name: Project name
        description: Project description (Markdown)
        summary: Short summary, max 255 chars
        start_date: Start date (YYYY-MM-DD)
        target_date: Target date (YYYY-MM-DD)
        priority: 0=None, 1=Urgent, 2=High, 3=Medium, 4=Low
        dry_run: If True (default), simulates creation and returns preview

    Returns:
        If dry_run=True: preview of what would be created
        If dry_run=False: created project details with ID and URL
    """
    client = get_client()
    result = await client.create_project(
        team_id=team_id,
        name=name,
        description=description,
        summary=summary,
        start_date=start_date,
        target_date=target_date,
        priority=priority,
        dry_run=dry_run
    )
    if not result.success:
        return {"error": result.error}
    return result.output


@tool
async def linear_create_full_project(
    team_id: str,
    project_plan: str,
    dry_run: bool = True
) -> dict:
    """Create a full project in Linear with milestones and tasks.

    Use this when the user wants to create a complete project with phases (milestones)
    and tasks. First call with dry_run=True to get a preview, then the user confirms
    and you call again with dry_run=False.

    Args:
        team_id: Team ID (use linear_get_teams to find)
        project_plan: JSON string with structure: {
            "project": {"name", "summary", "description", "startDate", "targetDate", "priority"},
            "milestones": [{"name", "targetDate", "description"}],
            "tasks": [{"title", "description", "milestone": "milestone name", "priority"}]
        }
        dry_run: If True (default), returns preview without creating. Set False only after user confirms.

    Returns:
        Preview (dry_run=True) or created project URL and issue list (dry_run=False)
    """
    client = get_client()
    # Normalize: handle None, empty string, and markdown-wrapped JSON
    raw = project_plan if isinstance(project_plan, str) else ""
    normalized = _normalize_project_plan_json(raw)
    if not normalized:
        return {
            "error": "project_plan está vazio ou ausente. O plano deve ser um JSON com 'project', 'milestones' e 'tasks'. Gere o plano antes de confirmar a criação."
        }
    try:
        plan = json.loads(normalized)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid project_plan JSON: {e}"}
    if not isinstance(plan, dict):
        return {"error": "project_plan must be a JSON object"}
    result = await client.create_project_with_plan(team_id=team_id, plan=plan, dry_run=dry_run)
    if not result.success:
        return {"error": result.error}
    return result.output
