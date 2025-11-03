# backend/fastapi_app/services/orchestrator.py
from celery import Celery
import redis
import json
import time
import random
from datetime import datetime
from backend.fastapi_app.core.config import CacheConfig
from shared.utils.logger import get_logger

log = get_logger("TrainingService")


cache_config = CacheConfig()


# Initialise Celery
celery_app = Celery(
    "resimhub",
    broker=cache_config.url+'0', #"redis://localhost:6379/0",
    backend=cache_config.url+'1', #"redis://localhost:6379/1",
)

# Redis for live progress updates
redis_client = redis.Redis(host="localhost", port=6379, db=2, decode_responses=True)

# Optional: Redis-backed table for tracking tasks (used by /tasks)
TASK_TABLE_KEY = "resimhub:tasks"


def _sync_task_to_db(task_id: str, data: dict):
    """
    Sync or update task metadata in Redis.
    (Later can be extended to PostgreSQL or SQLAlchemy model)
    """
    existing = redis_client.hgetall(f"{TASK_TABLE_KEY}:{task_id}") or {}
    existing.update(data)
    redis_client.hset(f"{TASK_TABLE_KEY}:{task_id}", mapping=existing)


@celery_app.task(bind=True, name="run_training_task")
def run_training_task(self, experiment_id: int, env_name: str, algo: str):
    """
    Simulate asynchronous reinforcement learning training job.
    Logs actual reward values per epoch for analytics integration.
    Broadcasts updates over Redis channels for progress monitoring.
    """
    log.info(f"Starting training job for Experiment {experiment_id} | Env={env_name} | Algo={algo}")
    task_id = self.request.id
    total_epochs = 5

    # Record job start in Redis
    _sync_task_to_db(task_id, {
        "experiment_id": experiment_id,
        "algo": algo,
        "env": env_name,
        "status": "RUNNING",
        "created_at": datetime.utcnow().isoformat(),
    })

    for epoch in range(total_epochs):
        time.sleep(2)  # Simulate training time
        # Simulate realistic reward signal
        reward = round(random.uniform(180, 250), 2)

        meta = {
            "experiment_id": experiment_id,
            "env": env_name,
            "algo": algo,
            "epoch": epoch + 1,
            "total_epochs": total_epochs,
            "reward": reward,
            "status": "PROGRESS",
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Update Celery progress state
        self.update_state(state="PROGRESS", meta=meta)

        # Broadcast via Redis (for Server-Sent Events or WebSocket updates)
        redis_client.publish(f"task_progress:{task_id}", json.dumps(meta))

        # ✅ Log reward in analytics-compatible format
        log.info(f"Experiment {experiment_id} | Epoch {epoch + 1}/{total_epochs} | Reward: {reward}")

        # Persist latest epoch info in Redis
        _sync_task_to_db(task_id, {
            "last_epoch": epoch + 1,
            "last_reward": reward,
            "updated_at": datetime.utcnow().isoformat(),
        })

    # Final results summary
    final_accuracy = round(random.uniform(0.8, 0.99), 4)
    result = {
        "experiment_id": experiment_id,
        "algo": algo,
        "env": env_name,
        "final_accuracy": final_accuracy,
        "completed_at": datetime.utcnow().isoformat(),
        "status": "SUCCESS",
    }

    # Broadcast completion
    redis_client.publish(f"task_progress:{task_id}", json.dumps(result))
    log.info(
        f"Training job for Experiment {experiment_id} completed successfully "
        f"(Final Accuracy: {final_accuracy})"
    )

    # Sync final state to Redis
    _sync_task_to_db(task_id, {
        "status": "SUCCESS",
        "final_accuracy": final_accuracy,
        "completed_at": datetime.utcnow().isoformat(),
    })

    return result


@celery_app.task(bind=True, name="long_task")
def long_task(self, total=100):
    """
    Simulates a long-running task with progress updates.
    Useful for testing orchestration pipeline.
    """
    task_id = self.request.id
    _sync_task_to_db(task_id, {"status": "RUNNING", "type": "long_task"})

    for i in range(total):
        time.sleep(0.1)
        progress = (i + 1)
        self.update_state(state="PROGRESS", meta={"current": progress, "total": total})
        redis_client.publish(f"task_progress:{task_id}", json.dumps({
            "progress": progress,
            "total": total,
            "status": "PROGRESS"
        }))

    _sync_task_to_db(task_id, {"status": "SUCCESS", "completed_at": datetime.utcnow().isoformat()})
    return {"current": total, "total": total, "status": "Task completed!"}
