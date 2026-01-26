---
name: zabbix-integration
description: Zabbix monitoring JSON-RPC API integration patterns. Use this skill when implementing alert queries, host management, trigger analysis, or problem correlation with Zabbix. Read-only focus for v1.
---

# Zabbix Integration

## API Overview

```
Endpoint: https://your-zabbix.com/api_jsonrpc.php
Protocol: JSON-RPC 2.0 over HTTP
Auth: API Token in request body
```

## Client Implementation

```python
class ZabbixClient:
    def __init__(self, config: ZabbixConfig):
        self.config = config
        self.request_id = 0
    
    async def call(self, method: str, params: dict = None) -> dict:
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
            result = response.json()
            
            if "error" in result:
                raise ZabbixAPIError(result["error"])
            
            return result["result"]
```

## Common Operations

### Get Active Problems

```python
async def get_problems(self, severity_min: int = 0, limit: int = 100) -> list[dict]:
    return await self.call("problem.get", {
        "output": "extend",
        "selectHosts": ["hostid", "host", "name"],
        "selectTriggers": ["triggerid", "description", "priority"],
        "sortfield": ["eventid"],
        "sortorder": "DESC",
        "limit": limit,
        "recent": True,
        "suppressed": False,
        "severities": list(range(severity_min, 6)) if severity_min > 0 else None
    })
```

### Get Hosts

```python
async def get_hosts(self, hostgroup_ids: list[str] = None) -> list[dict]:
    params = {
        "output": ["hostid", "host", "name", "status"],
        "selectInterfaces": ["ip", "dns", "type"]
    }
    if hostgroup_ids:
        params["groupids"] = hostgroup_ids
    
    return await self.call("host.get", params)
```

### Get Triggers

```python
async def get_triggers(self, min_severity: int = 0) -> list[dict]:
    return await self.call("trigger.get", {
        "output": "extend",
        "selectHosts": ["hostid", "host"],
        "min_severity": min_severity,
        "only_true": True,  # Only in PROBLEM state
        "monitored": True
    })
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

## Important Notes

- **Read-only in v1**: No write operations implemented
- **Always use async httpx**: Never block the event loop
- **Handle errors gracefully**: ZabbixAPIError for API failures
