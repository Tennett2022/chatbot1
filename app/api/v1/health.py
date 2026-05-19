from fastapi import APIRouter
from app.config import settings

router = APIRouter()


@router.get("/health", tags=["Health"], summary="Health check")
async def health():
    """Verify the API is running. No authentication required."""
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.API_VERSION,
        "env": settings.APP_ENV,
    }
