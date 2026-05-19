from fastapi import APIRouter

from app.api.v1 import auth, chat, conversations, health, knowledge, leads

router = APIRouter(prefix="/api/v1")

router.include_router(health.router)
router.include_router(auth.router)
router.include_router(chat.router)
router.include_router(leads.router)
router.include_router(conversations.router)
router.include_router(knowledge.router)
