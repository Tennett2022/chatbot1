from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class MessageMetadata(BaseModel):
    source: Optional[str] = None
    user_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class ChatMessageRequest(BaseModel):
    user_id: str = Field(..., description="Identificador único del usuario en el canal")
    channel: str = Field(
        ...,
        description="Canal origen: web | telegram | whatsapp | api | mobile | backend",
        examples=["web"],
    )
    message: str = Field(..., min_length=1, max_length=2000, description="Mensaje del usuario")
    conversation_id: Optional[str] = Field(
        None,
        description="ID de conversación existente. Si se omite se genera automáticamente.",
    )
    metadata: Optional[MessageMetadata] = None


class ChatMessageResponse(BaseModel):
    conversation_id: str
    response: str
    intent: str
    confidence: float
    lead_detected: bool
    lead_data: Dict[str, Any]
    requires_human: bool
    next_action: str
    scope: str = "crovenett_only"
