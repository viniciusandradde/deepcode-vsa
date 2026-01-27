"""Agents API routes."""

from fastapi import APIRouter, HTTPException

from api.models.requests import AgentInvokeRequest
from api.models.responses import AgentResponse


router = APIRouter()


@router.get("")
async def list_agents():
    """List available agents."""
    return {
        "agents": [
            {"id": "simple", "name": "Simple Agent", "description": "Basic agent with dynamic tools"},
            {"id": "unified", "name": "Unified Agent", "description": "Combined agent with ITIL classification, GUT scoring, and multi-intent planning"},
            {"id": "vsa", "name": "VSA Agent", "description": "Virtual Support Agent with ITIL methodology (legacy)"},
        ]
    }


@router.post("/{agent_id}/invoke", response_model=AgentResponse)
async def invoke_agent(agent_id: str, request: AgentInvokeRequest):
    """Invoke a specific agent."""
    try:
        if agent_id == "simple":
            from core.agents.simple import create_simple_agent
            agent = create_simple_agent(model_name="google/gemini-2.5-flash")
            result = await agent.ainvoke(request.input, request.config)
            return AgentResponse(output=result, agent_id=agent_id)
        elif agent_id == "unified":
            from core.agents.unified import create_unified_agent
            agent = create_unified_agent(
                model_name="google/gemini-2.5-flash",
                enable_itil=True,
                enable_planning=True,
            )
            result = await agent.ainvoke(request.input, request.config)
            return AgentResponse(output=result, agent_id=agent_id)
        elif agent_id == "vsa":
            from core.agents.vsa import VSAAgent
            agent = VSAAgent(model_name="google/gemini-2.5-flash")
            result = await agent.ainvoke(request.input, request.config)
            return AgentResponse(output=result, agent_id=agent_id)
        else:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent invocation error: {str(e)}")

