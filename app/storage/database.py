from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.storage.models import Base
from app.config import settings

# Create engine - supports SQLite and PostgreSQL via DATABASE_URL
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=(settings.APP_ENV == "development"),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Dependency for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
