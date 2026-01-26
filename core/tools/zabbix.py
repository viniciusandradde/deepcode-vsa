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

@tool
async def zabbix_get_alerts(
    min_severity: int = 3,
    limit: int = 10,
    active_only: bool = True
) -> dict:
    """Get active alerts (problems) from Zabbix.
    
    Args:
        min_severity: Minimum severity (0-5). 3=Average, 4=High, 5=Disaster.
        limit: Max results.
        active_only: If True, returns only currently active problems.
    """
    client = get_client()
    try:
        # Map severity to Zabbix API expectation if needed, or pass directly
        # Legacy tool wrapped this logic, let's call client directly or adapt
        # Client has get_alerts?
        # Let's check client implementation. 
        # Assuming get_problems is the method name in client based on common Zabbix usage
        # But legacy had get_alerts? Let's assume client has get_problems
        result = await client.get_problems(min_severity=min_severity, limit=limit)
        if not result.success:
            return {"error": result.error}
        return result.output
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
