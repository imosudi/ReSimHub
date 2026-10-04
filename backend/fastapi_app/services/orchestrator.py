# backend/fastapi_app/services/orchestrator.py
from celery import Celery
import redis
import json
import time
import random
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
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

# Initialise Celery application
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

# Redis-backed table keys
TASK_TABLE_KEY = "resimhub:tasks"
BATCH_TABLE_KEY = "resimhub:batches"


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
                batch_id=data.get("batch_id"),
                trial_id=data.get("trial_id"),
                seed=data.get("seed", 42),
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
            if "batch_id" in data:
                record.batch_id = data["batch_id"]
            if "trial_id" in data:
                record.trial_id = data["trial_id"]
            if "seed" in data:
                record.seed = data["seed"]
            if "last_epoch" in data:
                record.last_epoch = data["last_epoch"]
            if "last_reward" in data:
                record.last_reward = data["last_reward"]
            if "final_accuracy" in data:
                record.final_accuracy = data["final_accuracy"]
            if data.get("status") in ("SUCCESS", "COMPLETED"):
                record.completed_at = datetime.utcnow()
        db.commit()
        db.close()
    except Exception as exc:
        log.warning(f"Database task persistence error: {exc}")


def _sync_batch_status(batch_id: str):
    """
    Recalculate batch completion status and aggregate trial metrics in database.
    """
    try:
        from backend.fastapi_app.core.db import SessionLocal
        from shared.models.training_model import BatchScheduleRecord, TrainingRunRecord
        db = SessionLocal()
        batch = db.query(BatchScheduleRecord).filter(BatchScheduleRecord.batch_id == batch_id).first()
        if not batch:
            db.close()
            return

        trials = db.query(TrainingRunRecord).filter(TrainingRunRecord.batch_id == batch_id).all()
        completed = sum(1 for t in trials if t.status in ("SUCCESS", "COMPLETED"))
        failed = sum(1 for t in trials if t.status in ("FAILURE", "REVOKED", "FAILED"))

        batch.completed_trials = completed
        batch.failed_trials = failed

        total = batch.total_trials or len(trials)
        if (completed + failed) >= total and total > 0:
            if failed == 0:
                batch.status = "COMPLETED"
            elif completed == 0:
                batch.status = "FAILED"
            else:
                batch.status = "PARTIAL_FAILURE"
            batch.completed_at = datetime.utcnow()
        elif any(t.status in ("RUNNING", "PROGRESS") for t in trials):
            batch.status = "RUNNING"

        db.commit()
        db.close()
    except Exception as exc:
        log.warning(f"Failed to update batch schedule status for {batch_id}: {exc}")


# -------------------------------------------------------------
# 🎯 Celery Tasks
# -------------------------------------------------------------

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

    # Record job start
    _sync_task_to_db(task_id, {
        "experiment_id": experiment_id,
        "algo": algo,
        "env": env_name,
        "status": "RUNNING",
        "created_at": datetime.utcnow().isoformat(),
    })

    for epoch in range(total_epochs):
        time.sleep(1)  # Simulate training step
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

        self.update_state(state="PROGRESS", meta=meta)
        if redis_client:
            redis_client.publish(f"task_progress:{task_id}", json.dumps(meta))

        log.info(f"Experiment {experiment_id} | Epoch {epoch + 1}/{total_epochs} | Reward: {reward}")

        _sync_task_to_db(task_id, {
            "last_epoch": epoch + 1,
            "last_reward": reward,
            "updated_at": datetime.utcnow().isoformat(),
        })

    final_accuracy = round(random.uniform(0.8, 0.99), 4)
    result = {
        "experiment_id": experiment_id,
        "algo": algo,
        "env": env_name,
        "final_accuracy": final_accuracy,
        "completed_at": datetime.utcnow().isoformat(),
        "status": "SUCCESS",
    }

    if redis_client:
        redis_client.publish(f"task_progress:{task_id}", json.dumps(result))

    log.info(
        f"Training job for Experiment {experiment_id} completed | "
        f"Env={env_name} | Algo={algo} | Final Accuracy: {final_accuracy}"
    )

    _sync_task_to_db(task_id, {
        "status": "SUCCESS",
        "final_accuracy": final_accuracy,
        "completed_at": datetime.utcnow().isoformat(),
    })

    return result


