from fastapi import APIRouter, Query
from shared.utils.logger import get_logger
from backend.fastapi_app.services.analytics_service import AnalyticsService

log = get_logger("AnalyticsRouter")
router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/recent")
async def get_recent_experiments(limit: int = Query(5, ge=1, le=50)):
    """
    List recent experiments with final accuracy/reward.
    """
    records = AnalyticsService.list_recent_experiments(limit)
    if not records:
        return {"error": "No experiments found in logs."}
    return records


@router.get("/experiment/{experiment_id}")
async def get_experiment_analytics(experiment_id: int):
    """
    Compute analytics for a single experiment:
    - mean_reward
    - std_reward
    - convergence_epoch
    - last_reward
    """
    df = AnalyticsService.parse_experiment_logs(experiment_id)
    if df.empty:
        log.warning(f"No logs found for Experiment {experiment_id}")
        return {"error": f"No logs found for Experiment {experiment_id}"}

    stats = AnalyticsService.compute_statistics(df)
    stats["last_reward"] = df["reward"].iloc[-1] if not df.empty else None
    stats["total_epochs"] = len(df)

    return stats
