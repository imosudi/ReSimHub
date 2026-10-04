import json
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import StreamingResponse
from celery.result import AsyncResult
from backend.fastapi_app.services.orchestrator import (
    run_training_task,
    celery_app,
    schedule_multi_agent_batch,
    get_batch_status as fetch_batch_status,
    list_batches as fetch_batch_list,
)
from backend.fastapi_app.services.progress_broadcast import get_broadcast_service
from shared.schemas.orchestrator_schema import (
    TaskQueueResponse,
    TaskStatusResponse,
    TrainingRequest,
    TrainingRunListResponse,
    TrainingRunItemResponse,
    BatchScheduleRequest,
    BatchScheduleResponse,
    BatchStatusResponse,
    BatchListResponse,
)
from shared.utils.logger import get_logger

router = APIRouter(prefix="/orchestrate", tags=["Orchestration"])
log = get_logger("OrchestratorRouter")

broadcast_service = get_broadcast_service()


@router.on_event("startup")
async def startup_event():
    await broadcast_service.connect()


# -------------------------------------------------------------
# 🧠 Training Orchestration (Single Agent)
# -------------------------------------------------------------
@router.post("/train", response_model=TaskQueueResponse)
async def orchestrate_training(payload: TrainingRequest):
    """
    Queue a new training job asynchronously via Celery and persist record to DB.
    """
    log.info(
        f"Queuing training task: experiment={payload.experiment_id}, env={payload.env_name}, algo={payload.algo}"
    )
    task = run_training_task.delay(
        payload.experiment_id,
        payload.env_name,
        payload.algo,
        payload.checkpoint_id,
        payload.resume_epochs or 5,
    )

    # Persist initial QUEUED record to database
    try:
        from backend.fastapi_app.core.db import SessionLocal
        from shared.models.training_model import TrainingRunRecord
        db = SessionLocal()
        run_rec = TrainingRunRecord(
            task_id=task.id,
            experiment_id=payload.experiment_id,
            algo=payload.algo,
            env_name=payload.env_name,
            status="QUEUED",
            created_at=datetime.utcnow()
        )
        db.add(run_rec)
        db.commit()
        db.close()
    except Exception as exc:
        log.warning(f"Failed to record queued training run in DB: {exc}")

    return TaskQueueResponse(task_id=task.id, status="queued")


# -------------------------------------------------------------
# 🤖 Multi-Agent Batch Scheduling & Orchestration
# -------------------------------------------------------------
@router.post("/batch", response_model=BatchScheduleResponse)
async def schedule_batch(payload: BatchScheduleRequest):
    """
    Schedule a parallel batch of diverse agent trials across distributed Celery workers.
    Each trial executes concurrently with dedicated seed, algorithm, and hyperparameters.
    """
    log.info(f"Scheduling multi-agent batch '{payload.name}' on {payload.env_name} with {len(payload.agents)} trials")
    try:
        result = schedule_multi_agent_batch(payload)
        return BatchScheduleResponse(**result)
    except Exception as exc:
        log.error(f"Failed to schedule batch: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to schedule batch: {str(exc)}")


@router.get("/batch/{batch_id}", response_model=BatchStatusResponse)
async def get_batch(batch_id: str):
    """
    Retrieve real-time consolidated status, trial progress, and aggregate performance metrics for a batch.
    """
    data = fetch_batch_status(batch_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Batch schedule '{batch_id}' not found.")
    return BatchStatusResponse(**data)


@router.get("/batches", response_model=BatchListResponse)
async def list_all_batches(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List paginated multi-agent batch schedules recorded in the database.
    """
    data = fetch_batch_list(limit=limit, offset=offset)
    return BatchListResponse(
        total=data["total"],
        batches=[BatchStatusResponse(**b) for b in data["batches"]]
    )


# -------------------------------------------------------------
# 🔍 Check Task Status (API)
# -------------------------------------------------------------
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
        response["progress"] = None
        response["result"] = str(result.info)

    log.info(f"Task {task_id} status: {response['status']}")
    return response


# -------------------------------------------------------------
# 📡 Stream Task Progress (SSE)
# -------------------------------------------------------------
@router.get("/tasks/stream/{task_id}")
async def stream_task_progress(request: Request, task_id: str):
    """
    Stream live progress updates from Celery through Redis to FastAPI via SSE.
    """
    async def event_stream():
        async for message in broadcast_service.subscribe(task_id):
            if await request.is_disconnected():
                log.info(f"Client disconnected from SSE stream for {task_id}")
                break
            yield f"data: {message}\n\n"
            await asyncio.sleep(0.2)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# -------------------------------------------------------------
# 📋 List All Tasks
# -------------------------------------------------------------
@router.get("/tasks", response_model=TrainingRunListResponse)
async def list_all_tasks(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None, description="Filter by status (e.g. SUCCESS, RUNNING, QUEUED)"),
    algo: Optional[str] = Query(None, description="Filter by algorithm"),
):
    """
    List historical training runs from the database with pagination and filtering.
    """
    try:
        from backend.fastapi_app.core.db import SessionLocal
        from shared.models.training_model import TrainingRunRecord
        db = SessionLocal()
        query = db.query(TrainingRunRecord)
        if status:
            query = query.filter(TrainingRunRecord.status == status)
        if algo:
            query = query.filter(TrainingRunRecord.algo == algo)

        total = query.count()
        rows = query.order_by(TrainingRunRecord.created_at.desc()).offset(offset).limit(limit).all()
        db.close()
        return TrainingRunListResponse(
            total=total,
            tasks=[TrainingRunItemResponse.model_validate(r) for r in rows]
        )
    except Exception as exc:
        log.warning(f"Error querying training runs: {exc}")
        return TrainingRunListResponse(total=0, tasks=[])
