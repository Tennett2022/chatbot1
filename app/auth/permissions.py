from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer

from app.auth.jwt_handler import decode_access_token
from app.config import settings

_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    token: Optional[str] = Depends(_oauth2),
    api_key: Optional[str] = Depends(_api_key_header),
) -> dict:
    """
    Accept X-API-Key (backend-to-backend) OR Bearer JWT (frontend / web).
    Returns a user context dict with role and auth_method.
    """
    # API key takes priority — checked first for performance
    if api_key and settings.API_KEY and api_key == settings.API_KEY:
        return {"role": "integration", "auth_method": "api_key", "user_id": None}

    if token:
        payload = decode_access_token(token)
        return {
            "role": payload.get("role", "public_client"),
            "user_id": payload.get("sub"),
            "telegram_id": payload.get("telegram_id"),
            "auth_method": "jwt",
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=(
            "Autenticación requerida. "
            "Incluye el header X-API-Key o un Bearer token en Authorization."
        ),
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Restrict endpoint to admin role only."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de administrador.",
        )
    return current_user
