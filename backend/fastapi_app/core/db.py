# backend/fastapi_app/core/db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.fastapi_app.core.config import settings,Settings ,  SecurityConfig, SettingsConfigDict, SystemConfig, BaseSettings

# Default to SQLite for local testing; override with DATABASE_URL in .env or system env
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./resimhub.db")

# For PostgreSQL, use: postgresql+psycopg2://user:password@localhost/dbname
engine = create_engine(
    DATABASE_URL,
    # Uncomment for optional PostgreSQL pool settings
    # pool_pre_ping=True,
    # pool_size=5,
    # max_overflow=10,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    """Initialize database tables. Should be called at startup."""
    import backend.fastapi_app.models  # Ensure models are imported
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
