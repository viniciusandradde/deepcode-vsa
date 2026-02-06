"""Zabbix JSON-RPC API Client."""

import httpx
from typing import Any, Optional

from ..config import ZabbixSettings
from .tool_result import ToolResult


class ZabbixClient:
    """Zabbix JSON-RPC API client.
    
    Implements authentication and data retrieval via JSON-RPC.
    """

    def __init__(self, settings: ZabbixSettings):
        self.settings = settings
        # Handle both URL formats: with or without /api_jsonrpc.php
        base = settings.base_url.rstrip('/')
        if base.endswith('/api_jsonrpc.php'):
            self.api_url = base
        else:
            self.api_url = f"{base}/api_jsonrpc.php"
        self.auth_token: str | None = settings.api_token
        self._client: httpx.AsyncClient | None = None
        self._request_id = 1

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def _rpc_call(self, method: str, params: dict) -> ToolResult:
        """Execute a JSON-RPC call."""
        client = await self._get_client()
        
        # Auto-login if no token (and not login method)
        if not self.auth_token and method != "user.login":
            return ToolResult.fail(
                "No API token provided and login not implemented yet for basic auth",
                operation=method
            )

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self._request_id,
            "auth": self.auth_token if method != "user.login" else None
        }
        self._request_id += 1

        try:
            response = await client.post(self.api_url, json=payload)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                return ToolResult.fail(
                    f"Zabbix RPC Error: {data['error'].get('data') or data['error'].get('message')}",
                    operation=method
                )

            return ToolResult.ok(data["result"], operation=method)
            
        except httpx.HTTPStatusError as e:
            return ToolResult.fail(f"HTTP Error: {e.response.status_code}", operation=method)
        except Exception as e:
            return ToolResult.fail(str(e), operation=method)

    async def get_problems(self, limit: int = 50, severity: int = 3, with_hosts: bool = True) -> ToolResult:
        """Get active problems.

        Args:
            limit: Max records
            severity: Min severity (0-5) - Note: applied as filter after retrieval
            with_hosts: If True, enriches each problem with host name via trigger.get
        """
        params = {
            "output": ["eventid", "name", "severity", "clock", "opdata", "acknowledged", "objectid"],
            "selectTags": ["tag", "value"],
            "sortfield": ["eventid"],
            "sortorder": "DESC",
            "recent": True,
            "limit": limit
        }
        result = await self._rpc_call("problem.get", params)

        # Filter by severity after retrieval if needed
        if result.success and severity > 0:
            problems = result.output if isinstance(result.output, list) else []
            filtered = [p for p in problems if int(p.get('severity', 0)) >= severity]
            result.output = filtered

        # Enrich with host names via trigger.get (problem.get does not return hosts)
        if result.success and with_hosts and result.output:
            problems = result.output if isinstance(result.output, list) else []
            trigger_ids = list({str(p.get("objectid")) for p in problems if p.get("objectid")})
            if trigger_ids:
                trig_result = await self._rpc_call("trigger.get", {
                    "triggerids": trigger_ids,
                    "output": ["triggerid"],
                    "selectHosts": ["name"],
                })
                if trig_result.success and isinstance(trig_result.output, list):
                    # Map triggerid -> host name (first host)
                    trigger_to_host: dict[str, str] = {}
                    for t in trig_result.output:
                        tid = t.get("triggerid")
                        hosts = t.get("hosts") or []
                        name = (hosts[0].get("name") or "") if hosts else ""
                        if tid:
                            trigger_to_host[str(tid)] = name
                    for p in problems:
                        p["host_name"] = trigger_to_host.get(str(p.get("objectid")), "")

        return result

    async def get_host(self, name: str) -> ToolResult:
        """Find host by name."""
        params = {
            "filter": {"host": [name]},
            "output": ["hostid", "host", "name", "status", "interfaces"]
        }
        return await self._rpc_call("host.get", params)
    
    async def get_items(self, host_id: str, tags: list[str] = None) -> ToolResult:
         """Get items for a host."""
         params = {
             "hostids": host_id,
             "output": ["itemid", "name", "key_", "lastvalue", "units"],
             "sortfield": "name"
         }
         return await self._rpc_call("item.get", params)

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