@celery_app.task(bind=True, name="run_multi_agent_trial_task")
def run_multi_agent_trial_task(
    self,
    batch_id: str,
    trial_id: str,
    algo: str,
    env_name: str,
    seed: int = 42,
    total_epochs: int = 5,
    hyperparameters: Optional[dict] = None
):
    """
    Execute an individual RL agent trial within a multi-agent scheduled batch.
    Publishes live progress to both task-specific and batch-level Redis channels.
    """
    task_id = self.request.id
    log.info(
        f"Starting trial {trial_id} in batch {batch_id}: "
        f"algo={algo}, seed={seed}, env={env_name}, epochs={total_epochs}"
    )

    try:
        # Initialise random state deterministically for this seed
        rnd = random.Random(seed + sum(ord(c) for c in trial_id))

        _sync_task_to_db(task_id, {
            "batch_id": batch_id,
            "trial_id": trial_id,
            "algo": algo,
            "env": env_name,
            "seed": seed,
            "status": "RUNNING",
            "total_epochs": total_epochs,
            "created_at": datetime.utcnow().isoformat(),
        })

        # Algorithm specific baseline rewards
        base_rewards = {"SAC": 220.0, "PPO": 210.0, "DQN": 190.0, "A2C": 180.0}
        base = base_rewards.get(algo, 195.0)

        for epoch in range(total_epochs):
            time.sleep(0.8)  # Step simulation
            epoch_gain = (epoch + 1) * rnd.uniform(2.5, 6.0)
            noise = rnd.uniform(-10.0, 10.0)
            reward = round(base + epoch_gain + noise, 2)

            meta = {
                "batch_id": batch_id,
                "trial_id": trial_id,
                "task_id": task_id,
                "algo": algo,
                "seed": seed,
                "env": env_name,
                "epoch": epoch + 1,
                "total_epochs": total_epochs,
                "reward": reward,
                "status": "PROGRESS",
                "timestamp": datetime.utcnow().isoformat(),
            }

            self.update_state(state="PROGRESS", meta=meta)

            if redis_client:
                redis_client.publish(f"task_progress:{task_id}", json.dumps(meta))
                redis_client.publish(f"batch_progress:{batch_id}", json.dumps(meta))

            _sync_task_to_db(task_id, {
                "last_epoch": epoch + 1,
                "last_reward": reward,
                "updated_at": datetime.utcnow().isoformat(),
            })

        final_accuracy = round(rnd.uniform(0.85, 0.99), 4)
        result = {
            "batch_id": batch_id,
            "trial_id": trial_id,
            "task_id": task_id,
            "algo": algo,
            "seed": seed,
            "env": env_name,
            "final_accuracy": final_accuracy,
            "final_reward": reward,
            "completed_at": datetime.utcnow().isoformat(),
            "status": "SUCCESS",
        }

        if redis_client:
            redis_client.publish(f"task_progress:{task_id}", json.dumps(result))
            redis_client.publish(f"batch_progress:{batch_id}", json.dumps(result))

        _sync_task_to_db(task_id, {
            "status": "SUCCESS",
            "final_accuracy": final_accuracy,
            "completed_at": datetime.utcnow().isoformat(),
        })

        _sync_batch_status(batch_id)

        log.info(f"Trial {trial_id} in batch {batch_id} finished: reward={reward}, accuracy={final_accuracy}")
        return result
    except Exception as exc:
        log.error(f"Trial {trial_id} in batch {batch_id} failed: {exc}")
        _sync_task_to_db(task_id, {
            "status": "FAILED",
            "completed_at": datetime.utcnow().isoformat(),
        })
        _sync_batch_status(batch_id)
        raise exc


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
        if redis_client:
            redis_client.publish(f"task_progress:{task_id}", json.dumps({
                "progress": progress,
                "total": total,
                "status": "PROGRESS"
            }))

    _sync_task_to_db(task_id, {"status": "SUCCESS", "completed_at": datetime.utcnow().isoformat()})
    return {"current": total, "total": total, "status": "Task completed!"}


# -------------------------------------------------------------
# 🚀 High-Level Orchestration API Services
# -------------------------------------------------------------

