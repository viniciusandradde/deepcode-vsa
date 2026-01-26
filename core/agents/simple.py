"""Simple agent implementation using LangChain 1.0 create_agent.

Based on fastapp approach with dynamic model/tool configuration.
"""

import os
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Iterable, List, Optional

from dotenv import load_dotenv
from langchain.agents import AgentState, create_agent
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from core.agents.base import BaseAgent
from core.middleware.dynamic import DynamicSettingsMiddleware
from typing import Dict, Any


load_dotenv()

DEFAULT_OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
DEBUG_AGENT_LOGS = os.getenv("DEBUG_AGENT_LOGS", "false").strip().lower() in {"1", "true", "yes"}


def dbg(*args):
    """Debug logging helper."""
    if DEBUG_AGENT_LOGS:
        try:
            print(*args, flush=True)
        except Exception:
            pass


class SimpleAgent(BaseAgent):
    """Simple agent using LangChain 1.0 create_agent.
    
    Features:
    - Dynamic model/tool configuration via middleware
    - Support for OpenRouter models
    - Configurable system prompts
    """
    
    def __init__(
        self,
        model_name: str,
        system_prompt: Optional[str] = None,
        tools: Optional[Iterable[BaseTool]] = None,
        checkpointer: Optional[Any] = None,
        openrouter_api_key: Optional[str] = None,
        openrouter_base_url: str = DEFAULT_OPENROUTER_BASE_URL,
        temperature: float = 0.2,
        use_dynamic_middleware: bool = True,
    ):
        """Initialize simple agent.
        
        Args:
            model_name: Model identifier (e.g., "google/gemini-2.5-flash")
            system_prompt: System instructions for the agent
            tools: List of tools available to the agent
            openrouter_api_key: OpenRouter API key (falls back to env)
            openrouter_base_url: OpenRouter API base URL
            temperature: Model temperature
            use_dynamic_middleware: Enable dynamic settings middleware
        """
        api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("Defina OPENROUTER_API_KEY para inicializar o agente.")
        
        # Default system prompt with current date
        if system_prompt is None:
            data_atual_sp = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y")
            system_prompt = (
                f"Você é um assistente útil. Hoje é {data_atual_sp} (fuso de São Paulo). "
                "Seja direto e preciso nas respostas."
            )
        
        model = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=api_key,
            openai_api_base=openrouter_base_url,
        )
        
        super().__init__(
            model=model,
            tools=tools,
            system_prompt=system_prompt,
            name="SimpleAgent"
        )
        
        self.model_name = model_name
        self.openrouter_api_key = api_key
        self.openrouter_base_url = openrouter_base_url
        self.temperature = temperature
        self.use_dynamic_middleware = use_dynamic_middleware
        self.checkpointer = checkpointer
        self._graph = None
    
    def create_graph(self):
        """Create agent graph with optional dynamic middleware and checkpointer.
        
        Returns:
            Compiled LangGraph graph
        """
        if self._graph is None:
            middlewares = []
            if self.use_dynamic_middleware:
                middlewares.append(DynamicSettingsMiddleware())
            
            # create_agent returns a compiled graph
            self._graph = create_agent(
                model=self.model,
                tools=self.tools,
                system_prompt=self.system_prompt,
                state_schema=AgentState,
                middleware=middlewares,
                checkpointer=self.checkpointer,
            )
        
        return self._graph
    
    def invoke(self, input: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Invoke agent synchronously."""
        graph = self.create_graph()
        return graph.invoke(input, config or {})
    
    async def ainvoke(self, input: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Invoke agent asynchronously."""
        graph = self.create_graph()
        return await graph.ainvoke(input, config or {})


def create_simple_agent(
    model_name: str,
    system_prompt: Optional[str] = None,
    tools: Optional[Iterable[BaseTool]] = None,
    checkpointer: Optional[Any] = None,
    openrouter_api_key: Optional[str] = None,
    openrouter_base_url: str = DEFAULT_OPENROUTER_BASE_URL,
    temperature: float = 0.2,
    use_dynamic_middleware: bool = True,
) -> SimpleAgent:
    """Factory function to create a simple agent.
    
    Args:
        model_name: Model identifier
        system_prompt: System instructions
        tools: List of tools
        openrouter_api_key: OpenRouter API key
        openrouter_base_url: OpenRouter base URL
        temperature: Model temperature
        use_dynamic_middleware: Enable dynamic middleware
        
    Returns:
        Configured SimpleAgent instance
    """
    return SimpleAgent(
        model_name=model_name,
        system_prompt=system_prompt,
        tools=tools,
        checkpointer=checkpointer,
        openrouter_api_key=openrouter_api_key,
        openrouter_base_url=openrouter_base_url,
        temperature=temperature,
        use_dynamic_middleware=use_dynamic_middleware,
    )

