import httpx
from typing import Optional
from app.channels.base_channel import BaseChannel
from app.schemas.message import IncomingMessage, OutgoingMessage
from app.config import settings
from app.utils.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org/bot"


class TelegramChannel(BaseChannel):
    """Telegram Bot API channel implementation."""

    def get_channel_name(self) -> str:
        return "telegram"

    async def parse_incoming(self, raw_payload: dict) -> Optional[IncomingMessage]:
        """Extract message data from Telegram webhook payload."""
        try:
            message = raw_payload.get("message") or raw_payload.get("edited_message")
            if not message:
                logger.debug("Telegram payload has no 'message' field, skipping")
                return None

            text = message.get("text", "").strip()
            if not text:
                logger.debug("Telegram message has no text, skipping")
                return None

            # Handle commands like /start
            if text.startswith("/start"):
                text = "Hola"

            user = message.get("from", {})
            user_id = str(user.get("id", ""))
            if not user_id:
                return None

            timestamp = message.get("date")
            dt = datetime.utcfromtimestamp(timestamp) if timestamp else datetime.utcnow()

            return IncomingMessage(
                user_id=user_id,
                channel="telegram",
                text=text,
                raw_payload=raw_payload,
                timestamp=dt,
            )
        except Exception as e:
            logger.error(f"Error parsing Telegram payload: {e}")
            return None

    async def send_message(self, message: OutgoingMessage) -> bool:
        """Send a text message via Telegram Bot API."""
        url = f"{TELEGRAM_API_BASE}{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": message.user_id,
            "text": message.text,
            "parse_mode": "Markdown",
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                logger.info(f"Message sent to Telegram user {message.user_id}")
                return True
        except httpx.HTTPStatusError as e:
            logger.error(f"Telegram API error {e.response.status_code}: {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False

    async def set_webhook(self, webhook_url: str) -> bool:
        """Register webhook URL with Telegram."""
        url = f"{TELEGRAM_API_BASE}{settings.TELEGRAM_BOT_TOKEN}/setWebhook"
        payload = {"url": webhook_url}
        if settings.TELEGRAM_WEBHOOK_SECRET:
            payload["secret_token"] = settings.TELEGRAM_WEBHOOK_SECRET
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                data = response.json()
                if data.get("ok"):
                    logger.info(f"Telegram webhook set to: {webhook_url}")
                    return True
                else:
                    logger.error(f"Failed to set webhook: {data}")
                    return False
        except Exception as e:
            logger.error(f"Error setting Telegram webhook: {e}")
            return False
