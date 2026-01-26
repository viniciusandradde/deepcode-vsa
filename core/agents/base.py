"""Base class for all agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Iterable
from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage


class BaseAgent(ABC):
    """Abstract base class for all agents.
    
    Provides a common interface for agent implementations and ensures
    consistent behavior across different agent types.
    """
    
    def __init__(
        self,
        model: BaseChatModel,
        tools: Optional[Iterable[BaseTool]] = None,
        system_prompt: Optional[str] = None,
        name: Optional[str] = None,
    ):
        """Initialize base agent.
        
        Args:
            model: Language model to use
            tools: List of tools available to the agent
            system_prompt: System prompt/instructions for the agent
            name: Name identifier for the agent
        """
        self.model = model
        self.tools = list(tools or [])
        self.system_prompt = system_prompt
        self.name = name or self.__class__.__name__
    
    @abstractmethod
    def create_graph(self):
        """Create and return the agent graph.
        
        Returns:
            Compiled LangGraph graph
        """
        pass
    
    @abstractmethod
    def invoke(self, input: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Invoke the agent synchronously.
        
        Args:
            input: Input dictionary with messages and other state
            config: Optional configuration (e.g., thread_id)
            
        Returns:
            Output dictionary with agent response
        """
        pass
    
    async def ainvoke(self, input: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Invoke the agent asynchronously.
        
        Args:
            input: Input dictionary with messages and other state
            config: Optional configuration (e.g., thread_id)
            
        Returns:
            Output dictionary with agent response
        """
        return self.invoke(input, config)
    
    def stream(self, input: Dict[str, Any], config: Optional[Dict[str, Any]] = None, **kwargs):
        """Stream agent responses.
        
        Args:
            input: Input dictionary with messages and other state
            config: Optional configuration
            **kwargs: Extra arguments for graph.stream (e.g., stream_mode)
            
        Yields:
            Streaming chunks from the agent
        """
        graph = self.create_graph()
        return graph.stream(input, config, **kwargs)
    
    async def astream(self, input: Dict[str, Any], config: Optional[Dict[str, Any]] = None, **kwargs):
        """Stream agent responses asynchronously.
        
        Args:
            input: Input dictionary with messages and other state
            config: Optional configuration
            **kwargs: Extra arguments for graph.astream (e.g., stream_mode)
            
        Yields:
            Streaming chunks from the agent
        """
        graph = self.create_graph()
        async for chunk in graph.astream(input, config, **kwargs):
            yield chunk
    
    def add_tool(self, tool: BaseTool):
        """Add a tool to the agent.
        
        Args:
            tool: Tool to add
        """
        self.tools.append(tool)
    
    def remove_tool(self, tool_name: str):
        """Remove a tool from the agent.
        
        Args:
            tool_name: Name of the tool to remove
        """
        self.tools = [t for t in self.tools if getattr(t, "name", None) != tool_name]

