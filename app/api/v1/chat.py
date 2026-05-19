from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.permissions import get_current_user
from app.core.chatbot_engine import process_message
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse
from app.schemas.conversation import MessageRecord
from app.schemas.lead import LeadData
from app.storage.database import get_db
from app.storage.repositories import (
    ConversationRepository,
    EventLogRepository,
    LeadRepository,
)
from app.utils.logger import get_logger
from app.utils.rate_limiter import limiter

router = APIRouter()
logger = get_logger(__name__)

_LEAD_WRITABLE_FIELDS = {
    "nombre", "empresa", "rubro", "cargo", "email", "telefono",
    "canal_preferido", "problema_principal", "servicio_interesado",
    "presupuesto_estimado", "urgencia", "estado",
}


@router.post(
    "/chat/message",
    response_model=ChatMessageResponse,
    tags=["Chat"],
    summary="Send a message to the Crovenett chatbot",
)
@limiter.limit("60/minute")
async def chat_message(
    request: Request,  # required by slowapi
    body: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Send a message to the Crovenett chatbot from any channel or frontend.

    Authentication: X-API-Key header (backend) or Bearer JWT token (frontend).

    The engine always returns only Crovenett-related information.
    Off-topic questions are rejected with a redirect response.
    """
    conv_repo = ConversationRepository(db)
    lead_repo = LeadRepository(db)
    event_repo = EventLogRepository(db)

    # Deterministic conversation_id: provided by caller or derived from channel+user
    conversation_id = body.conversation_id or f"{body.channel}:{body.user_id}"

    # Load conversation history
    history_records = conv_repo.get_recent_messages(
        body.user_id, body.channel, limit=10
    )
    history = [
        {"message_in": m.message_in, "message_out": m.message_out}
        for m in reversed(history_records)
    ]
    message_count = len(history_records)

    # Hydrate existing lead data
    existing_lead = lead_repo.get_lead(body.user_id, body.channel)
    lead_data: dict = {}
    if existing_lead:
        lead_data = {
            f: getattr(existing_lead, f)
            for f in _LEAD_WRITABLE_FIELDS
            if getattr(existing_lead, f, None) is not None
        }

    # Seed from request metadata if caller provided contact info
    if body.metadata:
        if body.metadata.email and not lead_data.get("email"):
            lead_data["email"] = body.metadata.email
        if body.metadata.phone and not lead_data.get("telefono"):
            lead_data["telefono"] = body.metadata.phone

    # Process through the central chatbot engine
    try:
        result = await process_message(
            user_message=body.message,
            user_id=body.user_id,
            channel=body.channel,
            history=history,
            lead_data=lead_data,
            message_count=message_count,
        )
    except Exception as exc:
        logger.error(
            f"chat_api: engine error user={body.user_id} channel={body.channel} — {exc!r}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del motor conversacional.",
        )

    # Persist conversation (storage failure must not block the response)
    try:
        conv_repo.save_message(
            MessageRecord(
                user_id=body.user_id,
                channel=body.channel,
                message_in=body.message,
                message_out=result.response,
                intent=result.intent,
                confidence=result.confidence,
                escalated=result.should_escalate,
                timestamp=datetime.utcnow(),
                metadata=result.metadata,
            )
        )
    except Exception as exc:
        logger.error(f"chat_api: conversation save failed — {exc!r}", exc_info=True)

    # Persist lead data
    if result.lead_data:
        writable = {
            k: v for k, v in result.lead_data.items()
            if k in _LEAD_WRITABLE_FIELDS and v is not None
        }
        try:
            lead_repo.create_or_update_lead(
                LeadData(
                    user_id=body.user_id,
                    channel=body.channel,
                    mensaje_original=body.message[:500],
                    **writable,
                )
            )
        except Exception as exc:
            logger.error(f"chat_api: lead save failed — {exc!r}", exc_info=True)

    # Log escalation events
    if result.should_escalate:
        try:
            event_repo.log(
                event_type="escalation",
                user_id=body.user_id,
                channel=body.channel,
                description="Conversation escalated to human agent via REST API",
                payload={"intent": result.intent, **result.lead_data},
            )
        except Exception as exc:
            logger.error(f"chat_api: event log failed — {exc!r}", exc_info=True)

    lead_detected = bool(
        result.lead_data.get("nombre")
        or result.lead_data.get("email")
        or result.lead_data.get("telefono")
    )

    return ChatMessageResponse(
        conversation_id=conversation_id,
        response=result.response,
        intent=result.intent,
        confidence=result.confidence,
        lead_detected=lead_detected,
        lead_data=result.lead_data,
        requires_human=result.should_escalate,
        next_action=result.next_action,
        scope="crovenett_only",
    )
