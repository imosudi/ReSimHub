from fastapi import APIRouter, HTTPException
from backend.fastapi_app.services.orchestrator import run_training_task

router = APIRouter(prefix="/train", tags=["Training"])

@router.post("/{experiment_id}")
async def launch_training(experiment_id: int):
    try:
        task = run_training_task.delay(experiment_id, "DQN")
        return {"task_id": task.id, "status": "queued"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
