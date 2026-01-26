---
name: glpi-integration
description: GLPI REST API integration patterns. Ticket management, SLA monitoring, asset queries. Follows APITool contract.
license: MIT
compatibility: opencode
metadata:
  api: glpi-rest
  version: "10.x"
---

# GLPI Integration Skill

Patterns for integrating with GLPI ITSM REST API.

## API Overview

GLPI uses a REST API with session-based authentication:

```
Base URL: https://your-glpi.com/apirest.php
Auth: App-Token + User-Token headers
```

## Authentication

```python
import httpx
from pydantic import BaseModel

class GLPIConfig(BaseModel):
    base_url: str
    app_token: str
    user_token: str

class GLPIClient:
    def __init__(self, config: GLPIConfig):
        self.config = config
        self.session_token: str | None = None
    
    async def init_session(self) -> str:
        """Initialize GLPI session."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.config.base_url}/initSession",
                headers={
                    "App-Token": self.config.app_token,
                    "Authorization": f"user_token {self.config.user_token}"
                }
            )
            response.raise_for_status()
            self.session_token = response.json()["session_token"]
            return self.session_token
    
    async def kill_session(self) -> None:
        """Close GLPI session."""
        if self.session_token:
            async with httpx.AsyncClient() as client:
                await client.get(
                    f"{self.config.base_url}/killSession",
                    headers=self._headers()
                )
            self.session_token = None
    
    def _headers(self) -> dict:
        return {
            "App-Token": self.config.app_token,
            "Session-Token": self.session_token,
            "Content-Type": "application/json"
        }
```

## Common Operations

### List Tickets

```python
async def get_tickets(
    self,
    status: list[int] | None = None,
    priority: list[int] | None = None,
    limit: int = 50
) -> list[dict]:
    """Get tickets with filters."""
    params = {"range": f"0-{limit-1}"}
    
    criteria = []
    if status:
        criteria.append({
            "field": 12,  # status field
            "searchtype": "contains",
            "value": status
        })
    if priority:
        criteria.append({
            "field": 3,  # priority field
            "searchtype": "contains",
            "value": priority
        })
    
    if criteria:
        params["criteria"] = criteria
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{self.config.base_url}/Ticket",
            headers=self._headers(),
            params=params
        )
        response.raise_for_status()
        return response.json()
```

### Get Single Ticket

```python
async def get_ticket(self, ticket_id: int) -> dict:
    """Get ticket by ID with related items."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{self.config.base_url}/Ticket/{ticket_id}",
            headers=self._headers(),
            params={"expand_dropdowns": True}
        )
        response.raise_for_status()
        return response.json()
```

### Create Ticket (with governance)

```python
from ..governance import governed_operation, OperationType

@governed_operation(OperationType.WRITE)
async def create_ticket(
    self,
    title: str,
    content: str,
    priority: int = 3,
    category: int | None = None,
    dry_run: bool = True
) -> ToolResult:
    """Create a new ticket."""
    data = {
        "input": {
            "name": title,
            "content": content,
            "priority": priority
        }
    }
    if category:
        data["input"]["itilcategories_id"] = category
    
    if dry_run:
        return ToolResult(
            success=True,
            data={"preview": data, "action": "create_ticket"}
        )
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{self.config.base_url}/Ticket",
            headers=self._headers(),
            json=data
        )
        response.raise_for_status()
        result = response.json()
        return ToolResult(success=True, data={"id": result["id"]})
```

### Add Comment/Followup

```python
@governed_operation(OperationType.WRITE)
async def add_followup(
    self,
    ticket_id: int,
    content: str,
    is_private: bool = False,
    dry_run: bool = True
) -> ToolResult:
    """Add followup to ticket."""
    data = {
        "input": {
            "items_id": ticket_id,
            "itemtype": "Ticket",
            "content": content,
            "is_private": int(is_private)
        }
    }
    
    if dry_run:
        return ToolResult(
            success=True,
            data={"preview": data, "action": "add_followup"}
        )
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{self.config.base_url}/ITILFollowup",
            headers=self._headers(),
            json=data
        )
        response.raise_for_status()
        return ToolResult(success=True, data=response.json())
```

## GLPI Field IDs

Common search field IDs for the Search API:

| Field ID | Name | Description |
|----------|------|-------------|
| 1 | name | Ticket title |
| 2 | id | Ticket ID |
| 3 | priority | Priority (1-6) |
| 12 | status | Status code |
| 15 | date | Open date |
| 16 | closedate | Close date |
| 18 | time_to_resolve | SLA deadline |
| 21 | content | Description |

## Status Codes

| Code | Status |
|------|--------|
| 1 | New |
| 2 | Processing (assigned) |
| 3 | Processing (planned) |
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

## Full Tool Implementation

```python
from ..base import APITool, ToolResult, Operation

class GLPITool(APITool):
    def __init__(self, config: GLPIConfig):
        self.client = GLPIClient(config)
    
    @property
    def name(self) -> str:
        return "glpi"
    
    @property
    def description(self) -> str:
        return "GLPI ITSM - Ticket management, SLA monitoring, asset queries"
    
    @property
    def operations(self) -> list[Operation]:
        return [
            Operation(name="get_tickets", description="List tickets", method="GET"),
            Operation(name="get_ticket", description="Get single ticket", method="GET"),
            Operation(name="create_ticket", description="Create ticket", method="POST", requires_confirmation=True),
            Operation(name="add_followup", description="Add comment", method="POST", requires_confirmation=True),
        ]
    
    async def read(self, operation: str, params: dict) -> ToolResult:
        await self.client.init_session()
        try:
            if operation == "get_tickets":
                data = await self.client.get_tickets(**params)
            elif operation == "get_ticket":
                data = await self.client.get_ticket(params["id"])
            else:
                return ToolResult(success=False, error=f"Unknown operation: {operation}")
            return ToolResult(success=True, data=data)
        finally:
            await self.client.kill_session()
    
    async def write(self, operation: str, data: dict, dry_run: bool = True) -> ToolResult:
        await self.client.init_session()
        try:
            if operation == "create_ticket":
                return await self.client.create_ticket(**data, dry_run=dry_run)
            elif operation == "add_followup":
                return await self.client.add_followup(**data, dry_run=dry_run)
            else:
                return ToolResult(success=False, error=f"Unknown operation: {operation}")
        finally:
            await self.client.kill_session()
```

## References

- [GLPI REST API Documentation](https://glpi-project.org/doc/api)
- [GLPI Search API](https://glpi-project.org/doc/api/search.html)
