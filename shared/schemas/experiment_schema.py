
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ExperimentCreate(BaseModel):
    name: str = Field(..., description="Unique name of the experiment")
    algo: str = Field(..., description="Reinforcement learning algorithm used")

class ExperimentResponse(BaseModel):
    id: int
    name: str
    algo: str
    status: str
    created_at: datetime

    class Config:
        orm_mode = True


class EnvironmentCreate(BaseModel):
    env_name: str = Field(..., description="Registered environment, e.g., CartPole-v1")
    version: Optional[str] = Field(default="v1", description="Environment version")

class EnvironmentResponse(BaseModel):
    id: int
    env_name: str
    version: str
    registered_at: datetime

    class Config:
        orm_mode = True

