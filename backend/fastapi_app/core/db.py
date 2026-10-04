# backend/fastapi_app/core/db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.fastapi_app.core.config import settings
from shared.models.base import Base
import shared.models  # Register Experiment, Environment, BenchmarkRecord, ModelMetadata, TrainingRunRecord

# Load database configuration
DATABASE_URL = settings.database.url or os.getenv("DATABASE_URL", "sqlite:///./resimhub.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables. Called on application startup."""
    import shared.models
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency to yield database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
