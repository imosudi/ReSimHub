import json
import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from celery.result import AsyncResult
from backend.fastapi_app.services.orchestrator import run_training_task, celery_app
from backend.fastapi_app.services.progress_broadcast import ProgressBroadcastService
from shared.schemas.orchestrator_schema import TaskQueueResponse, TaskStatusResponse, TrainingRequest
from shared.utils.logger import get_logger

router = APIRouter(prefix="/orchestrate", tags=["Orchestration"])
log = get_logger("OrchestratorRouter")

broadcast_service = ProgressBroadcastService()

# Connect the broadcast service to Redis
@router.on_event("startup")
async def startup_event():
    await broadcast_service.connect()


# -----------------------------
# 🧠 Training Orchestration
# -----------------------------
@router.post("/train", response_model=TaskQueueResponse)
async def orchestrate_training(payload: TrainingRequest):
    """
    Queue a new training job asynchronously via Celery.
    """
    log.info(
        f"Queuing training task: experiment={payload.experiment_id}, env={payload.env_name}, algo={payload.algo}"
    )
    task = run_training_task.delay(payload.experiment_id, payload.env_name, payload.algo)
    return TaskQueueResponse(task_id=task.id, status="queued")


# -----------------------------
# 🔍 Check Task Status (API)
# -----------------------------
@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get current status and progress for a given Celery task.
    """
    result = AsyncResult(task_id, app=celery_app)
    response = {"task_id": task_id, "status": result.status}

    if result.status == "PENDING":
        response["progress"] = {"current": 0, "total": 1, "percentage": 0}
        response["result"] = None
    elif result.status == "PROGRESS":
        meta = result.info or {}
        current = meta.get("current", 0)
        total = meta.get("total", 1)
        response["progress"] = {
            "current": current,
            "total": total,
            "percentage": round((current / total) * 100, 2),
        }
        response["result"] = None
    elif result.status == "SUCCESS":
        meta = result.result or {}
        response["progress"] = {
            "current": meta.get("total", 1),
            "total": meta.get("total", 1),
            "percentage": 100,
        }
        response["result"] = meta
    else:
        # FAILURE / RETRY / REVOKED
        response["progress"] = None
        response["result"] = str(result.info)

    log.info(f"Task {task_id} status: {response['status']}")
    return response


# -----------------------------
# 📡 Stream Task Progress (SSE)
# -----------------------------
@router.get("/tasks/stream/{task_id}")
async def stream_task_progress(request: Request, task_id: str):
    """
    Stream live progress updates from Celery through Redis → FastAPI via SSE.
    """
    async def event_stream():
        async for message in broadcast_service.subscribe(task_id):
            if await request.is_disconnected():
                log.info(f"Client disconnected from SSE stream for {task_id}")
                break
            yield f"data: {message}\n\n"
            await asyncio.sleep(0.2)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# -----------------------------
# 📋 Placeholder: List All Tasks
# -----------------------------
@router.get("/tasks")
async def list_all_tasks():
    """
    Placeholder endpoint to list all tasks.
    """

    
    return {"message": "Feature coming soon"}
