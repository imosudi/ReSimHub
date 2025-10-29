from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from shared.schemas.experiment_schema import ExperimentCreate, ExperimentResponse
from shared.models.experiment_model import Experiment
from backend.fastapi_app.dependencies.db import get_db

router = APIRouter(prefix="/experiments", tags=["Experiments"])

@router.post("/", response_model=ExperimentResponse)
async def create_experiment(payload: ExperimentCreate, db: Session = Depends(get_db)):
    existing = db.query(Experiment).filter(Experiment.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Experiment name already exists")
    experiment = Experiment(name=payload.name, algo=payload.algo)
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return experiment

@router.get("/", response_model=list[ExperimentResponse])
async def list_experiments(db: Session = Depends(get_db)):
    return db.query(Experiment).all()
