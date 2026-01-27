"""Checkpointing utilities for agent state persistence."""

import os
from typing import Optional

from dotenv import load_dotenv

from core.database import get_db_url


load_dotenv()


def get_checkpointer():
    """Get appropriate checkpointer for environment.

    Returns:
        MemorySaver (PostgresSaver requires context manager setup)

    Note: PostgreSQL checkpointing requires proper async context management.
    For now, using MemorySaver. To implement PostgreSQL:
    1. Use AsyncPostgresSaver with async context manager
    2. Initialize in async context: async with AsyncPostgresSaver.from_conn_string(url) as saver:
    3. Or use a connection pool and pass connection to saver

    See: https://langchain-ai.github.io/langgraph/reference/checkpoints/#asyncpostgressaver
    """
    # For now, always use MemorySaver until we implement proper async context
    # TODO: Implement PostgreSQL checkpointing with proper async context management
    print("ℹ️  Using MemorySaver (PostgreSQL checkpointing requires async context - TODO)")
    from langgraph.checkpoint.memory import MemorySaver
    return MemorySaver()

