"""Checkpointing utilities for agent state persistence.

Note: PostgreSQL checkpointing with LangGraph AsyncPostgresSaver is complex
because it requires async context management. For now, we use MemorySaver
which is fast and reliable for development.

For production persistence, we have these options:
1. Implement custom checkpointer that wraps PostgreSQL
2. Use MemorySaver + periodic backup to PostgreSQL
3. Use Redis/file-based checkpointing instead

See: .agent/PROBLEMA-PERSISTENCIA.md for detailed analysis.
"""

import os
from typing import Optional

from dotenv import load_dotenv

from core.database import get_db_url


load_dotenv()

# Global checkpointer instance
_checkpointer: Optional[any] = None


async def initialize_checkpointer():
    """Initialize checkpointer.

    Currently uses MemorySaver for simplicity and reliability.
    PostgreSQL checkpointing requires complex async context management.
    """
    global _checkpointer

    use_postgres = os.getenv("USE_POSTGRES_CHECKPOINT", "false").lower() == "true"

    if use_postgres:
        print("⚠️  PostgreSQL checkpointing not yet implemented (requires async context)")
        print("ℹ️  Using MemorySaver instead")

    print("✅ Using MemorySaver for checkpointing")
    from langgraph.checkpoint.memory import MemorySaver
    _checkpointer = MemorySaver()


async def cleanup_checkpointer():
    """Cleanup checkpointer resources."""
    global _checkpointer
    _checkpointer = None
    print("ℹ️  Checkpointer cleanup complete")


def get_checkpointer():
    """Get the global checkpointer instance.

    Returns MemorySaver (fast, reliable, but not persistent across restarts).
    """
    global _checkpointer

    if _checkpointer is None:
        print("⚠️  Checkpointer not initialized, creating MemorySaver fallback")
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()

    return _checkpointer

