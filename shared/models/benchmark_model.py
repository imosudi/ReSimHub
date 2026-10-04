# shared/models/benchmark_model.py
from sqlalchemy import Column, Integer, String, Float, DateTime, func
from .base import Base


class BenchmarkRecord(Base):
    __tablename__ = "benchmark_records"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String, index=True, nullable=False)
    env_name = Column(String, index=True, nullable=False)
    total_episodes = Column(Integer, default=50)

    # Core reward metrics
    mean_reward = Column(Float, nullable=False)
    std_reward = Column(Float, nullable=False)
    median_reward = Column(Float, nullable=False)
    min_reward = Column(Float, nullable=True)
    max_reward = Column(Float, nullable=True)

    # Advanced RL statistical & robustness metrics
    iqm_reward = Column(Float, nullable=True)          # Interquartile Mean (trimmed 25%)
    success_rate = Column(Float, nullable=True)        # % of episodes achieving goal threshold
    cvar_reward = Column(Float, nullable=True)         # Conditional Value-at-Risk (worst 10% episodes)
    stability_score = Column(Float, nullable=True)     # Mean / (Std + eps) signal-to-noise ratio

    # Performance & latency
    latency_ms = Column(Float, nullable=False)
    status = Column(String, default="completed")
    evaluated_at = Column(DateTime, default=func.now())


class ModelMetadata(Base):
    __tablename__ = "model_metadata"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String, unique=True, index=True, nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=func.now())
