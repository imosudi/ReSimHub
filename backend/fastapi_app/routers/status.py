from fastapi import APIRouter
from backend.fastapi_app.services.orchestrator import celery_app

router = APIRouter(prefix="/status", tags=["Task Status"])

@router.get("/{task_id}")
async def get_status(task_id: str):
    task_result = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "state": task_result.state,
        "result": task_result.result
    }
