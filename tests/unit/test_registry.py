"""Tests for Tool Registry."""

import pytest

from deepcode_vsa.integrations.base import APITool, Operation, ToolResult
from deepcode_vsa.integrations.registry import ToolRegistry


class MockTool(APITool):
    """Mock tool for testing."""

    def __init__(self, tool_name: str = "mock"):
        self._name = tool_name

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return "A mock tool for testing"

    @property
    def operations(self) -> list[Operation]:
        return [
            Operation(name="read_data", description="Read data", method="GET"),
            Operation(
                name="write_data", 
                description="Write data", 
                method="POST", 
                requires_confirmation=True
            ),
        ]

    async def read(self, operation: str, params: dict) -> ToolResult:
        return ToolResult.ok({"operation": operation, "params": params})

    async def write(self, operation: str, data: dict, dry_run: bool = True) -> ToolResult:
        return ToolResult.ok({"operation": operation, "data": data, "dry_run": dry_run})


class TestToolResult:
    """Tests for ToolResult."""

    def test_ok_result(self):
        """Test successful result creation."""
        result = ToolResult.ok({"key": "value"}, source="test")

        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.error is None
        assert result.metadata == {"source": "test"}

    def test_fail_result(self):
        """Test failed result creation."""
        result = ToolResult.fail("Something went wrong", code=500)

        assert result.success is False
        assert result.data is None
        assert result.error == "Something went wrong"
        assert result.metadata == {"code": 500}


class TestToolRegistry:
    """Tests for ToolRegistry."""

    def test_register_tool(self):
        """Test tool registration."""
        registry = ToolRegistry()
        tool = MockTool("test_tool")

        registry.register(tool)

        assert "test_tool" in registry
        assert len(registry) == 1

    def test_register_duplicate(self):
        """Test duplicate registration raises error."""
        registry = ToolRegistry()
        tool = MockTool("duplicate")

        registry.register(tool)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(tool)

    def test_get_tool(self):
        """Test getting tool by name."""
        registry = ToolRegistry()
        tool = MockTool("my_tool")
        registry.register(tool)

        retrieved = registry.get("my_tool")

        assert retrieved is tool

    def test_get_nonexistent(self):
        """Test getting non-existent tool."""
        registry = ToolRegistry()

        result = registry.get("nonexistent")

        assert result is None

    def test_unregister_tool(self):
        """Test tool unregistration."""
        registry = ToolRegistry()
        tool = MockTool("to_remove")
        registry.register(tool)

        registry.unregister("to_remove")

        assert "to_remove" not in registry
        assert len(registry) == 0

    def test_list_tools(self):
        """Test listing all tools."""
        registry = ToolRegistry()
        tool1 = MockTool("tool1")
        tool2 = MockTool("tool2")

        registry.register(tool1)
        registry.register(tool2)

        tools = registry.list_tools()

        assert len(tools) == 2
        assert tool1 in tools
        assert tool2 in tools

    def test_get_tools_for_llm(self):
        """Test getting tools in LLM format."""
        registry = ToolRegistry()
        tool = MockTool("llm_tool")
        registry.register(tool)

        llm_tools = registry.get_tools_for_llm()

        assert len(llm_tools) == 1
        assert llm_tools[0]["type"] == "function"
        assert llm_tools[0]["function"]["name"] == "llm_tool"
        assert "description" in llm_tools[0]["function"]


class TestMockTool:
    """Tests for the MockTool implementation."""

    @pytest.mark.asyncio
    async def test_read_operation(self):
        """Test read operation."""
        tool = MockTool()

        result = await tool.read("read_data", {"id": 123})

        assert result.success is True
        assert result.data["operation"] == "read_data"
        assert result.data["params"] == {"id": 123}

    @pytest.mark.asyncio
    async def test_write_operation(self):
        """Test write operation."""
        tool = MockTool()

        result = await tool.write("write_data", {"name": "test"}, dry_run=True)

        assert result.success is True
        assert result.data["dry_run"] is True

    def test_get_schema(self):
        """Test schema generation."""
        tool = MockTool("schema_test")

        schema = tool.get_schema()

        assert schema["name"] == "schema_test"
        assert schema["description"] == "A mock tool for testing"
        assert len(schema["operations"]) == 2
