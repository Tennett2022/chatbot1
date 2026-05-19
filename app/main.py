from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.storage.database import init_db, get_db
from app.routes import health, telegram_webhook, whatsapp_webhook
from app.storage.repositories import LeadRepository, ConversationRepository
from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting Crovenett Chatbot API [{settings.APP_ENV}]")
    init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down Crovenett Chatbot API")


app = FastAPI(
    title="Crovenett Chatbot API",
    description="Chatbot empresarial multicanal con IA para Crovenett",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(telegram_webhook.router, tags=["Telegram"])
app.include_router(whatsapp_webhook.router, tags=["WhatsApp"])


@app.get("/leads", tags=["Admin"])
async def list_leads(db: Session = Depends(get_db)):
    """List all captured leads."""
    repo = LeadRepository(db)
    leads = repo.list_leads()
    return [
        {
            "id": lead.id,
            "user_id": lead.user_id,
            "channel": lead.channel,
            "nombre": lead.nombre,
            "empresa": lead.empresa,
            "email": lead.email,
            "telefono": lead.telefono,
            "servicio_interesado": lead.servicio_interesado,
            "estado": lead.estado,
            "fecha_creacion": lead.fecha_creacion,
        }
        for lead in leads
    ]


@app.get("/conversations/{user_id}", tags=["Admin"])
async def get_conversation(
    user_id: str,
    channel: str = "telegram",
    db: Session = Depends(get_db),
):
    """Get conversation history for a specific user."""
    repo = ConversationRepository(db)
    messages = repo.get_recent_messages(user_id, channel, limit=50)
    return [
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
    ]
