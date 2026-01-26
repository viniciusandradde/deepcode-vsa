"""Checkpointing utilities for agent state persistence."""

import os
from typing import Optional

from dotenv import load_dotenv

from core.database import get_db_url


load_dotenv()


def get_checkpointer():
    """Get appropriate checkpointer for environment.
    
    Returns:
        MemorySaver for development, PostgresSaver for production
    """
    use_postgres = os.getenv("USE_POSTGRES_CHECKPOINT", "true").lower() == "true"
    
    if use_postgres:
        try:
            from langgraph.checkpoint.postgres import PostgresSaver
            db_url = get_db_url()
            
            # PostgresSaver.from_conn_string returns the saver directly
            # Setup will be called automatically when needed (lazy initialization)
            try:
                checkpointer = PostgresSaver.from_conn_string(db_url)
                # Don't call setup() here - it will be called automatically when first used
                # or we can skip it if tables already exist
                return checkpointer
            except Exception as e:
                print(f"Warning: Failed to initialize PostgresSaver, falling back to MemorySaver: {e}")
                from langgraph.checkpoint.memory import MemorySaver
                return MemorySaver()
        except Exception as e:
            print(f"Warning: Failed to initialize PostgresSaver, falling back to MemorySaver: {e}")
            from langgraph.checkpoint.memory import MemorySaver
            return MemorySaver()
    else:
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()

