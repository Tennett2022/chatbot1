"""
WhatsApp Webhook Route

This route handles incoming WhatsApp messages.
The implementation is provider-agnostic; configure WHATSAPP_PROVIDER in .env.

To activate:
1. Set WHATSAPP_PROVIDER, WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID in .env
2. Implement your provider in app/channels/whatsapp_channel.py
3. Register this webhook URL in your WhatsApp provider dashboard

For Meta WhatsApp Cloud API:
- Go to developers.facebook.com → your app → WhatsApp → Configuration
- Set Webhook URL to: https://your-domain.com/webhook/whatsapp
- Set Verify Token to the value of WHATSAPP_VERIFY_TOKEN
"""

from fastapi import APIRouter, Request, HTTPException, Query, Depends
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.channels.whatsapp_channel import WhatsAppChannel
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
channel = WhatsAppChannel()


@router.get("/webhook/whatsapp")
async def whatsapp_verify(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
):
    """Meta WhatsApp Cloud API webhook verification handshake."""
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified successfully")
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """Receive and process WhatsApp webhook messages."""
    if not settings.WHATSAPP_PROVIDER:
        logger.warning("WHATSAPP_PROVIDER not configured. Ignoring message.")
        return {"ok": True}

    payload = await request.json()
    logger.debug(f"WhatsApp webhook received from provider: {settings.WHATSAPP_PROVIDER}")

    incoming = await channel.parse_incoming(payload)
    if not incoming:
        logger.debug("WhatsApp payload ignored (not a valid text message)")
        return {"ok": True}

    conv_repo = ConversationRepository(db)
    lead_repo = LeadRepository(db)
    event_repo = EventLogRepository(db)

    history_records = conv_repo.get_recent_messages(
        incoming.user_id, "whatsapp", limit=settings.MAX_HISTORY_MESSAGES
    )
    history = [
        {"message_in": m.message_in, "message_out": m.message_out}
        for m in reversed(history_records)
    ]
    message_count = len(history_records)

    existing_lead = lead_repo.get_lead(incoming.user_id, "whatsapp")
    lead_data = {}
    if existing_lead:
        lead_data = {
            "nombre": existing_lead.nombre,
            "empresa": existing_lead.empresa,
            "email": existing_lead.email,
            "telefono": existing_lead.telefono,
            "rubro": existing_lead.rubro,
            "servicio_interesado": existing_lead.servicio_interesado,
            "urgencia": existing_lead.urgencia,
        }

    try:
        engine_response = await process_message(
            user_message=incoming.text,
            user_id=incoming.user_id,
            channel="whatsapp",
            history=history,
            lead_data=lead_data,
            message_count=message_count,
        )
    except Exception as e:
        logger.error(f"Engine error for WhatsApp user {incoming.user_id}: {e}")
        return {"ok": True}

    record = MessageRecord(
        user_id=incoming.user_id,
        channel="whatsapp",
        message_in=incoming.text,
        message_out=engine_response.response,
        intent=engine_response.intent,
        confidence=engine_response.confidence,
        escalated=engine_response.should_escalate,
        timestamp=datetime.utcnow(),
    )
    conv_repo.save_message(record)

    if engine_response.lead_data:
        lead_fields = {
            k: v for k, v in engine_response.lead_data.items()
            if k in LeadData.model_fields and k not in ("user_id", "channel", "mensaje_original")
        }
        lead_schema = LeadData(
            user_id=incoming.user_id,
            channel="whatsapp",
            mensaje_original=incoming.text,
            **lead_fields,
        )
        lead_repo.create_or_update_lead(lead_schema)

    if engine_response.should_escalate:
        event_repo.log(
            event_type="escalation",
            user_id=incoming.user_id,
            channel="whatsapp",
            description="User escalated to human agent",
            payload={"intent": engine_response.intent},
        )

    outgoing = OutgoingMessage(
        user_id=incoming.user_id,
        channel="whatsapp",
        text=engine_response.response,
    )
    await channel.send_message(outgoing)

    return {"ok": True}
