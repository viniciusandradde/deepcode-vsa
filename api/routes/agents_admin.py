"""Admin CRUD routes for multi-agent management."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg.rows import dict_row

from api.models.agents_admin import (
    AgentConnectorOut,
    AgentCreate,
    AgentDomainOut,
    AgentListItem,
    AgentOut,
    AgentSkillOut,
    AgentUpdate,
    ConnectorOut,
    DomainCreate,
    DomainUpdate,
    KnowledgeDomainOut,
    SkillOut,
)
from api.models.auth import User
from api.routes.auth import get_current_user, require_role
from core.database import get_conn

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_org_id(user: User) -> str:
    """Get user's org_id as string, falling back to default."""
    return str(user.org_id) if user.org_id else "00000000-0000-0000-0000-000000000001"


# ============================================================
# Connectors (read-only, system-level)
# ============================================================

@router.get("/connectors", response_model=list[ConnectorOut])
async def list_connectors(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List all available connectors."""
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM connectors WHERE is_active = true ORDER BY category, name"
            )
            return [ConnectorOut(**row) for row in cur.fetchall()]


# ============================================================
# Skills (read-only, system-level)
# ============================================================

@router.get("/skills", response_model=list[SkillOut])
async def list_skills(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List all available skills."""
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM skills WHERE is_active = true ORDER BY category, name"
            )
            return [SkillOut(**row) for row in cur.fetchall()]


# ============================================================
# Knowledge Domains
# ============================================================

@router.get("/domains", response_model=list[KnowledgeDomainOut])
async def list_domains(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List knowledge domains for the user's organization."""
    org_id = _get_org_id(current_user)
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM knowledge_domains WHERE org_id = %s AND is_active = true ORDER BY name",
                (org_id,),
            )
            return [KnowledgeDomainOut(**row) for row in cur.fetchall()]


@router.post("/domains", response_model=KnowledgeDomainOut, status_code=status.HTTP_201_CREATED)
async def create_domain(
    body: DomainCreate,
    current_user: Annotated[User, Depends(require_role("admin", "manager"))],
):
    """Create a new knowledge domain."""
    org_id = _get_org_id(current_user)
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """INSERT INTO knowledge_domains (org_id, name, slug, description, color)
                   VALUES (%s, %s, %s, %s, %s) RETURNING *""",
                (org_id, body.name, body.slug, body.description, body.color),
            )
            row = cur.fetchone()
            conn.commit()
            return KnowledgeDomainOut(**row)


@router.put("/domains/{domain_id}", response_model=KnowledgeDomainOut)
async def update_domain(
    domain_id: UUID,
    body: DomainUpdate,
    current_user: Annotated[User, Depends(require_role("admin", "manager"))],
):
    """Update a knowledge domain."""
    org_id = _get_org_id(current_user)
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clauses = ", ".join(f"{k} = %s" for k in updates)
    values = list(updates.values()) + [str(domain_id), org_id]

    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""UPDATE knowledge_domains SET {set_clauses}, updated_at = now()
                    WHERE id = %s AND org_id = %s RETURNING *""",
                values,
            )
            row = cur.fetchone()
            conn.commit()
            if not row:
                raise HTTPException(status_code=404, detail="Domain not found")
            return KnowledgeDomainOut(**row)


@router.delete("/domains/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_domain(
    domain_id: UUID,
    current_user: Annotated[User, Depends(require_role("admin", "manager"))],
):
    """Soft-delete a knowledge domain."""
    org_id = _get_org_id(current_user)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE knowledge_domains SET is_active = false WHERE id = %s AND org_id = %s",
                (str(domain_id), org_id),
            )
            conn.commit()
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Domain not found")


# ============================================================
# Agents
# ============================================================

def _fetch_agent_relations(cur, agent_id: str) -> tuple[list, list, list]:
    """Fetch connectors, skills, domains for an agent."""
    cur.execute(
        """SELECT c.slug, c.name, c.icon, ac.enabled, ac.config
           FROM agent_connectors ac
           JOIN connectors c ON c.id = ac.connector_id
           WHERE ac.agent_id = %s ORDER BY c.name""",
        (agent_id,),
    )
    connectors = [AgentConnectorOut(**r) for r in cur.fetchall()]

    cur.execute(
        """SELECT s.slug, s.name, s.icon, asks.enabled
           FROM agent_skills asks
           JOIN skills s ON s.id = asks.skill_id
           WHERE asks.agent_id = %s ORDER BY s.name""",
        (agent_id,),
    )
    skills = [AgentSkillOut(**r) for r in cur.fetchall()]

    cur.execute(
        """SELECT d.id, d.name, d.slug, d.color, ad.access_level
           FROM agent_domains ad
           JOIN knowledge_domains d ON d.id = ad.domain_id
           WHERE ad.agent_id = %s ORDER BY d.name""",
        (agent_id,),
    )
    domains = [AgentDomainOut(**r) for r in cur.fetchall()]

    return connectors, skills, domains


@router.get("/agents", response_model=list[AgentListItem])
async def list_agents(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List agents for the user's organization."""
    org_id = _get_org_id(current_user)
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """SELECT a.*,
                          (SELECT count(*) FROM agent_connectors WHERE agent_id = a.id) as connector_count,
                          (SELECT count(*) FROM agent_skills WHERE agent_id = a.id) as skill_count,
                          (SELECT count(*) FROM agent_domains WHERE agent_id = a.id) as domain_count
                   FROM agents a
                   WHERE a.org_id = %s AND a.is_active = true
                   ORDER BY a.is_default DESC, a.name""",
                (org_id,),
            )
            return [AgentListItem(**row) for row in cur.fetchall()]