def schedule_multi_agent_batch(batch_request) -> Dict[str, Any]:
    """
    Schedule a parallel batch of agent trials across Celery workers.
    Persists batch schedule and queued trials in the database.
    """
    from backend.fastapi_app.core.db import SessionLocal
    from shared.models.training_model import BatchScheduleRecord, TrainingRunRecord

    batch_id = f"batch_{uuid.uuid4().hex[:8]}"
    db = SessionLocal()

    batch_rec = BatchScheduleRecord(
        batch_id=batch_id,
        name=batch_request.name,
        env_name=batch_request.env_name,
        status="SCHEDULED",
        total_trials=len(batch_request.agents),
        completed_trials=0,
        failed_trials=0,
        priority=batch_request.priority,
        created_at=datetime.utcnow()
    )
    db.add(batch_rec)
    db.commit()

    task_ids = []
    for agent_cfg in batch_request.agents:
        trial_id = f"trial_{uuid.uuid4().hex[:6]}"
        hyperparams = getattr(agent_cfg, "hyperparameters", {}) or {}

        # Dispatch asynchronous Celery task with priority
        async_task = run_multi_agent_trial_task.apply_async(
            args=[
                batch_id,
                trial_id,
                agent_cfg.algo,
                batch_request.env_name,
                agent_cfg.seed,
                agent_cfg.total_epochs,
                hyperparams
            ],
            priority=batch_request.priority
        )
        task_ids.append(async_task.id)

        # Record initial trial state in DB
        trial_rec = TrainingRunRecord(
            task_id=async_task.id,
            batch_id=batch_id,
            trial_id=trial_id,
            algo=agent_cfg.algo,
            env_name=batch_request.env_name,
            seed=agent_cfg.seed,
            status="QUEUED",
            total_epochs=agent_cfg.total_epochs,
            created_at=datetime.utcnow()
        )
        db.add(trial_rec)

    db.commit()
    db.close()

    log.info(f"Scheduled multi-agent batch {batch_id} with {len(batch_request.agents)} parallel trials")
    return {
        "batch_id": batch_id,
        "name": batch_request.name,
        "env_name": batch_request.env_name,
        "status": "SCHEDULED",
        "total_trials": len(batch_request.agents),
        "task_ids": task_ids,
        "scheduled_at": datetime.utcnow().isoformat()
    }


def get_batch_status(batch_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve real-time consolidated status and aggregate metrics for a batch.
    """
    from backend.fastapi_app.core.db import SessionLocal
    from shared.models.training_model import BatchScheduleRecord, TrainingRunRecord

    db = SessionLocal()
    batch = db.query(BatchScheduleRecord).filter(BatchScheduleRecord.batch_id == batch_id).first()
    if not batch:
        db.close()
        return None

    trials = db.query(TrainingRunRecord).filter(TrainingRunRecord.batch_id == batch_id).all()

    trial_details = []
    rewards = []
    for t in trials:
        trial_details.append({
            "trial_id": t.trial_id or t.task_id[:8],
            "task_id": t.task_id,
            "algo": t.algo,
            "seed": t.seed or 42,
            "status": t.status,
            "current_epoch": t.last_epoch or 0,
            "total_epochs": t.total_epochs or 5,
            "latest_reward": t.last_reward,
            "final_accuracy": t.final_accuracy
        })
        if t.last_reward is not None:
            rewards.append(t.last_reward)

    summary_metrics = None
    if rewards:
        summary_metrics = {
            "avg_reward": round(sum(rewards) / len(rewards), 2),
            "max_reward": round(max(rewards), 2),
            "min_reward": round(min(rewards), 2),
            "active_trials": sum(1 for t in trials if t.status in ("RUNNING", "PROGRESS", "QUEUED")),
            "completed_trials": sum(1 for t in trials if t.status in ("SUCCESS", "COMPLETED"))
        }

    data = {
        "batch_id": batch.batch_id,
        "name": batch.name,
        "env_name": batch.env_name,
        "status": batch.status,
        "total_trials": batch.total_trials,
        "completed_trials": batch.completed_trials,
        "failed_trials": batch.failed_trials,
        "priority": batch.priority,
        "created_at": batch.created_at,
        "completed_at": batch.completed_at,
        "trials": trial_details,
        "summary_metrics": summary_metrics
    }
    db.close()
    return data


def list_batches(limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    """
    Query paginated list of scheduled multi-agent batches from the database.
    """
    from backend.fastapi_app.core.db import SessionLocal
    from shared.models.training_model import BatchScheduleRecord

    db = SessionLocal()
    query = db.query(BatchScheduleRecord).order_by(BatchScheduleRecord.created_at.desc())
    total = query.count()
    items = query.offset(offset).limit(limit).all()

    batch_list = []
    for b in items:
        status_info = get_batch_status(b.batch_id)
        if status_info:
            batch_list.append(status_info)

    db.close()
    return {"total": total, "batches": batch_list}
