from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class IncomingMessage(BaseModel):
    user_id: str
    channel: str  # telegram | whatsapp | web
    text: str
    raw_payload: Optional[dict] = None
    timestamp: Optional[datetime] = None


class OutgoingMessage(BaseModel):
    user_id: str
    channel: str
    text: str
    metadata: Optional[dict] = None