@router.post("/agents", response_model=AgentOut, status_code=status.HTTP_201_CREATED)
async def create_agent(
    body: AgentCreate,
    current_user: Annotated[User, Depends(require_role("admin", "manager"))],
):
    """Create a new agent with connectors, skills, and domains."""
    org_id = _get_org_id(current_user)
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            # Create agent
            cur.execute(
                """INSERT INTO agents (org_id, slug, name, description, avatar, system_prompt, agent_type, model_override)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING *""",
                (org_id, body.slug, body.name, body.description, body.avatar,
                 body.system_prompt, body.agent_type, body.model_override),
            )
            agent_row = cur.fetchone()
            agent_id = str(agent_row["id"])

            # Link connectors
            if body.connector_slugs:
                for slug in body.connector_slugs:
                    cur.execute(
                        """INSERT INTO agent_connectors (agent_id, connector_id)
                           SELECT %s, id FROM connectors WHERE slug = %s
                           ON CONFLICT DO NOTHING""",
                        (agent_id, slug),
                    )

            # Link skills
            if body.skill_slugs:
                for slug in body.skill_slugs:
                    cur.execute(
                        """INSERT INTO agent_skills (agent_id, skill_id)
                           SELECT %s, id FROM skills WHERE slug = %s
                           ON CONFLICT DO NOTHING""",
                        (agent_id, slug),
                    )

            # Link domains
            if body.domain_ids:
                for did in body.domain_ids:
                    cur.execute(
                        """INSERT INTO agent_domains (agent_id, domain_id)
                           VALUES (%s, %s) ON CONFLICT DO NOTHING""",
                        (agent_id, str(did)),
                    )

            conn.commit()

            connectors, skills, domains = _fetch_agent_relations(cur, agent_id)
            return AgentOut(**agent_row, connectors=connectors, skills=skills, domains=domains)


@router.get("/agents/{agent_id}", response_model=AgentOut)
async def get_agent(
    agent_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get agent detail with connectors, skills, and domains."""
    org_id = _get_org_id(current_user)
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM agents WHERE id = %s AND org_id = %s AND is_active = true",
                (str(agent_id), org_id),
            )
            agent_row = cur.fetchone()
            if not agent_row:
                raise HTTPException(status_code=404, detail="Agent not found")

            connectors, skills, domains = _fetch_agent_relations(cur, str(agent_id))
            return AgentOut(**agent_row, connectors=connectors, skills=skills, domains=domains)


@router.put("/agents/{agent_id}", response_model=AgentOut)
async def update_agent(
    agent_id: UUID,
    body: AgentUpdate,
    current_user: Annotated[User, Depends(require_role("admin", "manager"))],
):
    """Update an agent and optionally its connectors/skills/domains."""
    org_id = _get_org_id(current_user)
    aid = str(agent_id)

    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            # Update scalar fields
            scalar_fields = body.model_dump(
                exclude_unset=True,
                exclude={"connector_slugs", "skill_slugs", "domain_ids"},
            )
            if scalar_fields:
                set_clauses = ", ".join(f"{k} = %s" for k in scalar_fields)
                values = list(scalar_fields.values()) + [aid, org_id]
                cur.execute(
                    f"""UPDATE agents SET {set_clauses}, updated_at = now()
                        WHERE id = %s AND org_id = %s RETURNING *""",
                    values,
                )
                agent_row = cur.fetchone()
                if not agent_row:
                    raise HTTPException(status_code=404, detail="Agent not found")

                # If setting is_default=True, unset others
                if scalar_fields.get("is_default"):
                    cur.execute(
                        "UPDATE agents SET is_default = false WHERE org_id = %s AND id != %s",
                        (org_id, aid),
                    )
            else:
                cur.execute(
                    "SELECT * FROM agents WHERE id = %s AND org_id = %s AND is_active = true",
                    (aid, org_id),
                )
                agent_row = cur.fetchone()
                if not agent_row:
                    raise HTTPException(status_code=404, detail="Agent not found")

            # Replace connectors if provided
            if body.connector_slugs is not None:
                cur.execute("DELETE FROM agent_connectors WHERE agent_id = %s", (aid,))
                for slug in body.connector_slugs:
                    cur.execute(
                        """INSERT INTO agent_connectors (agent_id, connector_id)
                           SELECT %s, id FROM connectors WHERE slug = %s
                           ON CONFLICT DO NOTHING""",
                        (aid, slug),
                    )

            # Replace skills if provided
            if body.skill_slugs is not None:
                cur.execute("DELETE FROM agent_skills WHERE agent_id = %s", (aid,))
                for slug in body.skill_slugs:
                    cur.execute(
                        """INSERT INTO agent_skills (agent_id, skill_id)
                           SELECT %s, id FROM skills WHERE slug = %s
                           ON CONFLICT DO NOTHING""",
                        (aid, slug),
                    )

            # Replace domains if provided
            if body.domain_ids is not None:
                cur.execute("DELETE FROM agent_domains WHERE agent_id = %s", (aid,))
                for did in body.domain_ids:
                    cur.execute(
                        """INSERT INTO agent_domains (agent_id, domain_id)
                           VALUES (%s, %s) ON CONFLICT DO NOTHING""",
                        (aid, str(did)),
                    )

            conn.commit()

            connectors, skills, domains = _fetch_agent_relations(cur, aid)
            return AgentOut(**agent_row, connectors=connectors, skills=skills, domains=domains)


@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: UUID,
    current_user: Annotated[User, Depends(require_role("admin", "manager"))],
):
    """Soft-delete an agent (set is_active=false)."""
    org_id = _get_org_id(current_user)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE agents SET is_active = false WHERE id = %s AND org_id = %s",
                (str(agent_id), org_id),
            )
            conn.commit()
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Agent not found")
