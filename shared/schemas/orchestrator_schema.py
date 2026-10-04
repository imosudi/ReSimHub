# shared/schemas/orchestrator_schema.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
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
    batch_id: Optional[str] = None
    trial_id: Optional[str] = None
    seed: Optional[int] = 42
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


# -------------------------------------------------------------
# 🤖 Multi-Agent Batch Scheduling Schemas
# -------------------------------------------------------------

class AgentTrialConfig(BaseModel):
    """Configuration for an individual agent trial within a parallel batch."""
    algo: str = Field(..., description="RL algorithm name, e.g. DQN, PPO, SAC, A2C")
    seed: int = Field(42, description="Random seed for deterministic initialisation")
    total_epochs: int = Field(5, ge=1, le=100, description="Total epochs to execute")
    hyperparameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional hyperparameter overrides, e.g. learning rate or gamma"
    )


class BatchScheduleRequest(BaseModel):
    """Request payload to schedule a parallel batch of agent trials."""
    name: str = Field(..., description="Descriptive batch schedule campaign name")
    env_name: str = Field(..., description="Target simulation environment, e.g. CartPole-v1")
    agents: List[AgentTrialConfig] = Field(
        ...,
        min_length=1,
        description="Collection of agent configurations to execute in parallel"
    )
    priority: int = Field(
        5,
        ge=1,
        le=10,
        description="Queue priority rating (1 is lowest priority, 10 is highest priority)"
    )


class BatchTrialDetail(BaseModel):
    """Detailed runtime snapshot of a single trial inside a multi-agent batch."""
    trial_id: str
    task_id: str
    algo: str
    seed: int
    status: str
    current_epoch: int
    total_epochs: int
    latest_reward: Optional[float] = None
    final_accuracy: Optional[float] = None


class BatchScheduleResponse(BaseModel):
    """Response returned upon accepting and queuing a multi-agent parallel batch."""
    batch_id: str
    name: str
    env_name: str
    status: str
    total_trials: int
    task_ids: List[str]
    scheduled_at: datetime = Field(default_factory=datetime.utcnow)


class BatchStatusResponse(BaseModel):
    """Consolidated status and aggregate metrics of a scheduled multi-agent batch."""
    batch_id: str
    name: str
    env_name: str
    status: str
    total_trials: int
    completed_trials: int
    failed_trials: int
    priority: int = 5
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    trials: List[BatchTrialDetail] = Field(default_factory=list)
    summary_metrics: Optional[Dict[str, Any]] = None


class BatchListResponse(BaseModel):
    """Paginated list of multi-agent batch schedules."""
    total: int
    batches: List[BatchStatusResponse]
