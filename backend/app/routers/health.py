"""Health check router."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
async def healthz():
    """Report that the API process is alive."""
    return {"status": "ok"}


@router.get("/health")
async def health():
    """Report that the API process is alive."""
    return {"status": "ok"}
