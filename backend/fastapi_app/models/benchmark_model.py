# backend/fastapi_app/models/benchmark_model.py
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime

# ------------------------------------------------------
# Core Models
# ------------------------------------------------------

class BenchmarkUploadResponse(BaseModel):
    model_id: str
    status: str
    uploaded_at: Optional[datetime]

class BenchmarkResult(BaseModel):
    model_id: str
    env_name: str
    mean_reward: float
    std_reward: float
    median_reward: float
    latency_ms: float
    total_episodes: int
    status: str
    evaluated_at: Optional[datetime]


class ModelUploadResponse(BaseModel):
    model_id: str = Field(..., example="mdl_afdbb795")
    status: str = Field(..., example="uploaded")
    uploaded_at: datetime = Field(..., example="2025-10-30T14:16:26.241943")
    filename: Optional[str] = Field(None, example="dqn_model.pkl")


class BenchmarkRunRequest(BaseModel):
    model_id: str = Field(..., example="mdl_afdbb795")
    env_name: str = Field(..., example="CartPole-v1")
    episodes: int = Field(50, example=50, ge=1, le=1000)


class BenchmarkRunResponse(BaseModel):
    model_id: str = Field(..., example="mdl_afdbb795")
    env_name: str = Field(..., example="CartPole-v1")
    mean_reward: float = Field(..., example=203.68)
    std_reward: float = Field(..., example=34.65)
    median_reward: float = Field(..., example=204.18)
    latency_ms: float = Field(..., example=26.02)
    total_episodes: int = Field(..., example=50)
    status: str = Field(..., example="completed")
    evaluated_at: datetime = Field(..., example="2025-10-30T14:23:19.748328")


class BenchmarkRecentResponse(BaseModel):
    count: int = Field(..., example=2)
    results: List[BenchmarkRunResponse]


# ------------------------------------------------------
# Model Comparison Schemas
# ------------------------------------------------------

class ModelComparisonItem(BaseModel):
    model_id: str = Field(..., example="mdl_afdbb795")
    env_name: str = Field(..., example="CartPole-v1")
    mean_reward: float = Field(..., example=203.68)
    std_reward: float = Field(..., example=34.65)
    median_reward: float = Field(..., example=204.18)
    latency_ms: float = Field(..., example=26.02)
    total_episodes: Optional[int] = Field(None, example=50)
    status: Optional[str] = Field("completed", example="completed")
    evaluated_at: Optional[datetime] = Field(None, example="2025-10-30T14:23:19.748328")


class ComparisonSummary(BaseModel):
    env_name: str = Field(..., example="CartPole-v1")
    metric: str = Field(..., example="mean_reward")
    best_model: str = Field(..., example="mdl_afdbb795")
    best_score: float = Field(..., example=203.68)


class BenchmarkComparisonResponse(BaseModel):
    comparison_summary: ComparisonSummary
    models: List[ModelComparisonItem]


# ------------------------------------------------------
# Generic API Error
# ------------------------------------------------------

class APIErrorResponse(BaseModel):
    error: str = Field(..., example="No benchmark records found for given model_ids")
    error_id: Optional[str] = Field(None, example="2c13cc19-9c5c-47d0-baf9-9dc14fce1f8d")


