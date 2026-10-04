# shared/models/checkpoint_model.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, func
from .base import Base


class ModelCheckpointRecord(Base):
    """
    Stores model weight checkpoints and artifact versioning metadata captured
    dynamically during reinforcement learning training runs.
    """
    __tablename__ = "model_checkpoints"

    id = Column(Integer, primary_key=True, index=True)
    checkpoint_id = Column(String, unique=True, index=True, nullable=False)
    task_id = Column(String, index=True, nullable=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=True)
    batch_id = Column(String, index=True, nullable=True)
    trial_id = Column(String, index=True, nullable=True)

    algo = Column(String, nullable=False)
    env_name = Column(String, nullable=False)
    epoch = Column(Integer, nullable=False)
    step = Column(Integer, default=0, nullable=True)

    reward = Column(Float, nullable=True)
    loss = Column(Float, nullable=True)

    file_path = Column(String, nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    checksum = Column(String, nullable=False)  # SHA-256 integrity hash
    version = Column(String, default="v1.0", nullable=False)
    is_best = Column(Boolean, default=False, nullable=False)

    metadata_json = Column(Text, nullable=True)  # Serialised hyperparameters and layer specs
    created_at = Column(DateTime, default=func.now())
