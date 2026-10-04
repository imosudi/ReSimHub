# shared/schemas/orchestrator_schema.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TaskQueueResponse(BaseModel):
    task_id: str
    status: str
    queued_at: datetime = Field(default_factory=datetime.utcnow)


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: Optional[dict] = None
    result: Optional[dict] = None


class TrainingRequest(BaseModel):
    experiment_id: int
    env_name: str
    algo: str


class TrainingRunItemResponse(BaseModel):
    id: Optional[int] = None
    task_id: str
    experiment_id: Optional[int] = None
    algo: str
    env_name: str
    status: str
    total_epochs: int = 5
    last_epoch: int = 0
    last_reward: Optional[float] = None
    final_accuracy: Optional[float] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TrainingRunListResponse(BaseModel):
    total: int
    tasks: List[TrainingRunItemResponse]
