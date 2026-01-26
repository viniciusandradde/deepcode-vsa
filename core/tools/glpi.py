"""GLPI Integration Tools."""

from typing import Optional, List
from langchain.tools import tool

from ..integrations.glpi_client import GLPIClient
from ..config import get_settings

_client: Optional[GLPIClient] = None

def get_keys_from_env():
    """Get keys from settings."""
    settings = get_settings()
    return settings.glpi

def get_client() -> GLPIClient:
    """Get or create GLPI client singleton."""
    global _client
    if not _client:
        settings = get_keys_from_env()
        _client = GLPIClient(settings)
    return _client

@tool
async def glpi_create_ticket(
    name: str, 
    content: str, 
    urgency: int = 3, 
    priority: int = 3, 
    dry_run: bool = True
) -> dict:
    """Create a new support ticket in GLPI.
    
    Args:
        name: Brief title of the ticket
        content: Detailed description of the issue
        urgency: Urgency level (1-5, default 3)
        priority: Priority level (1-5, default 3)
        dry_run: If True (default), simulates creation and returns preview.
    """
    client = get_client()
    result = await client.create_ticket(name, content, urgency, priority, dry_run)
    if not result.success:
        return {"error": result.error}
    return result.output

@tool
async def glpi_get_tickets(
    status: Optional[List[int]] = None,
    limit: int = 10
) -> dict:
    """Get list of tickets from GLPI.
    
    Args:
        status: Optional list of status IDs to filter (1=New, 2=Processing, etc.)
        limit: Max number of tickets to return (default 10)
    """
    client = get_client()
    # status input from LLM might be list of ints or string representation
    if status and isinstance(status, str):
        try:
            status = [int(s.strip()) for s in status.split(",")]
        except:
            pass
            
    result = await client.get_tickets(status, limit)
    if not result.success:
        return {"error": result.error}
    return result.output

@tool
async def glpi_get_ticket_details(ticket_id: int) -> dict:
    """Get full details of a specific GLPI ticket.
    
    Args:
        ticket_id: The ID of the ticket
    """
    client = get_client()
    result = await client.get_ticket(ticket_id)
    if not result.success:
        return {"error": result.error}
    return result.output
