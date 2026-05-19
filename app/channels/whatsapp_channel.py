"""
WhatsApp Channel — Architecture stub.

This module defines the WhatsApp channel integration layer.
It is intentionally left as a configurable stub: wire it up by
implementing the methods below for your chosen provider.

Supported providers (set WHATSAPP_PROVIDER in .env):
  - meta      → Meta WhatsApp Cloud API (official)
  - twilio    → Twilio WhatsApp API
  - evolution → Evolution API (self-hosted)
  - wati      → WATI (WhatsApp Team Inbox)
  - zapi      → Z-API (Brazil-focused)

See README.md > "Extendiendo a WhatsApp" for setup instructions.
"""

import httpx
from typing import Optional
from app.channels.base_channel import BaseChannel
from app.schemas.message import IncomingMessage, OutgoingMessage
from app.config import settings
from app.utils.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)


class WhatsAppChannel(BaseChannel):
    """
    WhatsApp channel — supports multiple providers via WHATSAPP_PROVIDER env var.
    """

    def get_channel_name(self) -> str:
        return "whatsapp"

    async def parse_incoming(self, raw_payload: dict) -> Optional[IncomingMessage]:
        """Parse incoming WhatsApp webhook payload (provider-specific)."""
        provider = settings.WHATSAPP_PROVIDER.lower()

        if provider == "meta":
            return self._parse_meta(raw_payload)
        elif provider == "twilio":
            return self._parse_twilio(raw_payload)
        elif provider == "evolution":
            return self._parse_evolution(raw_payload)
        elif provider == "wati":
            return self._parse_wati(raw_payload)
        else:
            logger.warning(f"Unknown WhatsApp provider: '{provider}'. Payload not parsed.")
            return None

    def _parse_meta(self, payload: dict) -> Optional[IncomingMessage]:
        """Parse Meta WhatsApp Cloud API webhook payload."""
        try:
            entry = payload.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [])
            if not messages:
                return None
            msg = messages[0]
            if msg.get("type") != "text":
                return None
            return IncomingMessage(
                user_id=msg.get("from", ""),
                channel="whatsapp",
                text=msg.get("text", {}).get("body", ""),
                raw_payload=payload,
                timestamp=datetime.utcnow(),
            )
        except Exception as e:
            logger.error(f"Error parsing Meta WhatsApp payload: {e}")
            return None

    def _parse_twilio(self, payload: dict) -> Optional[IncomingMessage]:
        """Parse Twilio WhatsApp webhook payload."""
        # Twilio sends form-encoded data; FastAPI should parse it with Form() or as dict
        try:
            from_number = payload.get("From", "").replace("whatsapp:", "")
            body = payload.get("Body", "").strip()
            if not from_number or not body:
                return None
            return IncomingMessage(
                user_id=from_number,
                channel="whatsapp",
                text=body,
                raw_payload=payload,
                timestamp=datetime.utcnow(),
            )
        except Exception as e:
            logger.error(f"Error parsing Twilio WhatsApp payload: {e}")
            return None

    def _parse_evolution(self, payload: dict) -> Optional[IncomingMessage]:
        """Parse Evolution API webhook payload."""
        try:
            data = payload.get("data", {})
            message = data.get("message", {})
            text = message.get("conversation") or message.get("extendedTextMessage", {}).get("text", "")
            sender = data.get("key", {}).get("remoteJid", "").split("@")[0]
            if not sender or not text:
                return None
            return IncomingMessage(
                user_id=sender,
                channel="whatsapp",
                text=text,
                raw_payload=payload,
                timestamp=datetime.utcnow(),
            )
        except Exception as e:
            logger.error(f"Error parsing Evolution API payload: {e}")
            return None

    def _parse_wati(self, payload: dict) -> Optional[IncomingMessage]:
        """Parse WATI webhook payload."""
        try:
            sender = payload.get("waId", "")
            text = payload.get("text", "").strip()
            if not sender or not text:
                return None
            return IncomingMessage(
                user_id=sender,
                channel="whatsapp",
                text=text,
                raw_payload=payload,
                timestamp=datetime.utcnow(),
            )
        except Exception as e:
            logger.error(f"Error parsing WATI payload: {e}")
            return None

    async def send_message(self, message: OutgoingMessage) -> bool:
        """Send a WhatsApp message via the configured provider."""
        provider = settings.WHATSAPP_PROVIDER.lower()

        if provider == "meta":
            return await self._send_meta(message)
        elif provider == "twilio":
            return await self._send_twilio(message)
        elif provider == "evolution":
            return await self._send_evolution(message)
        elif provider == "wati":
            return await self._send_wati(message)
        else:
            logger.warning(f"send_message not implemented for provider: '{provider}'")
            return False

    async def _send_meta(self, message: OutgoingMessage) -> bool:
        """Send via Meta WhatsApp Cloud API."""
        url = f"https://graph.facebook.com/v18.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": message.user_id,
            "type": "text",
            "text": {"body": message.text},
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Meta WhatsApp send error: {e}")
            return False

    async def _send_twilio(self, message: OutgoingMessage) -> bool:
        """Send via Twilio WhatsApp API."""
        try:
            from twilio.rest import Client  # type: ignore
            client = Client(settings.WHATSAPP_TOKEN, settings.WHATSAPP_PHONE_NUMBER_ID)
            client.messages.create(
                from_=f"whatsapp:{settings.WHATSAPP_PHONE_NUMBER_ID}",
                to=f"whatsapp:{message.user_id}",
                body=message.text,
            )
            return True
        except ImportError:
            logger.error("twilio package not installed. Run: pip install twilio")
            return False
        except Exception as e:
            logger.error(f"Twilio send error: {e}")
            return False

    async def _send_evolution(self, message: OutgoingMessage) -> bool:
        """Send via Evolution API."""
        try:
            url = f"{settings.WHATSAPP_TOKEN}/message/sendText/{settings.WHATSAPP_PHONE_NUMBER_ID}"
            payload = {
                "number": message.user_id,
                "options": {"delay": 1200, "presence": "composing"},
                "textMessage": {"text": message.text},
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Evolution API send error: {e}")
            return False

    async def _send_wati(self, message: OutgoingMessage) -> bool:
        """Send via WATI API."""
        try:
            url = f"{settings.WHATSAPP_TOKEN}/api/v1/sendSessionMessage/{message.user_id}"
            headers = {"Authorization": f"Bearer {settings.WHATSAPP_PHONE_NUMBER_ID}"}
            payload = {"messageText": message.text}
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"WATI send error: {e}")
            return False
