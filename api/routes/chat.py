"""Chat API routes."""

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage
import logging
import uuid
import os

from api.models.requests import ChatRequest
from api.models.responses import ChatResponse
from core.agents.simple import SimpleAgent
from core.tools.search import tavily_search
from core.checkpointing import get_checkpointer

# Integration tools (Task 1.1)
from core.tools.glpi import glpi_get_tickets, glpi_get_ticket_details, glpi_create_ticket
from core.tools.zabbix import zabbix_get_alerts, zabbix_get_host
from core.tools.linear import linear_get_issues, linear_get_issue, linear_create_issue, linear_get_teams

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Debug flag for agent logs
DEBUG_AGENT_LOGS = os.getenv("DEBUG_AGENT_LOGS", "false").strip().lower() in {"1", "true", "yes"}

router = APIRouter()

# Initialize checkpointer
checkpointer = get_checkpointer()

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint - synchronous."""
    try:
        # Create agent with tools (Task 1.1 - Dynamic tools)
        tools = []
        if request.use_tavily:
            tools.append(tavily_search)
        
        # GLPI tools (Task 1.2)
        if request.enable_glpi:
            tools.extend([glpi_get_tickets, glpi_get_ticket_details, glpi_create_ticket])
            logger.info("✅ GLPI tools enabled")
        
        # Zabbix tools (Task 1.3)
        if request.enable_zabbix:
            tools.extend([zabbix_get_alerts, zabbix_get_host])
            logger.info("✅ Zabbix tools enabled")
        
        # Linear tools
        if request.enable_linear:
            tools.extend([linear_get_issues, linear_get_issue, linear_create_issue, linear_get_teams])
            logger.info("✅ Linear tools enabled")
        
        agent = SimpleAgent(
            model_name=request.model or os.getenv("DEFAULT_MODEL_NAME", "google/gemini-2.5-flash"),
            tools=tools,
            checkpointer=checkpointer,
        )
        
        # Generate thread_id if not provided
        thread_id = request.thread_id or f"thread_{uuid.uuid4().hex[:8]}"
        
        # Invoke agent
        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }
        
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=request.message)]},
            config=config
        )
        
        # Extract response
        messages = result.get("messages", [])
        response_text = messages[-1].content if messages else "No response generated"
        
        return ChatResponse(
            response=response_text,
            thread_id=thread_id,
            model=request.model
        )
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.post("/stream")
async def stream_chat(request: ChatRequest):
    """Chat endpoint - streaming (SSE)."""
    from fastapi.responses import StreamingResponse
    import json
    
    try:
        # Create agent with tools (Task 1.1 - Dynamic tools)
        tools = []
        if request.use_tavily:
            tools.append(tavily_search)
        
        # GLPI tools (Task 1.2)
        if request.enable_glpi:
            tools.extend([glpi_get_tickets, glpi_get_ticket_details, glpi_create_ticket])
            logger.info("✅ GLPI tools enabled (stream)")
        
        # Zabbix tools (Task 1.3)
        if request.enable_zabbix:
            tools.extend([zabbix_get_alerts, zabbix_get_host])
            logger.info("✅ Zabbix tools enabled (stream)")
        
        # Linear tools
        if request.enable_linear:
            tools.extend([linear_get_issues, linear_get_issue, linear_create_issue, linear_get_teams])
            logger.info("✅ Linear tools enabled (stream)")
        
        agent = SimpleAgent(
            model_name=request.model or os.getenv("DEFAULT_MODEL_NAME", "google/gemini-2.5-flash"),
            tools=tools,
            checkpointer=checkpointer,
        )
        
        # Generate thread_id if not provided
        thread_id = request.thread_id or f"thread_{uuid.uuid4().hex[:8]}"
        
        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        async def generate():
            try:
                # Use astream from SimpleAgent
                # Important: SimpleAgent's create_agent uses a specific graph structure
                from langchain_core.messages import AIMessage, AIMessageChunk
                
                # Use stream_mode="messages" to get deltas (tokens) for a smoother experience
                async for chunk, metadata in agent.astream(
                    {"messages": [HumanMessage(content=request.message)]},
                    config=config,
                    stream_mode="messages"
                ):
                    # In 'messages' mode, chunk is typically a message delta (AIMessageChunk)
                    if isinstance(chunk, (AIMessage, AIMessageChunk)) and chunk.content:
                        # Only stream AI content, skipping tool calls and metadata
                        if not hasattr(chunk, 'tool_calls') or not chunk.tool_calls:
                            data = {
                                "type": "content",
                                "content": chunk.content,
                                "thread_id": thread_id,
                                "model": request.model
                            }
                            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                                
                yield f"data: {json.dumps({'type': 'done', 'thread_id': thread_id}, ensure_ascii=False)}\n\n"
                
            except Exception as e:
                logger.error(f"Stream error: {str(e)}", exc_info=True)
                # Try to extract a clean string from the exception
                error_msg = str(e)
                if hasattr(e, 'body') and isinstance(e.body, dict):
                    error_msg = e.body.get('message', error_msg)
                elif "API key USD spend limit exceeded" in error_msg:
                    error_msg = "Limite de gastos da chave API do OpenRouter excedido. Verifique suas configurações de 'Spending Limit' no OpenRouter."
                
                yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")
        
    except Exception as e:
        logger.error(f"Stream setup error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Stream error: {str(e)}")
