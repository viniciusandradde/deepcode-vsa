---
name: zabbix-integration
description: Zabbix JSON-RPC API integration patterns. Alerts, hosts, triggers, problem correlation. Read-only focus for v1.
license: MIT
compatibility: opencode
metadata:
  api: zabbix-jsonrpc
  version: "6.x/7.x"
---

# Zabbix Integration Skill

Patterns for integrating with Zabbix JSON-RPC API.

## API Overview

Zabbix uses JSON-RPC 2.0 over HTTP:

```
Endpoint: https://your-zabbix.com/api_jsonrpc.php
Content-Type: application/json-rpc
Auth: API Token in request body
```

## Authentication

```python
import httpx
from pydantic import BaseModel

class ZabbixConfig(BaseModel):
    base_url: str
    api_token: str

class ZabbixClient:
    def __init__(self, config: ZabbixConfig):
        self.config = config
        self.request_id = 0
    
    async def call(self, method: str, params: dict = None) -> dict:
        """Make JSON-RPC call to Zabbix API."""
        self.request_id += 1
        
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self.request_id,
            "auth": self.config.api_token
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.config.base_url,
                json=payload,
                headers={"Content-Type": "application/json-rpc"}
            )
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                raise ZabbixAPIError(result["error"])
            
            return result["result"]

class ZabbixAPIError(Exception):
    def __init__(self, error: dict):
        self.code = error.get("code")
        self.message = error.get("message")
        self.data = error.get("data")
        super().__init__(f"Zabbix API Error {self.code}: {self.message}")
```

## Common Operations

### Get Active Problems

```python
async def get_problems(
    self,
    severity_min: int = 0,
    limit: int = 100,
    hostgroup_ids: list[str] | None = None
) -> list[dict]:
    """Get active problems/alerts."""
    params = {
        "output": "extend",
        "selectHosts": ["hostid", "host", "name"],
        "selectTriggers": ["triggerid", "description", "priority"],
        "sortfield": ["eventid"],
        "sortorder": "DESC",
        "limit": limit,
        "recent": True,
        "suppressed": False
    }
    
    if severity_min > 0:
        params["severities"] = list(range(severity_min, 6))
    
    if hostgroup_ids:
        params["groupids"] = hostgroup_ids
    
    return await self.call("problem.get", params)
```

### Get Hosts

```python
async def get_hosts(
    self,
    hostgroup_ids: list[str] | None = None,
    status: int | None = None,
    with_problems: bool = False
) -> list[dict]:
    """Get hosts with optional filters."""
    params = {
        "output": ["hostid", "host", "name", "status"],
        "selectInterfaces": ["ip", "dns", "type"]
    }
    
    if hostgroup_ids:
        params["groupids"] = hostgroup_ids
    
    if status is not None:
        params["filter"] = {"status": status}
    
    if with_problems:
        params["selectProblems"] = "extend"
        params["selectTriggers"] = ["triggerid", "description"]
    
    return await self.call("host.get", params)
```

### Get Triggers

```python
async def get_triggers(
    self,
    host_ids: list[str] | None = None,
    min_severity: int = 0,
    only_problems: bool = True
) -> list[dict]:
    """Get triggers (alarm definitions)."""
    params = {
        "output": "extend",
        "selectHosts": ["hostid", "host"],
        "selectLastEvent": ["eventid", "value"],
        "min_severity": min_severity,
        "sortfield": "priority",
        "sortorder": "DESC",
        "monitored": True
    }
    
    if host_ids:
        params["hostids"] = host_ids
    
    if only_problems:
        params["only_true"] = True  # Only in PROBLEM state
    
    return await self.call("trigger.get", params)
```

### Get History/Metrics

