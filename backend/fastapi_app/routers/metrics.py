# backend/fastapi_app/routers/metrics.py
from fastapi import APIRouter, Depends
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from sqlalchemy.orm import Session
from ..core.db import get_db
from ..core.logging_config import logger

router = APIRouter(prefix="/metrics", tags=["Observability"])

# Prometheus metric definitions
rl_experiments_active = Gauge("rl_experiments_active", "Number of active reinforcement learning experiments")
rl_training_completed_total = Gauge("rl_training_completed_total", "Total completed training runs")
rl_avg_benchmark_latency_ms = Gauge("rl_avg_benchmark_latency_ms", "Average benchmark latency in milliseconds")

# Simulated example values (in production, these should query the DB or state engine)
rl_experiments_active.set(3)
rl_training_completed_total.set(5)
rl_avg_benchmark_latency_ms.set(24.56)

logger.info("Observability & Persistence initialized.")

@router.get("/", response_class=Response)
async def get_metrics(db: Session = Depends(get_db)):
    """
    Expose application metrics in Prometheus format.
    Accessible at: http://127.0.0.1:8000/metrics
    """
    try:
        logger.info("Serving metrics endpoint")
        metrics_data = generate_latest()
        return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        logger.error("Error generating metrics", error=str(e))
        return Response(content=str(e), status_code=500)


