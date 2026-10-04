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


base_url = cache_config.url
if not base_url.endswith("/"):
    base_url += "/"

broker_url = f"{base_url}0"
backend_url = f"{base_url}1"
client_url = f"{base_url}2"

# Initialise Celery
celery_app = Celery(
    "resimhub",
    broker=broker_url,
    backend=backend_url,
)

# Redis for live progress updates
try:
    redis_client = redis.Redis.from_url(client_url, decode_responses=True)
except Exception:
    redis_client = None

# Optional: Redis-backed table for tracking tasks (used by /tasks)
TASK_TABLE_KEY = "resimhub:tasks"


def _sync_task_to_db(task_id: str, data: dict):
    """
    Sync or update task metadata in Redis and persist to database.
    """
    # 1. Update Redis cache
    if redis_client:
        try:
            existing = redis_client.hgetall(f"{TASK_TABLE_KEY}:{task_id}") or {}
            existing.update({k: str(v) for k, v in data.items()})
            redis_client.hset(f"{TASK_TABLE_KEY}:{task_id}", mapping=existing)
        except Exception as e:
            log.warning(f"Redis task sync error: {e}")

    # 2. Persist to PostgreSQL / SQLite database
    try:
        from backend.fastapi_app.core.db import SessionLocal
        from shared.models.training_model import TrainingRunRecord
        db = SessionLocal()
        record = db.query(TrainingRunRecord).filter(TrainingRunRecord.task_id == task_id).first()
        if not record:
            record = TrainingRunRecord(
                task_id=task_id,
                experiment_id=data.get("experiment_id"),
                algo=data.get("algo", "Unknown"),
                env_name=data.get("env", "CartPole-v1"),
                status=data.get("status", "RUNNING"),
                total_epochs=data.get("total_epochs", 5),
                created_at=datetime.utcnow()
            )
            db.add(record)
        else:
            if "status" in data:
                record.status = data["status"]
            if "last_epoch" in data:
                record.last_epoch = data["last_epoch"]
            if "last_reward" in data:
                record.last_reward = data["last_reward"]
            if "final_accuracy" in data:
                record.final_accuracy = data["final_accuracy"]
            if data.get("status") == "SUCCESS":
                record.completed_at = datetime.utcnow()
        db.commit()
        db.close()
    except Exception as exc:
        log.warning(f"Database task persistence error: {exc}")


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
        f"Training job for Experiment {experiment_id} completed | "
        f"Env={env_name} | Algo={algo} | Final Accuracy: {final_accuracy}"
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
