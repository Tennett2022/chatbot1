"""
Crovenett Chatbot — API-first entry point.

Architecture:
  External systems (web / mobile / Telegram / WhatsApp / backend)
      ↓
  FastAPI  (CORS · rate limiting · auth · Swagger/OpenAPI)
      ↓
  app/api/v1/   — REST API for any frontend or backend
  app/webhooks/ — Telegram & WhatsApp channel adapters
      ↓
  app/core/chatbot_engine.py  — single engine for all channels
      ↓
  Knowledge base → LLM provider → Storage (conversations · leads · logs)
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import router as api_v1_router
from app.config import settings
from app.storage.database import init_db
from app.utils.logger import get_logger
from app.utils.rate_limiter import limiter
from app.webhooks import telegram_webhook, whatsapp_webhook

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.API_VERSION} [{settings.APP_ENV}]")
    init_db()
    logger.info("Database initialized")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Motor conversacional de Crovenett. "
        "Responde únicamente información relacionada con Crovenett y sus servicios. "
        "Llamable desde cualquier frontend, backend o canal de mensajería."
    ),
    version=settings.API_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── Rate limiting ──────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
# REST API — primary interface for all external systems
app.include_router(api_v1_router)

# Channel adapters — Telegram bot & WhatsApp webhooks
app.include_router(telegram_webhook.router, tags=["Telegram"])
app.include_router(whatsapp_webhook.router, tags=["WhatsApp"])


# ── Root redirect to docs ──────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.API_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
        "chat": "POST /api/v1/chat/message",
    }
