# backend/fastapi_app/core/db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.models.base import Base
import shared.models  # Register Experiment, Environment, BenchmarkRecord, ModelMetadata, TrainingRunRecord

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./resimhub.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables. Called on application startup."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency to yield database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
