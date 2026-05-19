from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Crovenett Chatbot API"
    API_VERSION: str = "v1"
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

    # API Security
    API_KEY: str = ""
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 hours

    # CORS — comma-separated list of allowed origins
    ALLOWED_ORIGINS: str = "http://localhost:3000,https://crovenett.cl,https://www.crovenett.cl"

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


settings = Settings()
