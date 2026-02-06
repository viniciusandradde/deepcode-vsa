"""Shared result wrapper for integration clients."""


class ToolResult:
    """Simple result wrapper for API tool operations."""

    def __init__(
        self,
        success: bool,
        output: dict | str,
        operation: str,
        error: str | None = None,
    ):
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
