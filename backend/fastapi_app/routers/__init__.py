# backend/fastapi_app/routers/__init__.py
from . import experiments, environments, status, train, orchestrator, analytics, benchmark, metrics, dashboard

__all__ = [
    "experiments",
    "environments",
    "status",
    "train",
    "orchestrator",
    "analytics",
    "benchmark",
    "metrics",
    "dashboard",
]
