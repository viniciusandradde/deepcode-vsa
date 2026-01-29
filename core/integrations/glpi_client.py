"""GLPI REST API Client.

Reference: .claude/skills/glpi-integration/SKILL.md
"""


import httpx

import httpx
from ..config import GLPISettings

class ToolResult:
    """Simple result wrapper."""
    def __init__(self, success: bool, output: dict | str, operation: str, error: str | None = None):
        self.success = success
        self.output = output
        self.operation = operation
        self.error = error
    
    @classmethod
    def ok(cls, output, operation):
        return cls(True, output, operation)
        
    @classmethod
    def fail(cls, error, operation):
        return cls(False, {}, operation, error)


class GLPIClient:
    """GLPI REST API client.
    
    Implements session-based authentication and
    ticket management operations.
    """

    def __init__(self, settings: GLPISettings):
        self.settings = settings
        self.base_url = settings.base_url.rstrip("/")
        self.session_token: str | None = None
        self._client: httpx.AsyncClient | None = None

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

        Supports both Basic Auth (username/password) and User-Token authentication.
        Basic Auth is preferred if username is provided.
        """
        import base64
        
        client = await self._get_client()

        # Build authorization header
        if self.settings.username and self.settings.password:
            # Basic Auth (preferred)
            auth_string = base64.b64encode(
                f"{self.settings.username}:{self.settings.password}".encode()
            ).decode()
            auth_header = f"Basic {auth_string}"
        elif self.settings.user_token:
            # User Token fallback
            auth_header = f"user_token {self.settings.user_token}"
        else:
            return ToolResult.fail(
                "GLPI authentication not configured. "
                "Please provide either GLPI_USERNAME/GLPI_PASSWORD or GLPI_USER_TOKEN.",
                operation="init_session"
            )

        try:
            response = await client.get(
                f"{self.base_url}/initSession",
                headers={
                    "Content-Type": "application/json",
                    "App-Token": self.settings.app_token,
                    "Authorization": auth_header,
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
                f"GLPI auth failed: {e.response.status_code} - {e.response.text}",
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
        status: list[int] | None = None,
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

    async def get_tickets_new_unassigned(
        self,
        min_age_hours: int = 24,
        limit: int = 20
    ) -> ToolResult:
        """Get tickets with status New (1), unassigned, created more than X hours ago.
        
        Args:
            min_age_hours: Minimum age in hours (default 24h)
            limit: Max results
        """
        # First get all new tickets
        result = await self.get_tickets(status=[1], limit=100)
        if not result.success:
            return result
        
        from datetime import datetime, timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(hours=min_age_hours)
        
        filtered = []
        for t in result.output.get("tickets", []):
            # Check assignment (users_id_assign == 0 or missing means unassigned)
            assigned = t.get("users_id_assign") or t.get("_users_id_assign") or 0
            if assigned != 0:
                continue
            
            # Check creation date
            date_str = t.get("date") or t.get("date_creation")
            if date_str:
                try:
                    # GLPI returns dates like "2026-01-27 10:30:00"
                    created = datetime.fromisoformat(date_str.replace(" ", "T"))
                    if created.tzinfo is None:
                        created = created.replace(tzinfo=timezone.utc)
                    if created > cutoff:
                        continue  # Too recent, skip
                except (ValueError, TypeError):
                    pass  # Include if date parsing fails
            
            filtered.append(t)
        
        return ToolResult.ok(
            {
                "tickets": filtered[:limit],
                "count": len(filtered[:limit]),
                "total_found": len(filtered),
                "filter": "new_unassigned_old",
                "min_age_hours": min_age_hours
            },
            operation="get_tickets_new_unassigned"
        )

    async def get_tickets_pending_old(
        self,
        min_age_days: int = 7,
        limit: int = 20
    ) -> ToolResult:
        """Get tickets with status Pending (4) that haven't been updated in X days.
        
        Args:
            min_age_days: Minimum days since last update (default 7)
            limit: Max results
        """
        # First get all pending tickets
        result = await self.get_tickets(status=[4], limit=100)
        if not result.success:
            return result
        
        from datetime import datetime, timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(days=min_age_days)
        
        filtered = []
        for t in result.output.get("tickets", []):
            # Check last modification date
            date_str = t.get("date_mod") or t.get("date")
            if date_str:
                try:
                    modified = datetime.fromisoformat(date_str.replace(" ", "T"))
                    if modified.tzinfo is None:
                        modified = modified.replace(tzinfo=timezone.utc)
                    if modified > cutoff:
                        continue  # Updated recently, skip
                except (ValueError, TypeError):
                    pass  # Include if date parsing fails
            
            filtered.append(t)
        
        return ToolResult.ok(
            {
                "tickets": filtered[:limit],
                "count": len(filtered[:limit]),
                "total_found": len(filtered),
                "filter": "pending_old",
                "min_age_days": min_age_days
            },
            operation="get_tickets_pending_old"
        )

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
