# backend/fastapi_app/routers/analytics.py
from fastapi import APIRouter, HTTPException
from backend.fastapi_app.services.analytics_service import AnalyticsService
from shared.utils.logger import get_logger

log = get_logger("AnalyticsRouter")
router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/experiment/{experiment_id}")
async def get_experiment_analytics(experiment_id: int):
    df = AnalyticsService.parse_experiment_logs(experiment_id)
    if df.empty:
        log.warning(f"No logs found for Experiment {experiment_id}")
        raise HTTPException(status_code=404, detail="No logs found for this experiment")

    stats = AnalyticsService.compute_statistics(df)
    log.info(f"Analytics for Experiment {experiment_id}: {stats}")
    return stats
