"""Auth utility endpoints."""

from fastapi import APIRouter, Depends
from .dependencies import require_auth

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/health")
def auth_health() -> dict[str, str]:
    """Simple auth module liveness endpoint."""
    return {"status": "ok", "module": "auth"}


@router.get("/verify")
def verify_api_key(_: str = Depends(require_auth)) -> dict[str, str]:
    """Verify that the provided API key is valid."""
    return {"status": "ok", "auth": "valid"}
