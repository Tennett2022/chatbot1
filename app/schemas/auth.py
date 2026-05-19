from typing import Optional
from pydantic import BaseModel


class TelegramLoginData(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str


class UserOut(BaseModel):
    id: str
    telegram_id: str
    name: str
    username: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
