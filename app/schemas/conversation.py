from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class MessageRecord(BaseModel):
    id: Optional[int] = None
    user_id: str
    channel: str
    message_in: str
    message_out: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    escalated: bool = False
    timestamp: Optional[datetime] = None
    metadata: Optional[dict] = None


class ConversationHistory(BaseModel):
    user_id: str
    channel: str
    messages: List[MessageRecord] = []
