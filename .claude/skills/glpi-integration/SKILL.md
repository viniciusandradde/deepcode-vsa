---
name: glpi-integration
description: GLPI ITSM REST API integration patterns. Use this skill when implementing ticket management, SLA monitoring, asset queries, or user/group operations in GLPI. Covers authentication, common operations, and governance.
---

# GLPI Integration

## API Overview

```
Base URL: https://your-glpi.com/apirest.php
Auth: App-Token + User-Token headers
```

## Authentication

```python
class GLPIClient:
    def __init__(self, config: GLPIConfig):
        self.config = config
        self.session_token: str | None = None
    
    async def init_session(self) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.config.base_url}/initSession",
                headers={
                    "App-Token": self.config.app_token,
                    "Authorization": f"user_token {self.config.user_token}"
                }
            )
            self.session_token = response.json()["session_token"]
            return self.session_token
    
    async def kill_session(self) -> None:
        if self.session_token:
            async with httpx.AsyncClient() as client:
                await client.get(
                    f"{self.config.base_url}/killSession",
                    headers=self._headers()
                )
            self.session_token = None
```

## Common Operations

### List Tickets

```python
async def get_tickets(self, status: list[int] = None, limit: int = 50) -> list[dict]:
    params = {"range": f"0-{limit-1}"}
    if status:
        params["criteria"] = [{"field": 12, "searchtype": "contains", "value": status}]
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{self.config.base_url}/Ticket",
            headers=self._headers(),
            params=params
        )
        return response.json()
```

### Create Ticket (with governance)

```python
@governed_operation(OperationType.WRITE)
async def create_ticket(self, title: str, content: str, dry_run: bool = True) -> ToolResult:
    data = {"input": {"name": title, "content": content}}
    
    if dry_run:
        return ToolResult(success=True, data={"preview": data})
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{self.config.base_url}/Ticket",
            headers=self._headers(),
            json=data
        )
        return ToolResult(success=True, data=response.json())
```

## Status Codes

| Code | Status |
|------|--------|
| 1 | New |
| 2 | Assigned |
| 3 | Planned |
| 4 | Pending |
| 5 | Solved |
| 6 | Closed |

## Priority Codes

| Code | Priority |
|------|----------|
| 1 | Very low |
| 2 | Low |
| 3 | Medium |
| 4 | High |
| 5 | Very high |
| 6 | Major |

## Field IDs (Search API)

| ID | Field |
|----|-------|
| 1 | name (title) |
| 2 | id |
| 3 | priority |
| 12 | status |
| 15 | date (open) |
| 18 | time_to_resolve (SLA) |
