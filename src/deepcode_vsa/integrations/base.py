"""Base classes for API integrations.

Reference: ADR-006 and .claude/skills/api-patterns/SKILL.md
"""

from abc import ABC, abstractmethod
from typing import Optional

from pydantic import BaseModel


class Operation(BaseModel):
    """Describes an available API operation."""
    
    name: str
    description: str
    method: str  # GET, POST, PUT, DELETE
    requires_confirmation: bool = False


class ToolResult(BaseModel):
    """Standardized result from tool operations."""
    
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    metadata: dict = {}
    
    @classmethod
    def ok(cls, data: dict, **metadata) -> "ToolResult":
        """Create successful result."""
        return cls(success=True, data=data, metadata=metadata)
    
    @classmethod
    def fail(cls, error: str, **metadata) -> "ToolResult":
        """Create failed result."""
        return cls(success=False, error=error, metadata=metadata)


class APITool(ABC):
    """Base class for all API integration tools.
    
    All integrations must implement this contract to be registered
    in the ToolRegistry and used by the agent.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of the tool."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description for LLM to understand when to use."""
        pass
    
    @property
    @abstractmethod
    def operations(self) -> list[Operation]:
        """List of available operations."""
        pass
    
    @abstractmethod
    async def read(self, operation: str, params: dict) -> ToolResult:
        """Execute read operation (GET)."""
        pass
    
    @abstractmethod
    async def write(
        self,
        operation: str,
        data: dict,
        dry_run: bool = True
    ) -> ToolResult:
        """Execute write operation (POST/PUT).
        
        Args:
            operation: Operation name
            data: Data to write
            dry_run: If True, simulate without side effects
        """
        pass
    
    def get_schema(self) -> dict:
        """Get tool schema for LLM function calling."""
        return {
            "name": self.name,
            "description": self.description,
            "operations": [op.model_dump() for op in self.operations],
        }
