# backend/fastapi_app/routers/benchmark.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional

from backend.fastapi_app.services.benchmark_service import BenchmarkService
from backend.fastapi_app.models.benchmark_model import (
    ModelUploadResponse,
    BenchmarkRunResponse,
    BenchmarkRecentResponse,
    BenchmarkComparisonResponse,
    BenchmarkHistoryResponse,
    ModelDetailResponse,
    APIErrorResponse,
)

router = APIRouter(prefix="/benchmark", tags=["Benchmarking"])


@router.post("/upload_model", response_model=ModelUploadResponse)
async def upload_model(file: UploadFile = File(...)):
    """
    Upload an agent policy model file (.pkl, .pt, .onnx).
    Persists binary to storage and metadata to DB and cache. Returns generated model_id.
    """
    try:
        model_id, meta = BenchmarkService.save_model_file(file)
        return ModelUploadResponse(**meta, status="uploaded")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/run", response_model=BenchmarkRunResponse)
async def run_benchmark(
    model_id: str = Form(...),
    env_name: str = Form(...),
    episodes: int = Form(50)
):
    """
    Run evaluation simulation for a model on a specified environment.
    Computes standard RL metrics (mean, std, median) and advanced metrics
    (Interquartile Mean IQM, Success Rate, CVaR worst 10% tail, Stability Score).
    Persists evaluation record to the database.
    """
    try:
        result = BenchmarkService.run_benchmark_simulation(model_id, env_name, episodes)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/recent", response_model=BenchmarkRecentResponse)
async def list_recent(limit: int = Query(10, ge=1, le=100)):
    """
    Get recent benchmark results across all environments.
    """
    results = BenchmarkService.list_recent_results(limit)
    return {"count": len(results), "results": results}


@router.get("/history", response_model=BenchmarkHistoryResponse)
async def list_history(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    env_name: Optional[str] = Query(None, description="Filter by environment name"),
    model_id: Optional[str] = Query(None, description="Filter by model ID"),
):
    """
    Query historical benchmark records persisted in the database with optional filtering and pagination.
    """
    history = BenchmarkService.list_history(
        limit=limit,
        offset=offset,
        env_name=env_name,
        model_id=model_id,
    )
    return history


@router.get("/model/{model_id}", response_model=ModelDetailResponse, responses={404: {"model": APIErrorResponse}})
async def get_model_details(model_id: str):
    """
    Retrieve metadata, upload details, benchmark counts, and top score for an uploaded model.
    """
    details = BenchmarkService.get_model_details(model_id)
    if not details:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found in database or storage")
    return details


@router.get("/compare", response_model=BenchmarkComparisonResponse, responses={404: {"model": APIErrorResponse}})
async def compare_models(
    model_ids: str = Query(..., description="Comma separated model IDs, e.g. mdl_1,mdl_2"),
    env: Optional[str] = Query(None, description="Optional environment filter")
):
    """
    Compare multiple models across benchmark evaluation runs.
    Returns sorted rankings and metric summaries.
    """
    ids = [mid.strip() for mid in model_ids.split(",") if mid.strip()]
    if not ids:
        raise HTTPException(status_code=400, detail="No model_ids provided")

    comparison = BenchmarkService.compare_models(ids, env_name=env)
    if "error" in comparison:
        return JSONResponse(status_code=404, content={"error": comparison["error"]})
    return comparison