```python
async def get_history(
    self,
    item_ids: list[str],
    history_type: int = 0,
    time_from: int | None = None,
    time_till: int | None = None,
    limit: int = 100
) -> list[dict]:
    """Get item history (metrics data)."""
    params = {
        "itemids": item_ids,
        "history": history_type,
        "sortfield": "clock",
        "sortorder": "DESC",
        "limit": limit,
        "output": "extend"
    }
    
    if time_from:
        params["time_from"] = time_from
    if time_till:
        params["time_till"] = time_till
    
    return await self.call("history.get", params)
```

### Get Host Groups

```python
async def get_hostgroups(
    self,
    with_hosts: bool = False
) -> list[dict]:
    """Get host groups."""
    params = {
        "output": ["groupid", "name"]
    }
    
    if with_hosts:
        params["selectHosts"] = ["hostid", "host"]
    
    return await self.call("hostgroup.get", params)
```

## Severity Levels

| Code | Severity | Color |
|------|----------|-------|
| 0 | Not classified | Gray |
| 1 | Information | Light blue |
| 2 | Warning | Yellow |
| 3 | Average | Orange |
| 4 | High | Light red |
| 5 | Disaster | Red |

## History Types

| Code | Type |
|------|------|
| 0 | Float |
| 1 | Character |
| 2 | Log |
| 3 | Unsigned integer |
| 4 | Text |

## Full Tool Implementation

```python
from ..base import APITool, ToolResult, Operation

class ZabbixTool(APITool):
    def __init__(self, config: ZabbixConfig):
        self.client = ZabbixClient(config)
    
    @property
    def name(self) -> str:
        return "zabbix"
    
    @property
    def description(self) -> str:
        return "Zabbix Monitoring - Alerts, hosts, triggers, metrics"
    
    @property
    def operations(self) -> list[Operation]:
        return [
            Operation(name="get_problems", description="Get active alerts", method="GET"),
            Operation(name="get_hosts", description="List monitored hosts", method="GET"),
            Operation(name="get_triggers", description="Get trigger definitions", method="GET"),
            Operation(name="get_hostgroups", description="List host groups", method="GET"),
            Operation(name="get_history", description="Get metrics history", method="GET"),
        ]
    
    async def read(self, operation: str, params: dict) -> ToolResult:
        try:
            if operation == "get_problems":
                data = await self.client.get_problems(**params)
            elif operation == "get_hosts":
                data = await self.client.get_hosts(**params)
            elif operation == "get_triggers":
                data = await self.client.get_triggers(**params)
            elif operation == "get_hostgroups":
                data = await self.client.get_hostgroups(**params)
            elif operation == "get_history":
                data = await self.client.get_history(**params)
            else:
                return ToolResult(success=False, error=f"Unknown operation: {operation}")
            return ToolResult(success=True, data=data)
        except ZabbixAPIError as e:
            return ToolResult(success=False, error=str(e))
    
    async def write(self, operation: str, data: dict, dry_run: bool = True) -> ToolResult:
        # Zabbix operations are READ-ONLY in v1
        return ToolResult(
            success=False,
            error="Write operations not supported for Zabbix in v1"
        )
```

## Correlation with GLPI

```python
async def correlate_zabbix_glpi(
    zabbix: ZabbixTool,
    glpi: GLPITool
) -> list[dict]:
    """Correlate Zabbix alerts with GLPI tickets by hostname."""
    # Get active problems from Zabbix
    problems = await zabbix.read("get_problems", {"severity_min": 3})
    
    correlations = []
    for problem in problems.data:
        hostname = problem["hosts"][0]["host"]
        
        # Search for related tickets in GLPI
        tickets = await glpi.read("get_tickets", {
            "search": hostname,
            "status": [1, 2, 3, 4]  # Open tickets
        })
        
        correlations.append({
            "problem": problem,
            "hostname": hostname,
            "related_tickets": tickets.data
        })
    
    return correlations
```

## References

- [Zabbix API Documentation](https://www.zabbix.com/documentation/current/en/manual/api)
- [Zabbix JSON-RPC Reference](https://www.zabbix.com/documentation/current/en/manual/api/reference)
