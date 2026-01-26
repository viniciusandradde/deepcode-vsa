"""Database utilities for PostgreSQL connection."""

import os
import psycopg
from dotenv import load_dotenv


load_dotenv()


def get_db_url() -> str:
    """Build PostgreSQL connection URL from environment variables.
    
    Returns:
        PostgreSQL connection string
        
    Raises:
        RuntimeError: If required environment variables are missing
    """
    user = os.getenv("DB_USER")
    pwd = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME")
    
    if not all([user, pwd, host, name]):
        raise RuntimeError(
            "Defina DB_USER, DB_PASSWORD, DB_HOST, DB_NAME e opcionalmente DB_PORT/DB_SSLMODE"
        )
    
    sslmode = os.getenv("DB_SSLMODE", "require")
    return f"postgresql://{user}:{pwd}@{host}:{port}/{name}?sslmode={sslmode}"


def get_conn():
    """Get PostgreSQL connection.
    
    Returns:
        psycopg connection object
    """
    return psycopg.connect(get_db_url())

