
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TaskQueueResponse(BaseModel):
    task_id: str
    status: str
    queued_at: datetime = Field(default_factory=datetime.utcnow)



class TaskStatusResponse(BaseModel):
    task_id: str
    status: str


class TrainingRequest(BaseModel):
    experiment_id: int
    env_name: str
    algo: str
