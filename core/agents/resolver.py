"""Agent Resolver: builds tools and system prompt from DB-defined agent configuration.

Replaces hardcoded tool construction in chat.py with a database-driven approach.
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable
from uuid import UUID

from psycopg.rows import dict_row

from core.database import get_conn

logger = logging.getLogger(__name__)


@dataclass
class ResolvedAgent:
    """Result of resolving an agent definition into runtime configuration."""

    tools: list[Any] = field(default_factory=list)
    system_prompt: str | None = None
    agent_type: str = "simple"  # simple, unified, vsa
    model_name: str | None = None
    allowed_domain_ids: list[UUID] | None = None  # None = no restriction (admin)
    enable_itil: bool = False
    enable_planning: bool = False
    skill_slugs: list[str] = field(default_factory=list)


def _get_connector_tools() -> dict[str, Callable[[], list]]:
    """Registry mapping connector slugs to tool factory functions.

    Each factory returns a list of LangChain tools. Lazy imports avoid
    loading integrations that aren't configured.
    """

    def _glpi_tools():
        from core.tools.glpi import glpi_get_tickets, glpi_get_ticket_details, glpi_create_ticket
        return [glpi_get_tickets, glpi_get_ticket_details, glpi_create_ticket]

    def _zabbix_tools():
        from core.tools.zabbix import zabbix_get_alerts, zabbix_get_host
        return [zabbix_get_alerts, zabbix_get_host]

    def _linear_tools():
        from core.tools.linear import (
            linear_get_issues, linear_get_issue, linear_create_issue,
            linear_get_teams, linear_create_project, linear_create_full_project,
        )
        return [
            linear_get_issues, linear_get_issue, linear_create_issue,
            linear_get_teams, linear_create_project, linear_create_full_project,
        ]

    def _tavily_tools():
        from core.tools.search import tavily_search
        tools = [tavily_search]
        if os.getenv("TAVILY_API_KEY"):
            from core.tools.images import image_search
            tools.append(image_search)
        return tools

    def _planning_tools():
        from core.tools.planning import PLANNING_TOOLS
        return list(PLANNING_TOOLS)

    def _wareline_tools():
        from core.tools.wareline import wareline_search_tables
        return [wareline_search_tables]

    return {
        "glpi": _glpi_tools,
        "zabbix": _zabbix_tools,
        "linear": _linear_tools,
        "tavily": _tavily_tools,
        "planning": _planning_tools,
        "wareline": _wareline_tools,
    }


CONNECTOR_TOOL_REGISTRY = _get_connector_tools()

# Skills that map to special behavior flags
SKILL_FLAG_MAP = {
    "itil_classification": "enable_itil",
    "gut_scoring": "enable_itil",  # part of ITIL flow
}


def resolve(agent_id: str | UUID) -> ResolvedAgent:
    """Resolve an agent definition from DB into runtime configuration.

    Queries the agent, its connectors, skills, and domains,
    then builds the tools list and system prompt.
    """
    aid = str(agent_id)

    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            # Fetch agent
            cur.execute(
                "SELECT * FROM agents WHERE id = %s AND is_active = true",
                (aid,),
            )
            agent = cur.fetchone()
            if not agent:
                logger.warning("Agent %s not found or inactive", aid)
                return ResolvedAgent()

            # Fetch enabled connectors
            cur.execute(
                """SELECT c.slug FROM agent_connectors ac
                   JOIN connectors c ON c.id = ac.connector_id
                   WHERE ac.agent_id = %s AND ac.enabled = true AND c.is_active = true""",
                (aid,),
            )
            connector_slugs = [r["slug"] for r in cur.fetchall()]

            # Fetch enabled skills
            cur.execute(
                """SELECT s.slug, s.prompt_fragment FROM agent_skills asks
                   JOIN skills s ON s.id = asks.skill_id
                   WHERE asks.agent_id = %s AND asks.enabled = true AND s.is_active = true""",
                (aid,),
            )
            skill_rows = cur.fetchall()
            skill_slugs = [r["slug"] for r in skill_rows]

            # Fetch domain access
            cur.execute(
                """SELECT d.id, ad.access_level FROM agent_domains ad
                   JOIN knowledge_domains d ON d.id = ad.domain_id
                   WHERE ad.agent_id = %s AND d.is_active = true""",
                (aid,),
            )
            domain_rows = cur.fetchall()

    # Build tools list from connectors
    tools = []
    for slug in connector_slugs:
        factory = CONNECTOR_TOOL_REGISTRY.get(slug)
        if factory:
            try:
                tools.extend(factory())
                logger.info("Resolved connector '%s' -> %d tools", slug, len(factory()))
            except Exception as e:
                logger.warning("Failed to load tools for connector '%s': %s", slug, e)

    # Build system prompt from agent base + skill fragments
    prompt_parts = []
    if agent.get("system_prompt"):
        prompt_parts.append(agent["system_prompt"])

    for row in skill_rows:
        if row.get("prompt_fragment"):
            prompt_parts.append(row["prompt_fragment"])

    system_prompt = "\n\n".join(prompt_parts) if prompt_parts else None

    # Determine flags from skills
    enable_itil = any(s in SKILL_FLAG_MAP for s in skill_slugs)
    enable_planning = "planning" in connector_slugs

    # Domain IDs (None means admin access to all)
    has_admin_domain = any(r.get("access_level") == "admin" for r in domain_rows)
    allowed_domain_ids = (
        None if has_admin_domain
        else [UUID(str(r["id"])) for r in domain_rows]
    )

    return ResolvedAgent(
        tools=tools,
        system_prompt=system_prompt,
        agent_type=agent.get("agent_type", "simple"),
        model_name=agent.get("model_override"),
        allowed_domain_ids=allowed_domain_ids,
        enable_itil=enable_itil,
        enable_planning=enable_planning,
        skill_slugs=skill_slugs,
    )


def resolve_default(org_id: str | UUID | None = None) -> ResolvedAgent | None:
    """Resolve the default agent for an organization."""
    oid = str(org_id) if org_id else "00000000-0000-0000-0000-000000000001"

    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT id FROM agents WHERE org_id = %s AND is_default = true AND is_active = true LIMIT 1",
                (oid,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return resolve(row["id"])


def resolve_for_legacy(
    *,
    use_tavily: bool = False,
    enable_glpi: bool = False,
    enable_zabbix: bool = False,
    enable_linear: bool = False,
    enable_planning: bool = False,
    enable_wareline: bool = False,
    enable_vsa: bool = False,
    project_id: str | None = None,
) -> ResolvedAgent:
    """Backward-compatible resolver: maps individual flags to tools.

    Used when no agent_id is provided in the request (legacy frontend).
    """
    tools = []

    if use_tavily:
        factory = CONNECTOR_TOOL_REGISTRY.get("tavily")
        if factory:
            tools.extend(factory())
    elif os.getenv("TAVILY_API_KEY"):
        # image_search is always available if key exists
        from core.tools.images import image_search
        tools.append(image_search)

    if enable_glpi:
        factory = CONNECTOR_TOOL_REGISTRY.get("glpi")
        if factory:
            tools.extend(factory())

    if enable_zabbix:
        factory = CONNECTOR_TOOL_REGISTRY.get("zabbix")
        if factory:
            tools.extend(factory())

    if enable_linear:
        factory = CONNECTOR_TOOL_REGISTRY.get("linear")
        if factory:
            tools.extend(factory())

    if enable_planning:
        factory = CONNECTOR_TOOL_REGISTRY.get("planning")
        if factory:
            tools.extend(factory())

    if enable_wareline:
        factory = CONNECTOR_TOOL_REGISTRY.get("wareline")
        if factory:
            tools.extend(factory())

    if project_id:
        from core.tools.planning_rag import search_project_knowledge
        tools.append(search_project_knowledge)

    return ResolvedAgent(
        tools=tools,
        agent_type="unified" if enable_vsa else "simple",
        enable_itil=enable_vsa,
        enable_planning=enable_planning,
    )
