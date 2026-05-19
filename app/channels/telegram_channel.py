import httpx
from datetime import datetime
from typing import Optional

from app.channels.base_channel import BaseChannel
from app.config import settings
from app.schemas.message import IncomingMessage, OutgoingMessage
from app.utils.logger import get_logger
from app.utils.text import chunk_text

logger = get_logger(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{{}}/{{method}}"
# Telegram hard limit per message
TELEGRAM_MAX_CHARS = 4096


def _api_url(method: str) -> str:
    return f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/{method}"


class TelegramChannel(BaseChannel):
    """
    Telegram Bot API channel.

    Features:
    - Normalizes /start and /help commands to natural-language greetings.
    - Automatically chunks responses longer than 4096 chars into multiple messages.
    - Falls back to plain text if Markdown parsing fails.
    - Logs send failures with full context.
    """

    def get_channel_name(self) -> str:
        return "telegram"

    async def parse_incoming(self, raw_payload: dict) -> Optional[IncomingMessage]:
        """
        Extract and normalize a text message from a Telegram webhook update.
        Returns None for non-text updates (photos, stickers, etc.) or empty payloads.
        """
        try:
            message = raw_payload.get("message") or raw_payload.get("edited_message")
            if not message:
                return None  # e.g., channel posts, inline queries

            text: str = message.get("text", "").strip()
            if not text:
                logger.debug(
                    f"telegram: non-text update ignored "
                    f"(has_photo={bool(message.get('photo'))}, "
                    f"has_sticker={bool(message.get('sticker'))})"
                )
                return None

            # Normalize bot commands
            if text.startswith("/start"):
                text = "Hola"
            elif text.startswith("/help"):
                text = "¿Qué pueden hacer por mí?"
            elif text.startswith("/"):
                # Unknown command — ignore silently
                return None

            user = message.get("from", {})
            user_id = str(user.get("id", ""))
            if not user_id:
                logger.warning("telegram: message without from.id, skipping")
                return None

            # Build readable display name for logs
            display = " ".join(filter(None, [
                user.get("first_name", ""),
                user.get("last_name", ""),
            ])) or f"user_{user_id}"

            timestamp = message.get("date")
            dt = datetime.utcfromtimestamp(timestamp) if timestamp else datetime.utcnow()

            logger.info(
                f"telegram: incoming user={user_id} name='{display}' "
                f"text_len={len(text)} msg_id={message.get('message_id')}"
            )

            return IncomingMessage(
                user_id=user_id,
                channel="telegram",
                text=text,
                raw_payload=raw_payload,
                timestamp=dt,
            )

        except Exception as exc:
            logger.error(f"telegram: parse error — {exc!r}", exc_info=True)
            return None

    async def send_message(self, message: OutgoingMessage) -> bool:
        """
        Send a message to a Telegram user.
        Automatically splits responses longer than 4096 chars into multiple messages.
        Falls back from Markdown to plain text on parse errors.
        """
        chunks = chunk_text(message.text, max_len=TELEGRAM_MAX_CHARS)
        all_ok = True

        for i, chunk in enumerate(chunks):
            ok = await self._send_chunk(message.user_id, chunk, parse_mode="Markdown")
            if not ok:
                logger.error(
                    f"telegram: failed to deliver chunk {i + 1}/{len(chunks)} "
                    f"to user={message.user_id}"
                )
                all_ok = False

        return all_ok

    async def _send_chunk(
        self, chat_id: str, text: str, parse_mode: Optional[str] = "Markdown"
    ) -> bool:
        """Send one chunk. Retries once without Markdown if a parse error occurs."""
        payload = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(_api_url("sendMessage"), json=payload)

            if resp.status_code == 200:
                return True

            data = resp.json()
            # Telegram returns 400 for Markdown parse errors — retry as plain text
            if resp.status_code == 400 and parse_mode:
                logger.warning(
                    f"telegram: Markdown parse error for user={chat_id}, retrying as plain text. "
                    f"API response: {data.get('description', '')}"
                )
                return await self._send_chunk(chat_id, text, parse_mode=None)

            logger.error(
                f"telegram: sendMessage failed status={resp.status_code} "
                f"user={chat_id} desc='{data.get('description', '')}'"
            )
            return False

        except httpx.TimeoutException:
            logger.error(f"telegram: sendMessage timeout for user={chat_id}")
            return False
        except Exception as exc:
            logger.error(f"telegram: sendMessage error — {exc!r}", exc_info=True)
            return False

    async def send_typing_action(self, chat_id: str) -> None:
        """Send a 'typing...' indicator while the bot generates its response."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    _api_url("sendChatAction"),
                    json={"chat_id": chat_id, "action": "typing"},
                )
        except Exception:
            pass  # Typing indicator is cosmetic — never fail on it

    async def set_webhook(self, webhook_url: str) -> bool:
        """Register a webhook URL with Telegram."""
        payload: dict = {"url": webhook_url}
        if settings.TELEGRAM_WEBHOOK_SECRET:
            payload["secret_token"] = settings.TELEGRAM_WEBHOOK_SECRET
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(_api_url("setWebhook"), json=payload)
            data = resp.json()
            if data.get("ok"):
                logger.info(f"telegram: webhook registered → {webhook_url}")
                return True
            logger.error(f"telegram: setWebhook failed: {data.get('description', data)}")
            return False
        except Exception as exc:
            logger.error(f"telegram: setWebhook error — {exc!r}", exc_info=True)
            return False

    async def delete_webhook(self) -> bool:
        """Remove the registered webhook (switches bot to polling mode)."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(_api_url("deleteWebhook"))
            return resp.json().get("ok", False)
        except Exception as exc:
            logger.error(f"telegram: deleteWebhook error — {exc!r}", exc_info=True)
            return False
