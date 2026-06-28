# backend/fastapi_app/core/db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.fastapi_app.core.config import settings
from shared.models.base import Base

# Load database configuration
DATABASE_URL = settings.database.url or os.getenv("DATABASE_URL", "sqlite:///./resimhub.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables. Should be called at startup."""
    # Ensure models are imported to register them with metadata
    from shared.models.experiment_model import Experiment, Environment
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
