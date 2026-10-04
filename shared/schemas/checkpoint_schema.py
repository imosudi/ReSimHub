# shared/schemas/checkpoint_schema.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class CheckpointCreateRequest(BaseModel):
    """Payload to manually register or save an RL model weight checkpoint."""
    algo: str = Field(..., description="RL algorithm name, e.g. DQN, PPO, SAC, A2C")
    env_name: str = Field(..., description="Target simulation environment, e.g. CartPole-v1")
    epoch: int = Field(..., ge=1, description="Training epoch number for this checkpoint")
    task_id: Optional[str] = Field(None, description="Optional associated Celery task identifier")
    experiment_id: Optional[int] = Field(None, description="Optional associated experiment identifier")
    batch_id: Optional[str] = Field(None, description="Optional multi-agent batch identifier")
    trial_id: Optional[str] = Field(None, description="Optional multi-agent trial identifier")
    step: Optional[int] = Field(0, description="Cumulative simulation environment steps")
    reward: Optional[float] = Field(None, description="Achieved reward score at this checkpoint")
    loss: Optional[float] = Field(None, description="Training loss at this checkpoint")
    version: Optional[str] = Field("v1.0", description="Artifact version tag, e.g. v1.0 or epoch_3")
    weights: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Serialisable neural network weights or state dictionary"
    )
    hyperparameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Active hyperparameters and training configuration"
    )


class CheckpointDetailResponse(BaseModel):
    """Detailed metadata and verification snapshot for a model checkpoint."""
    checkpoint_id: str
    task_id: Optional[str] = None
    experiment_id: Optional[int] = None
    batch_id: Optional[str] = None
    trial_id: Optional[str] = None
    algo: str
    env_name: str
    epoch: int
    step: Optional[int] = 0
    reward: Optional[float] = None
    loss: Optional[float] = None
    file_path: str
    file_size_bytes: Optional[int] = None
    checksum: str
    version: str
    is_best: bool
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


class CheckpointListResponse(BaseModel):
    """Paginated collection of model checkpoints and versioned artifacts."""
    total: int
    checkpoints: List[CheckpointDetailResponse]


class CheckpointResumeRequest(BaseModel):
    """Request payload to dynamically resume training from a saved checkpoint."""
    resume_epochs: int = Field(
        5,
        ge=1,
        le=100,
        description="Additional training epochs to execute from restored checkpoint state"
    )
    override_hyperparameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional hyperparameter overrides for continued training"
    )


class CheckpointResumeResponse(BaseModel):
    """Response returned upon resuming a training session from a checkpoint."""
    task_id: str
    checkpoint_id: str
    algo: str
    env_name: str
    start_epoch: int
    target_epochs: int
    status: str
    resumed_at: datetime = Field(default_factory=datetime.utcnow)
