import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.channels.telegram_channel import TelegramChannel
from app.config import settings
from app.core.chatbot_engine import process_message
from app.schemas.conversation import MessageRecord
from app.schemas.lead import LeadData
from app.schemas.message import OutgoingMessage
from app.storage.database import get_db
from app.storage.repositories import (
    ConversationRepository,
    EventLogRepository,
    LeadRepository,
)
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)
channel = TelegramChannel()

# Lead schema fields we're allowed to set (excludes auto-set keys)
_LEAD_WRITABLE_FIELDS = {
    "nombre", "empresa", "rubro", "cargo", "email", "telefono",
    "canal_preferido", "problema_principal", "servicio_interesado",
    "presupuesto_estimado", "urgencia", "estado",
}

# Reject messages longer than this (spam / attack protection)
_MAX_MESSAGE_LEN = 2000


@router.post("/webhook/telegram", tags=["Telegram"])
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Receive Telegram webhook updates and process them through the chatbot engine.

    Telegram calls this endpoint for every update directed at the bot.
    Returns 200 OK immediately after processing (Telegram retries on non-200).
    """
    t_start = time.perf_counter()

    # ── Secret token validation ────────────────────────────────────────────────
    if settings.TELEGRAM_WEBHOOK_SECRET:
        if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
            logger.warning("telegram_webhook: rejected — invalid secret token")
            raise HTTPException(status_code=403, detail="Invalid secret token")

    # ── Parse JSON body ────────────────────────────────────────────────────────
    try:
        payload = await request.json()
    except Exception as exc:
        logger.warning(f"telegram_webhook: invalid JSON body — {exc!r}")
        # Return 200 to prevent Telegram from retrying a malformed payload
        return JSONResponse({"ok": True, "skipped": "invalid_json"})

    if not isinstance(payload, dict):
        logger.warning("telegram_webhook: payload is not a JSON object")
        return JSONResponse({"ok": True, "skipped": "not_an_object"})

    update_id = payload.get("update_id", "?")
    logger.debug(f"telegram_webhook: update_id={update_id}")

    # ── Parse incoming message ─────────────────────────────────────────────────
    incoming = await channel.parse_incoming(payload)
    if not incoming:
        return JSONResponse({"ok": True})  # non-text update, silently ignored

    # ── Basic input validation ─────────────────────────────────────────────────
    if len(incoming.text) > _MAX_MESSAGE_LEN:
        logger.warning(
            f"telegram_webhook: message too long ({len(incoming.text)} chars) "
            f"from user={incoming.user_id}, truncating"
        )
        incoming.text = incoming.text[:_MAX_MESSAGE_LEN]

    # ── Send typing indicator (cosmetic, non-blocking) ─────────────────────────
    await channel.send_typing_action(incoming.user_id)

    # ── Load conversation context ──────────────────────────────────────────────
    conv_repo = ConversationRepository(db)
    lead_repo = LeadRepository(db)
    event_repo = EventLogRepository(db)

    history_records = conv_repo.get_recent_messages(
        incoming.user_id, "telegram", limit=settings.MAX_HISTORY_MESSAGES
    )
    history = [
        {"message_in": m.message_in, "message_out": m.message_out}
        for m in reversed(history_records)
    ]
    message_count = len(history_records)

    # Hydrate existing lead data
    existing_lead = lead_repo.get_lead(incoming.user_id, "telegram")
    lead_data: dict = {}
    if existing_lead:
        lead_data = {
            f: getattr(existing_lead, f)
            for f in _LEAD_WRITABLE_FIELDS
            if getattr(existing_lead, f, None) is not None
        }

    # ── Engine processing ──────────────────────────────────────────────────────
    try:
        result = await process_message(
            user_message=incoming.text,
            user_id=incoming.user_id,
            channel="telegram",
            history=history,
            lead_data=lead_data,
            message_count=message_count,
        )
    except Exception as exc:
        logger.error(
            f"telegram_webhook: engine error user={incoming.user_id} — {exc!r}",
            exc_info=True,
        )
        fallback_text = (
            "Tuve un inconveniente técnico. "
            "Por favor intenta de nuevo en un momento."
        )
        await channel.send_message(
            OutgoingMessage(user_id=incoming.user_id, channel="telegram", text=fallback_text)
        )
        return JSONResponse({"ok": True})

    # ── Persist conversation ───────────────────────────────────────────────────
    try:
        conv_repo.save_message(
            MessageRecord(
                user_id=incoming.user_id,
                channel="telegram",
                message_in=incoming.text,
                message_out=result.response,
                intent=result.intent,
                confidence=result.confidence,
                escalated=result.should_escalate,
                timestamp=datetime.utcnow(),
                metadata=result.metadata,
            )
        )
    except Exception as exc:
        # Storage failure should not block the response
        logger.error(f"telegram_webhook: conversation save failed — {exc!r}", exc_info=True)

    # ── Persist lead data ──────────────────────────────────────────────────────
    if result.lead_data:
        writable = {
            k: v for k, v in result.lead_data.items()
            if k in _LEAD_WRITABLE_FIELDS and v is not None
        }
        try:
            lead_repo.create_or_update_lead(
                LeadData(
                    user_id=incoming.user_id,
                    channel="telegram",
                    mensaje_original=incoming.text[:500],  # cap original message
                    **writable,
                )
            )
            if result.lead_data.get("email") or result.lead_data.get("telefono"):
                logger.info(
                    f"telegram_webhook: lead updated user={incoming.user_id} "
                    f"fields={list(writable.keys())}"
                )
        except Exception as exc:
            logger.error(f"telegram_webhook: lead save failed — {exc!r}", exc_info=True)

    # ── Log escalation event ───────────────────────────────────────────────────
    if result.should_escalate:
        try:
            event_repo.log(
                event_type="escalation",
                user_id=incoming.user_id,
                channel="telegram",
                description="Conversation escalated to human agent",
                payload={
                    "intent": result.intent,
                    "lead_nombre": result.lead_data.get("nombre"),
                    "lead_empresa": result.lead_data.get("empresa"),
                    "lead_email": result.lead_data.get("email"),
                    "lead_telefono": result.lead_data.get("telefono"),
                },
            )
        except Exception as exc:
            logger.error(f"telegram_webhook: event log failed — {exc!r}", exc_info=True)

    # ── Send reply ─────────────────────────────────────────────────────────────
    sent = await channel.send_message(
        OutgoingMessage(
            user_id=incoming.user_id,
            channel="telegram",
            text=result.response,
        )
    )
    if not sent:
        logger.error(
            f"telegram_webhook: delivery failed to user={incoming.user_id} "
            f"response_len={len(result.response)}"
        )

    elapsed_ms = int((time.perf_counter() - t_start) * 1000)
    logger.info(
        f"telegram_webhook: done update_id={update_id} user={incoming.user_id} "
        f"intent={result.intent} escalated={result.should_escalate} "
        f"total_ms={elapsed_ms}"
    )

    return JSONResponse({"ok": True})


@router.post("/webhook/telegram/set", tags=["Telegram"])
async def set_telegram_webhook(webhook_url: str):
    """
    Register a webhook URL with Telegram (development helper only).
    Disabled when APP_ENV != 'development'.
    """
    if settings.APP_ENV != "development":
        raise HTTPException(status_code=403, detail="Only available in development mode")
    if not webhook_url.startswith("https://"):
        raise HTTPException(status_code=400, detail="Webhook URL must use HTTPS")
    success = await channel.set_webhook(webhook_url)
    return {"success": success, "webhook_url": webhook_url}
