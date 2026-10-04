# shared/schemas/simulator_schema.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class SimulatorResetRequest(BaseModel):
    """Payload to initialise or reset a simulation environment instance."""
    env_id: str = Field(default="CartPole-v1", description="Identifier of the environment to reset")
    seed: Optional[int] = Field(default=None, description="Optional random seed for deterministic reset")
    options: Optional[Dict[str, str]] = Field(default_factory=dict, description="Additional reset configuration options")


class SimulatorResetResponse(BaseModel):
    """Initial observation and status returned upon resetting an environment."""
    env_id: str
    observation: List[float]
    info: Dict[str, str]
    success: bool


class SimulatorStepRequest(BaseModel):
    """Single transition action request to step the simulation environment."""
    env_id: str = Field(default="CartPole-v1", description="Target environment identifier")
    action: Any = Field(default=0, description="Discrete action integer or continuous action vector")
    is_discrete: bool = Field(default=True, description="Flag indicating if the action space is discrete")
    step_index: int = Field(default=0, description="Sequential step counter or index")


class SimulatorStepResponse(BaseModel):
    """Simulation step outcome containing next observation, reward, and flags."""
    env_id: str
    observation: List[float]
    reward: float
    done: bool
    truncated: bool
    info: Dict[str, str]
    step_count: int
    latency_ms: float


class SimulatorBatchStepRequest(BaseModel):
    """Vectorised batch stepping request containing multiple step actions."""
    batch_id: Optional[str] = Field(default="", description="Identifier for this batch execution")
    steps: List[SimulatorStepRequest] = Field(..., description="Collection of environment step transitions")


class SimulatorBatchStepResponse(BaseModel):
    """Aggregated batch execution results with measured throughput and latency."""
    batch_id: str
    total_steps: int
    elapsed_ms: float
    average_step_latency_ms: float
    responses: List[SimulatorStepResponse]


class SimulatorStreamRequest(BaseModel):
    """Request to execute a continuous observation sequence on the simulator."""
    env_id: str = Field(default="CartPole-v1", description="Environment identifier to stream")
    max_steps: int = Field(default=50, ge=1, le=10000, description="Maximum transition steps to execute")
    seed: Optional[int] = Field(default=None, description="Optional random seed for initialisation")
    policy_type: str = Field(default="heuristic", description="Policy behaviour: heuristic, random, or zero")


class SimulatorStreamResponse(BaseModel):
    """Summary and transition steps collected from observation stream."""
    env_id: str
    total_steps: int
    cumulative_reward: float
    steps: List[SimulatorStepResponse]


class SimulatorBenchmarkRequest(BaseModel):
    """Request to profile simulator throughput across a designated step budget."""
    env_id: str = Field(default="CartPole-v1", description="Environment identifier to benchmark")
    num_steps: int = Field(default=1000, ge=1, le=100000, description="Total transition step budget")
    batch_size: int = Field(default=32, ge=1, le=1000, description="Step chunk size for vectorised evaluation")


class SimulatorBenchmarkResponse(BaseModel):
    """Benchmark performance metrics measuring throughput and step latency."""
    env_id: str
    total_steps: int
    elapsed_seconds: float
    steps_per_second: float
    protocol: str
    mean_latency_ms: float
