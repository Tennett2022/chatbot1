from abc import ABC, abstractmethod
from typing import Optional
from app.schemas.message import IncomingMessage, OutgoingMessage


class BaseChannel(ABC):
    """
    Abstract base class for all messaging channels.
    Any new channel (WhatsApp, Web, etc.) must implement this interface.
    """

    @abstractmethod
    async def parse_incoming(self, raw_payload: dict) -> Optional[IncomingMessage]:
        """
        Parse the raw webhook payload into a normalized IncomingMessage.
        Return None if the payload is not a valid/supported message.
        """
        pass

    @abstractmethod
    async def send_message(self, message: OutgoingMessage) -> bool:
        """
        Send a message to the user through this channel.
        Returns True on success, False on failure.
        """
        pass

    @abstractmethod
    def get_channel_name(self) -> str:
        """Return the canonical name of this channel (e.g., 'telegram', 'whatsapp')."""
        pass
