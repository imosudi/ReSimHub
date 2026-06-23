# backend/fastapi_app/routers/benchmark.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import JSONResponse
from backend.fastapi_app.services import benchmark_service
from typing import List, Optional

from backend.fastapi_app.models.benchmark_model import (
    ModelUploadResponse,
    BenchmarkRunResponse,
    BenchmarkRecentResponse,
    BenchmarkComparisonResponse,
    APIErrorResponse
)

router = APIRouter(prefix="/benchmark", tags=["Benchmarking"])

@router.post("/upload_model", response_model=ModelUploadResponse)
async def upload_model(file: UploadFile = File(...)):
    """
    Upload a model file (e.g. .pkl, .pt, .onnx). Returns a generated model_id.
    """
    try:
        model_id, meta = benchmark_service.BenchmarkService.save_model_file(file)
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
    Run evaluation for a model on a specified environment.
    """
    try:
        result = benchmark_service.BenchmarkService.run_benchmark_simulation(model_id, env_name, episodes)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/recent", response_model=BenchmarkRecentResponse)
async def list_recent(limit: int = Query(10, ge=1, le=100)):
    """
    Get recent benchmark results.
    """
    results = benchmark_service.BenchmarkService.list_recent_results(limit)
    return {"count": len(results), "results": results}


@router.get("/compare", response_model=BenchmarkComparisonResponse, responses={404: {"model": APIErrorResponse}})
async def compare_models(model_ids: str = Query(...), env: str = Query(None)):
    """
    Compare multiple models by mean_reward. Provide model_ids as a comma-separated list.
    """
    ids = [mid.strip() for mid in model_ids.split(",") if mid.strip()]
    comparison = benchmark_service.BenchmarkService.compare_models(ids, env_name=env)
    if "error" in comparison:
        return JSONResponse(status_code=404, content={"error": comparison["error"]})
    return comparison