from fastapi import APIRouter, Request, HTTPException, Header, Depends
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.channels.telegram_channel import TelegramChannel
from app.schemas.message import OutgoingMessage
from app.core.chatbot_engine import process_message
from app.storage.database import get_db
from app.storage.repositories import ConversationRepository, LeadRepository, EventLogRepository
from app.schemas.conversation import MessageRecord
from app.schemas.lead import LeadData
from app.config import settings
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)
channel = TelegramChannel()


@router.post("/webhook/telegram")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """Receive and process Telegram webhook messages."""
    # Validate secret token if configured
    if settings.TELEGRAM_WEBHOOK_SECRET:
        if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
            logger.warning("Invalid Telegram webhook secret token")
            raise HTTPException(status_code=403, detail="Invalid secret token")

    payload = await request.json()
    logger.debug(f"Telegram webhook received: {payload}")

    # Parse the incoming message
    incoming = await channel.parse_incoming(payload)
    if not incoming:
        logger.debug("Telegram payload ignored (no valid message)")
        return {"ok": True}

    # Initialize repositories
    conv_repo = ConversationRepository(db)
    lead_repo = LeadRepository(db)
    event_repo = EventLogRepository(db)

    # Get conversation history
    history_records = conv_repo.get_recent_messages(
        incoming.user_id, "telegram", limit=settings.MAX_HISTORY_MESSAGES
    )
    history = [
        {"message_in": m.message_in, "message_out": m.message_out}
        for m in reversed(history_records)
    ]
    message_count = len(history_records)

    # Get existing lead data
    existing_lead = lead_repo.get_lead(incoming.user_id, "telegram")
    lead_data = {}
    if existing_lead:
        lead_data = {
            "nombre": existing_lead.nombre,
            "empresa": existing_lead.empresa,
            "rubro": existing_lead.rubro,
            "email": existing_lead.email,
            "telefono": existing_lead.telefono,
            "canal_preferido": existing_lead.canal_preferido,
            "servicio_interesado": existing_lead.servicio_interesado,
            "urgencia": existing_lead.urgencia,
            "estado": existing_lead.estado,
        }

    # Process through chatbot engine
    try:
        engine_response = await process_message(
            user_message=incoming.text,
            user_id=incoming.user_id,
            channel="telegram",
            history=history,
            lead_data=lead_data,
            message_count=message_count,
        )
    except Exception as e:
        logger.error(f"Engine error for Telegram user {incoming.user_id}: {e}")
        error_msg = OutgoingMessage(
            user_id=incoming.user_id,
            channel="telegram",
            text="Tuve un problema técnico. Por favor intenta nuevamente en un momento.",
        )
        await channel.send_message(error_msg)
        return {"ok": True}

    # Save conversation record
    record = MessageRecord(
        user_id=incoming.user_id,
        channel="telegram",
        message_in=incoming.text,
        message_out=engine_response.response,
        intent=engine_response.intent,
        confidence=engine_response.confidence,
        escalated=engine_response.should_escalate,
        timestamp=datetime.utcnow(),
        metadata=engine_response.metadata,
    )
    conv_repo.save_message(record)

    # Save/update lead data
    if engine_response.lead_data:
        lead_fields = {
            k: v for k, v in engine_response.lead_data.items()
            if k in LeadData.model_fields and k not in ("user_id", "channel", "mensaje_original")
        }
        lead_schema = LeadData(
            user_id=incoming.user_id,
            channel="telegram",
            mensaje_original=incoming.text,
            **lead_fields,
        )
        lead_repo.create_or_update_lead(lead_schema)

    # Log escalation event
    if engine_response.should_escalate:
        event_repo.log(
            event_type="escalation",
            user_id=incoming.user_id,
            channel="telegram",
            description="User escalated to human agent",
            payload={"intent": engine_response.intent},
        )

    # Send response
    outgoing = OutgoingMessage(
        user_id=incoming.user_id,
        channel="telegram",
        text=engine_response.response,
    )
    success = await channel.send_message(outgoing)
    if not success:
        logger.error(f"Failed to send message to Telegram user {incoming.user_id}")

    return {"ok": True}


@router.post("/webhook/telegram/set")
async def set_telegram_webhook(webhook_url: str):
    """Helper endpoint to register the Telegram webhook (dev use only)."""
    if settings.APP_ENV != "development":
        raise HTTPException(status_code=403, detail="Only available in development mode")
    success = await channel.set_webhook(webhook_url)
    return {"success": success, "webhook_url": webhook_url}
