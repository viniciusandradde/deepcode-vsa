"""GLPI REST API Client.

Reference: .claude/skills/glpi-integration/SKILL.md
"""

from typing import Optional

import httpx

from ..base import ToolResult
from ...config.settings import GLPISettings


class GLPIClient:
    """GLPI REST API client.
    
    Implements session-based authentication and
    ticket management operations.
    """
    
    def __init__(self, settings: GLPISettings):
        self.settings = settings
        self.base_url = settings.base_url.rstrip("/")
        self.session_token: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def headers(self) -> dict:
        """Get request headers."""
        headers = {
            "Content-Type": "application/json",
            "App-Token": self.settings.app_token,
        }
        if self.session_token:
            headers["Session-Token"] = self.session_token
        return headers
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client
    
    async def init_session(self) -> ToolResult:
        """Initialize GLPI session.
        
        Uses User-Token authentication.
        """
        client = await self._get_client()
        
        try:
            response = await client.get(
                f"{self.base_url}/initSession",
                headers={
                    "Content-Type": "application/json",
                    "App-Token": self.settings.app_token,
                    "Authorization": f"user_token {self.settings.user_token}",
                }
            )
            response.raise_for_status()
            data = response.json()
            self.session_token = data.get("session_token")
            
            return ToolResult.ok(
                {"session_token": self.session_token},
                operation="init_session"
            )
        except httpx.HTTPStatusError as e:
            return ToolResult.fail(
                f"GLPI auth failed: {e.response.status_code}",
                operation="init_session"
            )
        except Exception as e:
            return ToolResult.fail(str(e), operation="init_session")
    
    async def kill_session(self) -> ToolResult:
        """Kill current session."""
        if not self.session_token:
            return ToolResult.ok({}, operation="kill_session")
        
        client = await self._get_client()
        
        try:
            await client.get(
                f"{self.base_url}/killSession",
                headers=self.headers
            )
            self.session_token = None
            return ToolResult.ok({}, operation="kill_session")
        except Exception as e:
            return ToolResult.fail(str(e), operation="kill_session")
    
    async def get_tickets(
        self,
        status: Optional[list[int]] = None,
        limit: int = 50,
        order: str = "DESC"
    ) -> ToolResult:
        """Get tickets from GLPI.
        
        Args:
            status: Filter by status IDs (1=new, 2=processing, etc.)
            limit: Max results
            order: Sort order (ASC/DESC)
        """
        if not self.session_token:
            init_result = await self.init_session()
            if not init_result.success:
                return init_result
        
        client = await self._get_client()
        
        params = {
            "range": f"0-{limit-1}",
            "order": order,
        }
        
        if status:
            params["searchText[status]"] = ",".join(str(s) for s in status)
        
        try:
            response = await client.get(
                f"{self.base_url}/Ticket",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            tickets = response.json()
            
            return ToolResult.ok(
                {"tickets": tickets, "count": len(tickets)},
                operation="get_tickets"
            )
        except httpx.HTTPStatusError as e:
            return ToolResult.fail(
                f"Get tickets failed: {e.response.status_code}",
                operation="get_tickets"
            )
        except Exception as e:
            return ToolResult.fail(str(e), operation="get_tickets")
    
    async def get_ticket(self, ticket_id: int) -> ToolResult:
        """Get single ticket details."""
        if not self.session_token:
            init_result = await self.init_session()
            if not init_result.success:
                return init_result
        
        client = await self._get_client()
        
        try:
            response = await client.get(
                f"{self.base_url}/Ticket/{ticket_id}",
                headers=self.headers
            )
            response.raise_for_status()
            ticket = response.json()
            
            return ToolResult.ok(
                {"ticket": ticket},
                operation="get_ticket"
            )
        except httpx.HTTPStatusError as e:
            return ToolResult.fail(
                f"Get ticket failed: {e.response.status_code}",
                operation="get_ticket"
            )
        except Exception as e:
            return ToolResult.fail(str(e), operation="get_ticket")
    
    async def create_ticket(
        self,
        name: str,
        content: str,
        urgency: int = 3,
        priority: int = 3,
        dry_run: bool = True
    ) -> ToolResult:
        """Create a new ticket.
        
        Args:
            name: Ticket title
            content: Ticket description
            urgency: 1 (very low) to 5 (very high)
            priority: 1 (very low) to 6 (major)
            dry_run: If True, simulate without creating
        """
        ticket_data = {
            "input": {
                "name": name,
                "content": content,
                "urgency": urgency,
                "priority": priority,
            }
        }
        
        # Dry run - return preview
        if dry_run:
            return ToolResult.ok(
                {
                    "preview": ticket_data,
                    "dry_run": True,
                    "message": "Ticket would be created with these values"
                },
                operation="create_ticket"
            )
        
        if not self.session_token:
            init_result = await self.init_session()
            if not init_result.success:
                return init_result
        
        client = await self._get_client()
        
        try:
            response = await client.post(
                f"{self.base_url}/Ticket",
                headers=self.headers,
                json=ticket_data
            )
            response.raise_for_status()
            result = response.json()
            
            return ToolResult.ok(
                {"ticket_id": result.get("id"), "created": True},
                operation="create_ticket"
            )
        except httpx.HTTPStatusError as e:
            return ToolResult.fail(
                f"Create ticket failed: {e.response.status_code}",
                operation="create_ticket"
            )
        except Exception as e:
            return ToolResult.fail(str(e), operation="create_ticket")
    
    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
