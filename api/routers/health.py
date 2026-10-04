"""Health check endpoint for liveness / readiness probes."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Return service health status."""
    return {"status": "healthy"}
