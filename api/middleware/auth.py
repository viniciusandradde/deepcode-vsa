"""API Key authentication middleware.

Protects all /api/v1/* endpoints with API key validation.
Configure via VSA_API_KEY environment variable.
"""

import os
from fastapi import HTTPException, Security, status, Depends
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
security_bearer = HTTPBearer(auto_error=False)

# Public endpoints that don't require auth
PUBLIC_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}


def get_api_key() -> str | None:
    """Get configured API key from environment."""
    return os.getenv("VSA_API_KEY")


async def verify_api_key(
    api_key: str | None = Security(API_KEY_HEADER),
    auth: HTTPAuthorizationCredentials | None = Depends(security_bearer),
) -> str:
    """Validate API key from X-API-Key header OR Bearer token.

    Returns the validated key or 'jwt-valid', or raises 401/403.
    """
    configured_key = get_api_key()

    # If no key is configured, allow access (development mode)
    if not configured_key:
        return "dev-mode"

    # 1. Check API Key
    if api_key and api_key == configured_key:
        return api_key

    # 2. Check JWT (Bearer token)
    if auth:
        from core.auth import decode_access_token
        payload = decode_access_token(auth.credentials)
        if payload and payload.get("sub"):
            return "jwt-valid"

    if not api_key and not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication. Provide X-API-Key header or Bearer token.",
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid authentication.",
    )
