"""Database utilities for PostgreSQL connection with connection pooling."""

import logging

import psycopg
from psycopg_pool import ConnectionPool

from core.config import get_settings

logger = logging.getLogger(__name__)

_pool: ConnectionPool | None = None


def get_db_url() -> str:
    """Build PostgreSQL connection URL from settings (with URL-encoded password)."""
    return get_settings().database.connection_string


def _get_pool() -> ConnectionPool:
    """Get or create the connection pool (lazy singleton)."""
    global _pool
    if _pool is None:
        db_url = get_db_url()
        _pool = ConnectionPool(
            conninfo=db_url,
            min_size=2,
            max_size=20,
            timeout=30,
            max_lifetime=300,  # recycle connections every 5 min
            max_idle=60,       # close idle connections after 60s
            open=True,
        )
        logger.info("Database connection pool created (min=2, max=20)")
    return _pool


def get_conn():
    """Get PostgreSQL connection from pool.

    Returns a context-managed connection. Usage:
        conn = get_conn()
        # ... use conn ...
        conn.close()  # returns to pool
    """
    return _get_pool().connection()


def return_conn(conn):
    """Return a connection to the pool."""
    _get_pool().putconn(conn)


def close_pool():
    """Close the connection pool. Call during shutdown."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None
        logger.info("Database connection pool closed")
