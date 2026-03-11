"""Health check endpoint for Kubernetes probes."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for liveness/readiness probes."""
    return {"status": "ok"}
