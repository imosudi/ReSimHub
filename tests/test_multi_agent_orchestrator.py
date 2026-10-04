# tests/test_multi_agent_orchestrator.py
"""
Unit and integration test suite for multi-agent parallel batch orchestration.
Validates:
  1. POST /orchestrate/batch (Scheduling diverse agent trials across Celery)
  2. GET /orchestrate/batch/{batch_id} (Consolidated status and aggregate metrics)
  3. GET /orchestrate/batches (Paginated list of batch schedules)
  4. Trial status synchronisation and aggregate metric calculations
  5. Partial failure state transitions
  6. WebSocket live batch progress telemetry (/ws/batch/{batch_id})
  7. Flask API gateway proxy integration (/api/v1/schedule_batch, /api/v1/batches)
  8. Pydantic request validation and error handling
"""

import json
import asyncio
from unittest.mock import patch, AsyncMock
import pytest
from fastapi.testclient import TestClient

from backend.fastapi_app.main import app as fastapi_app
from backend.fastapi_app.services.progress_broadcast import get_broadcast_service
from backend.fastapi_app.services.orchestrator import (
    _sync_task_to_db,
    _sync_batch_status,
    get_batch_status,
)
from backend.fastapi_app.core.db import SessionLocal
from shared.models.training_model import BatchScheduleRecord, TrainingRunRecord
from backend.flask_app import app as flask_app


import uuid


class DummyTaskResult:
    def __init__(self):
        self.id = f"task_{uuid.uuid4().hex[:8]}"


@pytest.fixture(autouse=True)
def mock_celery_apply_async():
    """
    Mock Celery task dispatch to isolate unit tests from external broker connectivity.
    """
    with patch(
        "backend.fastapi_app.services.orchestrator.run_multi_agent_trial_task.apply_async",
        side_effect=lambda *args, **kwargs: DummyTaskResult()
    ):
        yield


fastapi_client = TestClient(fastapi_app)
flask_test_client = flask_app.test_client()


def test_schedule_multi_agent_batch_success():
    """
    Verify scheduling a parallel multi-agent batch with diverse algorithms,
    seeds, and hyperparameters persists records in the database.
    """
    payload = {
        "name": "CartPole Parallel Hyperparameter Sweep",
        "env_name": "CartPole-v1",
        "priority": 7,
        "agents": [
            {
                "algo": "DQN",
                "seed": 101,
                "total_epochs": 5,
                "hyperparameters": {"learning_rate": 0.001, "gamma": 0.99}
            },
            {
                "algo": "PPO",
                "seed": 202,
                "total_epochs": 5,
                "hyperparameters": {"clip_ratio": 0.2, "entropy_coef": 0.01}
            },
            {
                "algo": "SAC",
                "seed": 303,
                "total_epochs": 5,
                "hyperparameters": {"tau": 0.005}
            }
        ]
    }

    response = fastapi_client.post("/orchestrate/batch", json=payload)
    assert response.status_code == 200, f"Scheduling failed: {response.text}"

    data = response.json()
    assert "batch_id" in data
    assert data["name"] == payload["name"]
    assert data["env_name"] == payload["env_name"]
    assert data["status"] == "SCHEDULED"
    assert data["total_trials"] == 3
    assert len(data["task_ids"]) == 3

    batch_id = data["batch_id"]

    # Verify persistence in database
    db = SessionLocal()
    batch_record = db.query(BatchScheduleRecord).filter(
        BatchScheduleRecord.batch_id == batch_id
    ).first()
    assert batch_record is not None
    assert batch_record.status == "SCHEDULED"
    assert batch_record.priority == 7
    assert batch_record.total_trials == 3

    trial_records = db.query(TrainingRunRecord).filter(
        TrainingRunRecord.batch_id == batch_id
    ).all()
    assert len(trial_records) == 3

    algos = {t.algo for t in trial_records}
    assert algos == {"DQN", "PPO", "SAC"}

    seeds = {t.seed for t in trial_records}
    assert seeds == {101, 202, 303}

    for t in trial_records:
        assert t.status == "QUEUED"
        assert t.total_epochs == 5

    db.close()


