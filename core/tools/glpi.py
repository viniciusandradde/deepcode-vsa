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

# Fields the LLM actually needs (slim output saves ~3,000 tokens per call)
_TICKET_SUMMARY_KEYS = {"id", "name", "status", "priority", "urgency", "date", "date_mod", "type"}


@tool
async def glpi_get_tickets(
    status: Optional[List[int]] = None,
    limit: int = 10
) -> dict:
    """Busca tickets/chamados de suporte no GLPI (helpdesk).
    Usar para: listar chamados abertos, novos, pendentes, buscar tickets por status.
    Retorna: id, nome, status, prioridade, urgência, data de abertura.

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

    # Slim down ticket JSON to essential fields only (token optimization)
    tickets = result.output.get("tickets", [])
    slim_tickets = [
        {k: v for k, v in t.items() if k in _TICKET_SUMMARY_KEYS}
        for t in tickets
    ]
    return {"tickets": slim_tickets, "count": len(slim_tickets)}

# Fields to drop from ticket details (bulky, zero value for LLM)
_TICKET_DETAIL_DROP_KEYS = {
    "links",                       # 16+ API URL objects (~2K chars)
    "content",                     # HTML duplicate of name
    "sla_waiting_duration", "ola_waiting_duration",
    "waiting_duration", "close_delay_stat", "solve_delay_stat",
    "takeintoaccount_delay_stat", "actiontime",
    "begin_waiting_date", "slalevels_id_ttr",
    "olalevels_id_ttr", "olalevels_id_tto",
    "internal_time_to_resolve", "internal_time_to_own",
    "time_to_own",
}


@tool
async def glpi_get_ticket_details(ticket_id: int) -> dict:
    """Busca detalhes completos de um ticket GLPI específico.

    Args:
        ticket_id: The ID of the ticket
    """
    client = get_client()
    result = await client.get_ticket(ticket_id)
    if not result.success:
        return {"error": result.error}

    # Strip bulky fields (links array with 16+ API URLs, HTML content)
    ticket = result.output.get("ticket", result.output)
    if isinstance(ticket, dict):
        slim = {k: v for k, v in ticket.items() if k not in _TICKET_DETAIL_DROP_KEYS}
        return {"ticket": slim}
    return result.output

@tool
async def glpi_generate_excel_report_previous_month() -> dict:
    """Gera relatório Excel 'Atendimentos por Centro de Custo' do MÊS ANTERIOR.
    
    Layout estrito conforme modelo 'INFORMÁTICA 01-2026.xlsx'.
    Busca dados via API GLPI (Locais) e agrupa por classificação.
    Retorna URL para download.
    """
    try:
        from core.reports.excel import generate_cost_center_report_excel
        import base64
        
        # Determine strict previous month range
        # Logic is inside generate_cost_center_report_excel
        
        excel_bytes, filename = await generate_cost_center_report_excel()
        
        # For now, return base64 data directly so frontend can download
        # In a real app, we might upload to S3/Blob storage and return URL
        b64_data = base64.b64encode(excel_bytes).decode('utf-8')
        
        return {
            "success": True,
            "filename": filename,
            "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "data_base64": b64_data,
            "message": f"Relatório '{filename}' gerado com sucesso."
        }
    except Exception as e:
        return {"error": str(e)}
