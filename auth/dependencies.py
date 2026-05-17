"""Auth dependencies for protecting FastAPI routes."""

import os
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_bearer = HTTPBearer(auto_error=False)


def _get_expected_api_key() -> str | None:
    """Read API key from environment."""
    return os.getenv("AUTH_API_KEY")


def _extract_provided_key(
    api_key: str | None = Depends(_api_key_header),
    bearer: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str | None:
    """Accept either X-API-Key or Authorization: Bearer <token>."""
    if api_key:
        return api_key
    if bearer and bearer.credentials:
        return bearer.credentials
    return None


def require_auth(provided_key: str | None = Depends(_extract_provided_key)) -> str:
    """Validate API key for protected endpoints.

    If AUTH_API_KEY is not configured, fail closed in production environments.
    """
    expected = _get_expected_api_key()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth is not configured. Set AUTH_API_KEY.",
        )

    if provided_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )

    return provided_key
