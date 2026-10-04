# backend/fastapi_app/dependencies/db.py
from backend.fastapi_app.core.db import engine, SessionLocal, get_db

__all__ = ["engine", "SessionLocal", "get_db"]
