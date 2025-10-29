from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.models.base import Base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./resimhub.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialise tables if not present
Base.metadata.create_all(bind=engine)
