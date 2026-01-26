"""Tool Registry for dynamic API tool management.

Reference: ADR-006
"""

from typing import Optional

from .base import APITool


class ToolRegistry:
    """Central registry for API tools.
    
    Allows dynamic registration and discovery of tools
    for the agent to use.
    """
    
    def __init__(self):
        self._tools: dict[str, APITool] = {}
    
    def register(self, tool: APITool) -> None:
        """Register a new tool.
        
        Raises:
            ValueError: If tool with same name already registered
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool
    
    def unregister(self, name: str) -> None:
        """Unregister a tool by name."""
        if name in self._tools:
            del self._tools[name]
    
    def get(self, name: str) -> Optional[APITool]:
        """Get tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> list[APITool]:
        """List all registered tools."""
        return list(self._tools.values())
    
    def get_tools_for_llm(self) -> list[dict]:
        """Get tools in LLM function calling format."""
        return [
            {
                "type": "function",
                "function": tool.get_schema()
            }
            for tool in self._tools.values()
        ]
    
    def __contains__(self, name: str) -> bool:
        return name in self._tools
    
    def __len__(self) -> int:
        return len(self._tools)


# Global registry instance
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get or create global registry instance."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
