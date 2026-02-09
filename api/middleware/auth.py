"""API Key authentication middleware.

Protects all /api/v1/* endpoints with API key validation.
Configure via VSA_API_KEY environment variable.
"""

import os
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, APIKeyQuery

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
API_KEY_QUERY = APIKeyQuery(name="api_key", auto_error=False)

# Public endpoints that don't require auth
PUBLIC_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}


def get_api_key() -> str | None:
    """Get configured API key from environment."""
    return os.getenv("VSA_API_KEY")


async def verify_api_key(
    api_key_header: str | None = Security(API_KEY_HEADER),
    api_key_query: str | None = Security(API_KEY_QUERY),
) -> str:
    """Validate API key from request header or query parameter.

    Returns the validated key, or raises 401/403.
    """
    api_key = api_key_header or api_key_query
    configured_key = get_api_key()

    # If no key is configured, allow access (development mode)
    if not configured_key:
        return "dev-mode"

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide X-API-Key header.",
        )

    if api_key != configured_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )

    return api_key
