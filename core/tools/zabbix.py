"""Zabbix Integration Tools."""

from typing import Optional, List
from langchain.tools import tool

from ..integrations.zabbix_client import ZabbixClient
from ..config import get_settings

_client: Optional[ZabbixClient] = None

def get_client() -> ZabbixClient:
    """Get or create Zabbix client singleton."""
    global _client
    if not _client:
        settings = get_settings().zabbix
        _client = ZabbixClient(settings)
    return _client

# Fields the LLM needs from each Zabbix problem (slim output)
_PROBLEM_SUMMARY_KEYS = {"eventid", "name", "severity", "clock", "opdata", "acknowledged", "host_name"}


@tool
async def zabbix_get_alerts(
    min_severity: int = 3,
    limit: int = 10,
    active_only: bool = True
) -> dict:
    """Busca alertas e problemas ativos no Zabbix (monitoramento de infraestrutura).
    Usar para: alertas críticos, problemas de rede/servidores, eventos de monitoramento, status de hosts.
    Retorna: eventid, nome do alerta, severidade, horário, host afetado.

    Args:
        min_severity: Minimum severity (0-5). 3=Average, 4=High, 5=Disaster.
        limit: Max results.
        active_only: If True, returns only currently active problems.
    """
    client = get_client()
    try:
        # Call get_problems with correct parameter name
        result = await client.get_problems(severity=min_severity, limit=limit)
        if not result.success:
            return {"error": result.error}

        problems = result.output if isinstance(result.output, list) else []
        # Slim down to essential fields only (token optimization)
        slim_problems = [
            {k: v for k, v in p.items() if k in _PROBLEM_SUMMARY_KEYS}
            for p in problems
        ]
        return {
            "count": len(slim_problems),
            "problems": slim_problems,
            "min_severity": min_severity
        }
    except Exception as e:
        return {"error": str(e)}

@tool
async def zabbix_get_host(host_name: str) -> dict:
    """Get details of a specific host in Zabbix.
    
    Args:
        host_name: Name of the host to search for.
    """
    client = get_client()
    result = await client.get_host(host_name)
    if not result.success:
        return {"error": result.error}
    return result.output
