from typing import Optional

from app.channels.base_channel import BaseChannel
from app.schemas.message import IncomingMessage, OutgoingMessage


class WebChannel(BaseChannel):
    """
    Web / REST API channel adapter.

    Messages arrive via POST /api/v1/chat/message and responses are returned
    directly in the HTTP response body — no external HTTP calls needed here.
    parse_incoming() and send_message() are no-ops for this channel.
    """

    def get_channel_name(self) -> str:
        return "web"

    async def parse_incoming(self, raw_payload: dict) -> Optional[IncomingMessage]:
        return None  # REST API endpoint handles parsing directly

    async def send_message(self, message: OutgoingMessage) -> bool:
        return True  # Response is returned in the HTTP response, not pushed
