"""Real integration tests for PostgreSQL persistence."""

import pytest
import asyncio
from typing import AsyncGenerator
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection
from deepcode_vsa.config import get_settings
from dotenv import load_dotenv
import os

# Explicitly load .env to match docker-compose environment behavior
load_dotenv()

# Get connection string from settings
settings = get_settings()
DB_URI = settings.database.connection_string

# If using docker-compose mapped port, we need to adjust localhost access
# Settings might load DB_PORT from .env (e.g. 5435 or 5432), but docker-compose.yml is hardcoded to 3435:5432
# So we MUST force port 3435 for localhost connections in this test suite
if "localhost" in settings.database.host or "127.0.0.1" in settings.database.host or "postgres" in settings.database.host:
     # Rebuild URI with hardcoded port 3435 and localhost
     from urllib.parse import quote_plus
     safe_pass = quote_plus(settings.database.password)
     safe_user = quote_plus(settings.database.user)
     DB_URI = f"postgresql://{safe_user}:{safe_pass}@localhost:3435/{settings.database.database}"


@pytest.mark.asyncio
async def test_postgres_connection():
    """Test real connection to PostgreSQL."""
    try:
        async with await AsyncConnection.connect(DB_URI) as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                result = await cur.fetchone()
                assert result[0] == 1
    except Exception as e:
        pytest.fail(f"Could not connect to PostgreSQL at {DB_URI}: {e}")


@pytest.mark.asyncio
async def test_langgraph_persistence():
    """Test LangGraph checkpointing with real Postgres."""
    import uuid

    # Use from_conn_string which handles connection pooling and autocommit properly
    async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        # 1. Setup tables (requires autocommit for CREATE INDEX CONCURRENTLY)
        await checkpointer.setup()

        # 2. Save a checkpoint with unique thread_id
        thread_id = f"test-thread-{uuid.uuid4().hex[:8]}"
        config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}
        checkpoint = {
            "v": 1,
            "ts": "2024-01-01T00:00:00.000000+00:00",
            "channel_values": {},
            "channel_versions": {"__start__": 1},
            "versions_seen": {"__start__": {"__start__": 1}},
            "pending_sends": [],
            "id": "checkpoint-001"
        }

        await checkpointer.aput(config, checkpoint, {}, {})

        # 3. Retrieve checkpoint and verify basic structure
        loaded = await checkpointer.aget(config)

        assert loaded is not None
        assert loaded["id"] == "checkpoint-001"
        assert loaded["v"] == 1
