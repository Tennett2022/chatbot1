from fastapi import APIRouter, HTTPException, status

from app.auth.jwt_handler import create_access_token
from app.auth.telegram_login import verify_telegram_login_widget
from app.schemas.auth import TelegramLoginData, TokenResponse, UserOut

router = APIRouter()


@router.post(
    "/auth/telegram/verify",
    response_model=TokenResponse,
    tags=["Auth"],
    summary="Telegram Login Widget verification",
)
async def telegram_verify(data: TelegramLoginData):
    """
    Verify Telegram Login Widget data and issue a Crovenett JWT.

    Use this when a user authenticates via Telegram Login Widget on a web
    frontend or panel. Returns an access_token valid for JWT_EXPIRE_MINUTES.

    The verification uses TELEGRAM_BOT_TOKEN to validate the hash — this
    is separate from the bot webhook; it does not affect bot operation.
    """
    payload = data.model_dump()

    if not verify_telegram_login_widget(payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Verificación de Telegram fallida. Hash inválido o datos expirados.",
        )

    telegram_id = str(data.id)
    name = " ".join(filter(None, [data.first_name, data.last_name or ""]))

    token = create_access_token(
        {
            "sub": telegram_id,
            "telegram_id": telegram_id,
            "name": name,
            "username": data.username,
            "role": "public_client",
        }
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserOut(
            id=telegram_id,
            telegram_id=telegram_id,
            name=name,
            username=data.username,
        ),
    )
