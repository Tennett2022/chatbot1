from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.permissions import get_current_user
from app.storage.database import get_db
from app.storage.models import Conversation
from app.storage.repositories import ConversationRepository

router = APIRouter()


@router.get(
    "/conversations/{conversation_id}",
    tags=["Conversations"],
    summary="Get conversation history",
)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """
    Return the message history for a conversation.

    conversation_id format: '{channel}:{user_id}' (e.g. 'web:user_abc').
    This is the same value returned by POST /api/v1/chat/message.
    """
    channel, sep, user_id = conversation_id.partition(":")
    if not sep:
        # Fallback: treat the whole thing as user_id on channel 'api'
        user_id, channel = conversation_id, "api"

    repo = ConversationRepository(db)
    messages = repo.get_recent_messages(user_id, channel, limit=50)
    if not messages:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")

    return {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "channel": channel,
        "messages": [
            {
                "id": m.id,
                "message_in": m.message_in,
                "message_out": m.message_out,
                "intent": m.intent,
                "confidence": m.confidence,
                "escalated": m.escalated,
                "timestamp": m.timestamp,
            }
            for m in reversed(messages)
        ],
    }


@router.get(
    "/users/{user_id}/conversations",
    tags=["Conversations"],
    summary="Get all conversations for a user",
)
async def get_user_conversations(
    user_id: str,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Return all conversation sessions associated with a user across all channels."""
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .all()
    )
    return {
        "user_id": user_id,
        "conversations": [
            {
                "conversation_id": f"{c.channel}:{c.user_id}",
                "channel": c.channel,
                "started_at": c.started_at,
                "last_activity": c.last_activity,
                "message_count": c.message_count,
            }
            for c in conversations
        ],
    }
