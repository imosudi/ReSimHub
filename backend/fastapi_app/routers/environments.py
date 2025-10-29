from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from shared.schemas.experiment_schema import EnvironmentCreate, EnvironmentResponse
from shared.models.experiment_model import Environment
from backend.fastapi_app.dependencies.db import get_db

router = APIRouter(prefix="/environments", tags=["Environments"])

@router.post("/", response_model=EnvironmentResponse)
async def register_environment(payload: EnvironmentCreate, db: Session = Depends(get_db)):
    existing = db.query(Environment).filter(Environment.env_name == payload.env_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Environment already registered")
    env = Environment(env_name=payload.env_name, version=payload.version)
    db.add(env)
    db.commit()
    db.refresh(env)
    return env

@router.get("/", response_model=list[EnvironmentResponse])
async def list_environments(db: Session = Depends(get_db)):
    return db.query(Environment).all()
