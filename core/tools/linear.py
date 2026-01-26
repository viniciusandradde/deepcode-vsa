"""Linear.app Integration Tools."""

from typing import Optional, List
from langchain.tools import tool

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
