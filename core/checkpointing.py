"""Checkpointing utilities for agent state persistence.

Uses PostgresSaver (sync) and AsyncPostgresSaver (async) for production.
Uses MemorySaver as fallback.

Reference: LangGraph checkpoint-postgres documentation
"""

import os
import asyncio
from typing import Optional, Any, Tuple

from dotenv import load_dotenv

from core.database import get_db_url


load_dotenv()

# Global checkpointer instances
_sync_checkpointer: Optional[Any] = None
_async_checkpointer: Optional[Any] = None
_async_pool = None
_postgres_connection = None
_initialized: bool = False


async def initialize_checkpointer():
    """Initialize both sync and async checkpointers."""
    global _sync_checkpointer, _async_checkpointer, _async_pool, _postgres_connection, _initialized
    
    use_postgres = os.getenv("USE_POSTGRES_CHECKPOINT", "true").lower() == "true"
    
    if not use_postgres:
        print("ℹ️  USE_POSTGRES_CHECKPOINT=false, using MemorySaver")
        from langgraph.checkpoint.memory import MemorySaver
        saver = MemorySaver()
        _sync_checkpointer = saver
        _async_checkpointer = saver
        _initialized = True
        return

    try:
        from langgraph.checkpoint.postgres import PostgresSaver
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        import psycopg
        from psycopg.rows import dict_row
        from psycopg_pool import AsyncConnectionPool
        
        db_url = get_db_url()
        print(f"🔄 Initializing PostgreSQL Checkpointers...")
        
        # 1. Sync Checkpointer (for /chat endpoint)
        # Create persistent connection with dict_row factory (REQUIRED by PostgresSaver)
        _postgres_connection = psycopg.connect(
            db_url, 
            autocommit=True, 
            prepare_threshold=0,
            row_factory=dict_row  # Required: PostgresSaver accesses columns by name
        )
        _sync_checkpointer = PostgresSaver(_postgres_connection)
        print("✅ Sync PostgresSaver initialized with dict_row factory")
        
        # 2. Async Checkpointer (for /stream endpoint)
        # Create persistent async pool with dict_row factory
        _async_pool = AsyncConnectionPool(
            conninfo=db_url,
            max_size=20,
            kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row}
        )
        await _async_pool.open()
        _async_checkpointer = AsyncPostgresSaver(_async_pool)
        print("✅ Async PostgresSaver initialized with dict_row factory")

        # 3. Setup tables (using async checkpointer is fine)
        try:
            print("🔧 Running async checkpointer setup...")
            await _async_checkpointer.setup()
            print("✅ PostgreSQL checkpointer tables ready")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("ℹ️  Tables already exist")
            else:
                print(f"⚠️  Setup warning: {e}")

        print("✅ PostgreSQL Checkpointers (Sync & Async) initialized")
        _initialized = True
        
    except ImportError as e:
        print(f"⚠️  Missing dependencies: {e}")
        print("ℹ️  Install: pip install langgraph-checkpoint-postgres psycopg-pool")
        _fallback_to_memory()
    except Exception as e:
        print(f"⚠️  Failed to initialize PostgreSQL checkpointers: {e}")
        _fallback_to_memory()


def _fallback_to_memory():
    """Fallback to MemorySaver."""
    global _sync_checkpointer, _async_checkpointer, _initialized
    from langgraph.checkpoint.memory import MemorySaver
    saver = MemorySaver()
    _sync_checkpointer = saver
    _async_checkpointer = saver
    _initialized = True
    print("⚠️  Fallback to MemorySaver active")


def get_checkpointer():
    """Get sync checkpointer (legacy support)."""
    global _sync_checkpointer
    if _sync_checkpointer is None:
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()
    return _sync_checkpointer


def get_async_checkpointer():
    """Get async checkpointer."""
    global _async_checkpointer
    if _async_checkpointer is None:
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()
    return _async_checkpointer


async def cleanup_checkpointer():
    """Cleanup resources."""
    global _async_pool, _postgres_connection, _sync_checkpointer, _async_checkpointer, _initialized
    
    if _async_pool:
        await _async_pool.close()
        print("ℹ️  Async pool closed")
        
    if _postgres_connection:
        _postgres_connection.close()
        print("ℹ️  Sync connection closed")
        
    _async_pool = None
    _postgres_connection = None
    _sync_checkpointer = None
    _async_checkpointer = None
    _initialized = False
    print("ℹ️  Checkpointer cleanup complete")
