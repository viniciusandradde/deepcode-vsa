"""Report endpoints: fetch data via APIs and format with code (no LLM)."""

import logging
from typing import Optional

from fastapi import APIRouter, Query

from core.reports import (
    format_glpi_report,
    format_zabbix_report,
    format_linear_report,
)
from core.reports.dashboard import format_dashboard_report

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/glpi/tickets")
async def get_glpi_tickets_report(
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None, description="Comma-separated status IDs (e.g. 1,2)"),
) -> dict:
    """GLPI tickets report as markdown. No LLM."""
    try:
        from core.tools.glpi import get_client

        client = get_client()
        status_list = None
        if status:
            try:
                status_list = [int(s.strip()) for s in status.split(",")]
            except ValueError:
                pass
        result = await client.get_tickets(status=status_list, limit=limit)
        if not result.success:
            data = {"error": result.error}
        else:
            data = result.output
        markdown = format_glpi_report(data)
        return {"markdown": markdown, "data": data}
    except Exception as e:
        logger.exception("GLPI report failed: %s", e)
        return {"markdown": f"**Erro:** {e}", "data": {"error": str(e)}}


@router.get("/zabbix/alerts")
async def get_zabbix_alerts_report(
    limit: int = Query(10, ge=1, le=100),
    min_severity: int = Query(3, ge=0, le=5),
) -> dict:
    """Zabbix alerts report as markdown. No LLM."""
    try:
        from core.tools.zabbix import get_client

        client = get_client()
        result = await client.get_problems(limit=limit, severity=min_severity)
        if not result.success:
            data = {"error": result.error}
        else:
            data = {"problems": result.output, "count": len(result.output), "min_severity": min_severity}
        markdown = format_zabbix_report(data)
        return {"markdown": markdown, "data": data}
    except Exception as e:
        logger.exception("Zabbix report failed: %s", e)
        return {"markdown": f"**Erro:** {e}", "data": {"error": str(e)}}


@router.get("/linear/issues")
async def get_linear_issues_report(
    limit: int = Query(10, ge=1, le=100),
    team_id: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
) -> dict:
    """Linear issues report as markdown. No LLM."""
    try:
        from core.tools.linear import get_client

        client = get_client()
        result = await client.get_issues(team_id=team_id, state=state, limit=limit)
        if not result.success:
            data = {"error": result.error}
        else:
            data = result.output
        markdown = format_linear_report(data)
        return {"markdown": markdown, "data": data}
    except Exception as e:
        logger.exception("Linear report failed: %s", e)
        return {"markdown": f"**Erro:** {e}", "data": {"error": str(e)}}


@router.get("/dashboard")
async def get_dashboard_report(
    glpi_limit: int = Query(10, ge=1, le=50),
    zabbix_limit: int = Query(10, ge=1, le=50),
) -> dict:
    """Dashboard: GLPI + Zabbix combined report. No LLM."""
    glpi_data = None
    zabbix_data = None
    linear_data = None
    errors = []

    try:
        from core.tools.glpi import get_client as get_glpi_client

        client = get_glpi_client()
        result = await client.get_tickets(limit=glpi_limit)
        if result.success:
            glpi_data = result.output
        else:
            glpi_data = {"error": result.error}
    except Exception as e:
        errors.append(f"GLPI: {e}")
        glpi_data = {"error": str(e)}

    try:
        from core.tools.zabbix import get_client as get_zabbix_client

        client = get_zabbix_client()
        result = await client.get_problems(limit=zabbix_limit, severity=3)
        if result.success:
            zabbix_data = {"problems": result.output, "count": len(result.output), "min_severity": 3}
        else:
            zabbix_data = {"error": result.error}
    except Exception as e:
        errors.append(f"Zabbix: {e}")
        zabbix_data = {"error": str(e)}

    markdown = format_dashboard_report(glpi_data=glpi_data, zabbix_data=zabbix_data, linear_data=linear_data)
    return {
        "markdown": markdown,
        "data": {"glpi": glpi_data, "zabbix": zabbix_data},
        "errors": errors if errors else None,
    }
