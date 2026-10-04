# backend/fastapi_app/routers/checkpoints.py
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, status
from fastapi.responses import FileResponse
from pathlib import Path

from backend.fastapi_app.services.checkpoint_service import (
    save_model_checkpoint,
    load_model_checkpoint,
    get_checkpoint_detail,
    list_checkpoints as query_checkpoints,
    get_best_checkpoint as query_best_checkpoint,
)
from backend.fastapi_app.services.orchestrator import run_training_task
from shared.schemas.checkpoint_schema import (
    CheckpointCreateRequest,
    CheckpointDetailResponse,
    CheckpointListResponse,
    CheckpointResumeRequest,
    CheckpointResumeResponse,
)
from shared.utils.logger import get_logger

log = get_logger("CheckpointsRouter")

router = APIRouter(prefix="/checkpoints", tags=["Model Checkpoints & Artifact Versioning"])


@router.post("", response_model=CheckpointDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_checkpoint(payload: CheckpointCreateRequest):
    """
    Manually save or register a model checkpoint artifact with neural network
    layer weights, metadata, and calculated SHA-256 integrity hash.
    """
    log.info(f"Registering checkpoint for {payload.algo} on {payload.env_name} at epoch {payload.epoch}")
    try:
        data = save_model_checkpoint(
            algo=payload.algo,
            env_name=payload.env_name,
            epoch=payload.epoch,
            task_id=payload.task_id,
            experiment_id=payload.experiment_id,
            batch_id=payload.batch_id,
            trial_id=payload.trial_id,
            step=payload.step,
            reward=payload.reward,
            loss=payload.loss,
            version=payload.version,
            weights_dict=payload.weights,
            hyperparameters=payload.hyperparameters,
        )
        return CheckpointDetailResponse(**data)
    except Exception as exc:
        log.error(f"Failed to create model checkpoint: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkpoint: {str(exc)}"
        )


@router.get("", response_model=CheckpointListResponse)
async def list_model_checkpoints(
    task_id: Optional[str] = Query(None, description="Filter by Celery task ID"),
    experiment_id: Optional[int] = Query(None, description="Filter by experiment ID"),
    algo: Optional[str] = Query(None, description="Filter by RL algorithm"),
    env_name: Optional[str] = Query(None, description="Filter by simulation environment"),
    is_best: Optional[bool] = Query(None, description="Filter only highest-performing checkpoints"),
    limit: int = Query(20, ge=1, le=100, description="Pagination page limit"),
    offset: int = Query(0, ge=0, description="Pagination record offset"),
):
    """
    Retrieve paginated collection of saved model checkpoints and artifact versions.
    """
    data = query_checkpoints(
        task_id=task_id,
        experiment_id=experiment_id,
        algo=algo,
        env_name=env_name,
        is_best=is_best,
        limit=limit,
        offset=offset,
    )
    return CheckpointListResponse(
        total=data["total"],
        checkpoints=[CheckpointDetailResponse(**c) for c in data["checkpoints"]]
    )


@router.get("/best", response_model=CheckpointDetailResponse)
async def get_best_model_checkpoint(
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    experiment_id: Optional[int] = Query(None, description="Filter by experiment ID"),
    env_name: Optional[str] = Query(None, description="Filter by environment"),
    algo: Optional[str] = Query(None, description="Filter by algorithm"),
):
    """
    Retrieve top-performing model checkpoint based on highest recorded reward.
    """
    data = query_best_checkpoint(
        task_id=task_id,
        experiment_id=experiment_id,
        env_name=env_name,
        algo=algo,
    )
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No matching checkpoint found for provided criteria."
        )
    return CheckpointDetailResponse(**data)


@router.get("/{checkpoint_id}", response_model=CheckpointDetailResponse)
async def get_checkpoint_by_id(checkpoint_id: str):
    """
    Retrieve metadata and integrity verification details for a specific checkpoint.
    """
    data = get_checkpoint_detail(checkpoint_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint '{checkpoint_id}' not found."
        )
    return CheckpointDetailResponse(**data)


@router.get("/{checkpoint_id}/weights")
async def get_checkpoint_weights(checkpoint_id: str):
    """
    Load and return the deserialised policy state dictionary and neural weights
    after verifying SHA-256 artifact integrity.
    """
    try:
        data = load_model_checkpoint(checkpoint_id, verify_checksum=True)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint artifact file not found on disk for '{checkpoint_id}'."
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(val_err)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load checkpoint: {str(exc)}"
        )

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint '{checkpoint_id}' not found."
        )

    return {
        "checkpoint_id": data["checkpoint_id"],
        "algo": data["algo"],
        "env_name": data["env_name"],
        "epoch": data["epoch"],
        "checksum": data["checksum"],
        "metadata": data["metadata"],
        "state_dict": data["state_dict"],
    }


@router.get("/{checkpoint_id}/download")
async def download_checkpoint_artifact(checkpoint_id: str):
    """
    Download the raw versioned weights file artifact from storage.
    """
    data = get_checkpoint_detail(checkpoint_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint '{checkpoint_id}' not found."
        )

    file_path = Path(data["file_path"])
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checkpoint file artifact missing from storage."
        )

    return FileResponse(
        path=str(file_path),
        filename=f"{checkpoint_id}_{data['version']}.pt",
        media_type="application/octet-stream"
    )


@router.post("/{checkpoint_id}/resume", response_model=CheckpointResumeResponse)
async def resume_training_from_checkpoint(checkpoint_id: str, payload: CheckpointResumeRequest):
    """
    Dynamically resume a reinforcement learning training process from a saved
    checkpoint, continuing policy optimisation from the restored epoch state.
    """
    data = get_checkpoint_detail(checkpoint_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint '{checkpoint_id}' not found."
        )

    start_epoch = data["epoch"]
    target_epochs = start_epoch + payload.resume_epochs
    experiment_id = data.get("experiment_id") or 1

    log.info(
        f"Resuming training from checkpoint {checkpoint_id} (epoch={start_epoch}) "
        f"for {payload.resume_epochs} additional epochs"
    )

    # Dispatch asynchronous Celery task with restored parameters
    async_task = run_training_task.apply_async(
        args=[
            experiment_id,
            data["env_name"],
            data["algo"],
            checkpoint_id,
            payload.resume_epochs,
        ]
    )

    return CheckpointResumeResponse(
        task_id=async_task.id,
        checkpoint_id=checkpoint_id,
        algo=data["algo"],
        env_name=data["env_name"],
        start_epoch=start_epoch,
        target_epochs=target_epochs,
        status="QUEUED",
    )
