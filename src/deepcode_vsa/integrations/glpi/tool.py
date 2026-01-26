"""GLPI Tool wrapper for agent integration."""

from ..base import APITool, Operation, ToolResult
from .client import GLPIClient
from ...config.settings import GLPISettings


class GLPITool(APITool):
    """GLPI integration tool for the agent.
    
    Wraps GLPIClient to implement the APITool interface.
    """
    
    def __init__(self, settings: GLPISettings):
        self._client = GLPIClient(settings)
    
    @property
    def name(self) -> str:
        return "glpi"
    
    @property
    def description(self) -> str:
        return (
            "GLPI ITSM integration. Use for ticket management: "
            "list tickets, get ticket details, create new tickets. "
            "Supports filtering by status and priority."
        )
    
    @property
    def operations(self) -> list[Operation]:
        return [
            Operation(
                name="get_tickets",
                description="List tickets with optional status filter",
                method="GET",
                requires_confirmation=False
            ),
            Operation(
                name="get_ticket",
                description="Get single ticket details by ID",
                method="GET",
                requires_confirmation=False
            ),
            Operation(
                name="create_ticket",
                description="Create a new ticket",
                method="POST",
                requires_confirmation=True
            ),
        ]
    
    async def read(self, operation: str, params: dict) -> ToolResult:
        """Execute read operations."""
        if operation == "get_tickets":
            return await self._client.get_tickets(
                status=params.get("status"),
                limit=params.get("limit", 50)
            )
        elif operation == "get_ticket":
            ticket_id = params.get("ticket_id")
            if not ticket_id:
                return ToolResult.fail("ticket_id is required")
            return await self._client.get_ticket(ticket_id)
        else:
            return ToolResult.fail(f"Unknown operation: {operation}")
    
    async def write(
        self,
        operation: str,
        data: dict,
        dry_run: bool = True
    ) -> ToolResult:
        """Execute write operations."""
        if operation == "create_ticket":
            return await self._client.create_ticket(
                name=data.get("name", ""),
                content=data.get("content", ""),
                urgency=data.get("urgency", 3),
                priority=data.get("priority", 3),
                dry_run=dry_run
            )
        else:
            return ToolResult.fail(f"Unknown operation: {operation}")
    
    async def close(self):
        """Close client connections."""
        await self._client.close()
