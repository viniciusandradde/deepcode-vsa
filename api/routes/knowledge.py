"""Knowledge sources API — aggregates available knowledge providers for @mention UI."""

import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()

# Color palette for knowledge providers
PROVIDER_COLORS = {
    "wareline": "#10b981",  # emerald-500
    "glpi": "#3b82f6",      # blue-500
    "zabbix": "#ef4444",    # red-500
}


@router.get("/sources")
async def list_knowledge_sources():
    """Return all available knowledge sources across providers.

    Each source has: id, provider, slug, name, description, color, meta.
    Frontend uses this for the @mention dropdown.
    """
    sources = []

    # --- Wareline domains ---
    try:
        from core.tools.wareline import get_wareline_domains

        domains = get_wareline_domains()
        for d in domains:
            domain_name = d["domain"]
            slug = domain_name.lower().replace(" ", "-")
            sources.append({
                "id": f"wareline:{slug}",
                "provider": "wareline",
                "slug": slug,
                "name": domain_name,
                "description": f"Catálogo hospitalar — {d['table_count']} tabelas",
                "color": PROVIDER_COLORS.get("wareline", "#6b7280"),
                "meta": {
                    "table_count": d["table_count"],
                },
            })
        logger.info("[KNOWLEDGE] Loaded %d Wareline domains", len(domains))
    except Exception as e:
        logger.warning("[KNOWLEDGE] Failed to load Wareline domains: %s", e)

    return {"sources": sources}


@router.get("/sources/wareline/domains")
async def list_wareline_domains():
    """Return Wareline-specific domain list with table counts."""
    try:
        from core.tools.wareline import get_wareline_domains

        domains = get_wareline_domains()
        return {"domains": domains}
    except Exception as e:
        logger.warning("[KNOWLEDGE] Failed to load Wareline domains: %s", e)
        return {"domains": [], "error": str(e)}
