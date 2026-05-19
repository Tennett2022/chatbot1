from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""

    # WhatsApp
    WHATSAPP_PROVIDER: str = ""  # meta | twilio | evolution | wati | zapi
    WHATSAPP_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_VERIFY_TOKEN: str = ""

    # LLM
    LLM_PROVIDER: str = "openai"  # openai | anthropic | gemini
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-haiku-20241022"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # Database
    DATABASE_URL: str = "sqlite:///./crovenett_chatbot.db"

    # Business
    ESCALATION_EMAIL: str = "contacto@crovenett.cl"
    ESCALATION_PHONE: str = "+56 9 XXXX XXXX"
    MAX_HISTORY_MESSAGES: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