def test_get_batch_status_success_and_not_found():
    """
    Verify retrieval of scheduled batch status, trial details, and 404 on missing batch.
    """
    # 1. Create a batch
    payload = {
        "name": "LunarLander Evaluation Campaign",
        "env_name": "LunarLander-v2",
        "priority": 5,
        "agents": [
            {"algo": "PPO", "seed": 42, "total_epochs": 4},
            {"algo": "A2C", "seed": 84, "total_epochs": 4}
        ]
    }
    create_res = fastapi_client.post("/orchestrate/batch", json=payload)
    assert create_res.status_code == 200
    batch_id = create_res.json()["batch_id"]

    # 2. Retrieve batch status
    status_res = fastapi_client.get(f"/orchestrate/batch/{batch_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()

    assert status_data["batch_id"] == batch_id
    assert status_data["name"] == payload["name"]
    assert status_data["env_name"] == "LunarLander-v2"
    assert status_data["total_trials"] == 2
    assert len(status_data["trials"]) == 2

    # 3. Test non-existent batch identifier
    missing_res = fastapi_client.get("/orchestrate/batch/batch_non_existent_9999")
    assert missing_res.status_code == 404
    error_msg = missing_res.json().get("error") or missing_res.json().get("detail", "")
    assert "not found" in error_msg.lower()


def test_list_batches_pagination():
    """
    Verify paginated query of multi-agent batch schedules.
    """
    list_res = fastapi_client.get("/orchestrate/batches?limit=10&offset=0")
    assert list_res.status_code == 200
    list_data = list_res.json()

    assert "total" in list_data
    assert "batches" in list_data
    assert isinstance(list_data["batches"], list)
    assert list_data["total"] >= len(list_data["batches"])


def test_batch_status_recalculation_and_metrics_aggregation():
    """
    Verify that trial state progression triggers accurate batch status
    transitions and mathematical metric aggregation (avg, max, min rewards).
    """
    payload = {
        "name": "BipedalWalker Convergence Benchmark",
        "env_name": "BipedalWalker-v3",
        "priority": 6,
        "agents": [
            {"algo": "SAC", "seed": 11, "total_epochs": 3},
            {"algo": "DQN", "seed": 22, "total_epochs": 3}
        ]
    }
    res = fastapi_client.post("/orchestrate/batch", json=payload)
    assert res.status_code == 200
    batch_id = res.json()["batch_id"]
    task_ids = res.json()["task_ids"]

    # Simulate completion of trial 1
    _sync_task_to_db(task_ids[0], {
        "status": "SUCCESS",
        "last_epoch": 3,
        "last_reward": 220.5,
        "final_accuracy": 0.94
    })
    _sync_batch_status(batch_id)

    # Check intermediate state: 1 completed, 1 queued
    intermediate = get_batch_status(batch_id)
    assert intermediate["completed_trials"] == 1
    assert intermediate["status"] in ("SCHEDULED", "RUNNING")

    # Simulate completion of trial 2
    _sync_task_to_db(task_ids[1], {
        "status": "SUCCESS",
        "last_epoch": 3,
        "last_reward": 260.5,
        "final_accuracy": 0.96
    })
    _sync_batch_status(batch_id)

    # Verify final aggregate status
    final_status = get_batch_status(batch_id)
    assert final_status["status"] == "COMPLETED"
    assert final_status["completed_trials"] == 2
    assert final_status["failed_trials"] == 0
    assert final_status["completed_at"] is not None

    metrics = final_status["summary_metrics"]
    assert metrics is not None
    assert metrics["avg_reward"] == 240.5
    assert metrics["max_reward"] == 260.5
    assert metrics["min_reward"] == 220.5
    assert metrics["completed_trials"] == 2
    assert metrics["active_trials"] == 0


def test_batch_partial_failure_state_transition():
    """
    Verify that a batch with mixed successes and failures transitions
    to PARTIAL_FAILURE status correctly.
    """
    payload = {
        "name": "Acrobot Resilience Testing",
        "env_name": "Acrobot-v1",
        "priority": 4,
        "agents": [
            {"algo": "PPO", "seed": 1, "total_epochs": 2},
            {"algo": "DQN", "seed": 2, "total_epochs": 2}
        ]
    }
    res = fastapi_client.post("/orchestrate/batch", json=payload)
    batch_id = res.json()["batch_id"]
    task_ids = res.json()["task_ids"]

    # Trial 1 succeeds
    _sync_task_to_db(task_ids[0], {
        "status": "SUCCESS",
        "last_epoch": 2,
        "last_reward": 185.0
    })

    # Trial 2 fails
    _sync_task_to_db(task_ids[1], {
        "status": "FAILURE",
        "last_epoch": 1,
        "last_reward": 50.0
    })

    _sync_batch_status(batch_id)

    batch_info = get_batch_status(batch_id)
    assert batch_info["status"] == "PARTIAL_FAILURE"
    assert batch_info["completed_trials"] == 1
    assert batch_info["failed_trials"] == 1


def test_websocket_batch_progress_stream():
    """
    Verify WebSocket subscription to /ws/batch/{batch_id} handles connection,
    ping/pong, and receives live broadcasted multi-agent telemetry events.
    """
    batch_id = "batch_test_stream_777"
    broadcaster = get_broadcast_service()

    with fastapi_client.websocket_connect(f"/ws/batch/{batch_id}") as websocket:
        # Initial greeting event
        greeting = websocket.receive_json()
        assert greeting["event"] == "connected"
        assert greeting["batch_id"] == batch_id
        assert greeting["status"] == "LISTENING"

        # Ping and pong check
        websocket.send_text(json.dumps({"action": "ping"}))
        pong = websocket.receive_json()
        assert pong["action"] == "pong"

        # Broadcast simulated batch progress update
        progress_payload = {
            "batch_id": batch_id,
            "trial_id": "trial_alpha_01",
            "algo": "SAC",
            "epoch": 2,
            "total_epochs": 5,
            "reward": 234.8,
            "status": "PROGRESS"
        }
        asyncio.run(broadcaster.publish_batch(batch_id, progress_payload))

        # Receive streamed progress message over WebSocket
        received_text = websocket.receive_text()
        received_data = json.loads(received_text)
        assert received_data["batch_id"] == batch_id
        assert received_data["trial_id"] == "trial_alpha_01"
        assert received_data["reward"] == 234.8
        assert received_data["status"] == "PROGRESS"


def test_flask_gateway_batch_proxy_routes():
    """
    Verify Flask API gateway forwards batch schedule, status, and list requests
    to the underlying FastAPI orchestration service.
    """
    mock_schedule_response = {
        "batch_id": "batch_mock_123",
        "name": "Gateway Test Batch",
        "env_name": "CartPole-v1",
        "status": "SCHEDULED",
        "total_trials": 2,
        "task_ids": ["task-1", "task-2"],
        "scheduled_at": "2026-10-04T10:00:00"
    }

    mock_status_response = {
        "batch_id": "batch_mock_123",
        "name": "Gateway Test Batch",
        "env_name": "CartPole-v1",
        "status": "COMPLETED",
        "total_trials": 2,
        "completed_trials": 2,
        "failed_trials": 0,
        "priority": 5,
        "trials": [],
        "summary_metrics": {"avg_reward": 210.0}
    }

    mock_list_response = {
        "total": 1,
        "batches": [mock_status_response]
    }

    with patch(
        "backend.flask_app.services.api_proxy.FastAPIProxy.post_schedule_batch",
        new=AsyncMock(return_value=mock_schedule_response)
    ), patch(
        "backend.flask_app.services.api_proxy.FastAPIProxy.get_batch_status",
        new=AsyncMock(return_value=mock_status_response)
    ), patch(
        "backend.flask_app.services.api_proxy.FastAPIProxy.get_batches",
        new=AsyncMock(return_value=mock_list_response)
    ):
        # 1. Test POST /api/v1/schedule_batch
        res_post = flask_test_client.post(
            "/api/v1/schedule_batch",
            json={"name": "Gateway Test Batch", "env_name": "CartPole-v1", "agents": []}
        )
        assert res_post.status_code == 200
        assert res_post.get_json()["batch_id"] == "batch_mock_123"

        # 2. Test GET /api/v1/batches/<batch_id>
        res_get = flask_test_client.get("/api/v1/batches/batch_mock_123")
        assert res_get.status_code == 200
        assert res_get.get_json()["status"] == "COMPLETED"

        # 3. Test GET /api/v1/batches
        res_list = flask_test_client.get("/api/v1/batches?limit=10&offset=0")
        assert res_list.status_code == 200
        assert res_list.get_json()["total"] == 1


def test_batch_schedule_validation_errors():
    """
    Verify that invalid request payloads are rejected with HTTP 422
    Unprocessable Entity by Pydantic validation rules.
    """
    # 1. Empty agent configuration list
    res_empty_agents = fastapi_client.post("/orchestrate/batch", json={
        "name": "Invalid Batch",
        "env_name": "CartPole-v1",
        "agents": []
    })
    assert res_empty_agents.status_code == 422

    # 2. Invalid priority out of bounds (> 10)
    res_bad_priority = fastapi_client.post("/orchestrate/batch", json={
        "name": "Invalid Priority",
        "env_name": "CartPole-v1",
        "priority": 99,
        "agents": [{"algo": "DQN"}]
    })
    assert res_bad_priority.status_code == 422

    # 3. Invalid total_epochs out of bounds (> 100)
    res_bad_epochs = fastapi_client.post("/orchestrate/batch", json={
        "name": "Invalid Epochs",
        "env_name": "CartPole-v1",
        "agents": [{"algo": "DQN", "total_epochs": 500}]
    })
    assert res_bad_epochs.status_code == 422
