# shared/models/training_model.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from .base import Base


class BatchScheduleRecord(Base):
    """
    Tracks multi-agent parallel batch execution schedules across Celery workers.
    """
    __tablename__ = "batch_schedules"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    env_name = Column(String, nullable=False)
    status = Column(String, default="SCHEDULED")  # SCHEDULED, RUNNING, COMPLETED, FAILED, CANCELLED

    total_trials = Column(Integer, default=1)
    completed_trials = Column(Integer, default=0)
    failed_trials = Column(Integer, default=0)
    priority = Column(Integer, default=5)

    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)


class TrainingRunRecord(Base):
    """
    Stores individual RL agent training runs and trial trajectories.
    """
    __tablename__ = "training_runs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True, nullable=False)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=True)
    batch_id = Column(String, index=True, nullable=True)
    trial_id = Column(String, index=True, nullable=True)
    seed = Column(Integer, default=42, nullable=True)

    algo = Column(String, nullable=False)
    env_name = Column(String, nullable=False)
    status = Column(String, default="RUNNING")

    total_epochs = Column(Integer, default=5)
    last_epoch = Column(Integer, default=0)
    last_reward = Column(Float, nullable=True)
    final_accuracy = Column(Float, nullable=True)

    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)

    experiment = relationship("Experiment", backref="runs")
