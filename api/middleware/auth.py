"""API Key authentication middleware.

Protects all /api/v1/* endpoints with API key validation.
Configure via VSA_API_KEY environment variable.
"""

import os
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Public endpoints that don't require auth
PUBLIC_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}


def get_api_key() -> str | None:
    """Get configured API key from environment."""
    return os.getenv("VSA_API_KEY")


async def verify_api_key(
    api_key: str | None = Security(API_KEY_HEADER),
) -> str:
    """Validate API key from request header.

    Returns the validated key, or raises 401/403.
    """
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
