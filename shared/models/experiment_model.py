from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from .base import Base

class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    algo = Column(String, nullable=False)
    status = Column(String, default="created")
    created_at = Column(DateTime, default=func.now())

    environment_id = Column(Integer, ForeignKey("environments.id"), nullable=True)
    environment = relationship("Environment", back_populates="experiments")


class Environment(Base):
    __tablename__ = "environments"

    id = Column(Integer, primary_key=True, index=True)
    env_name = Column(String, unique=True, nullable=False)
    version = Column(String, default="v1")
    registered_at = Column(DateTime, default=func.now())

    experiments = relationship("Experiment", back_populates="environment")
