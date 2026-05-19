from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

from app.config import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(_api_key_header)) -> str:
    """
    Validate the X-API-Key header for backend-to-backend integrations.
    API_KEY must be set in .env — never hardcoded.
    """
    if not settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key authentication is not configured on this server.",
        )
    if not api_key or api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key
