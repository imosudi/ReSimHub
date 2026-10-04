# tests/test_model_checkpointing.py
"""
Unit and integration test suite for model checkpointing and artifact versioning.
Validates:
  1. POST /checkpoints (Manual weight artifact registration and SHA-256 checksum generation)
  2. GET /checkpoints/{checkpoint_id}/weights (Dynamic weight loading and integrity check)
  3. Artifact tampering detection (SHA-256 checksum mismatch verification)
  4. GET /checkpoints/{checkpoint_id}/download (Binary artifact download)
  5. GET /checkpoints (Paginated filtering by algorithm, task, and is_best status)
  6. GET /checkpoints/best (Top-performing policy checkpoint retrieval)
  7. POST /checkpoints/{checkpoint_id}/resume (Dynamic training resumption)
  8. Flask API gateway checkpoint proxy routes
  9. Error handling and 404 not found responses
"""

import json
import uuid
import hashlib
from pathlib import Path
from unittest.mock import patch, AsyncMock
import pytest
from fastapi.testclient import TestClient

from backend.fastapi_app.main import app as fastapi_app
from backend.fastapi_app.services.checkpoint_service import (
    save_model_checkpoint,
    load_model_checkpoint,
    get_best_checkpoint,
    get_checkpoint_detail,
)
from backend.fastapi_app.core.db import SessionLocal
from shared.models.checkpoint_model import ModelCheckpointRecord
from backend.flask_app import app as flask_app


class DummyTaskResult:
    def __init__(self):
        self.id = f"task_{uuid.uuid4().hex[:8]}"


@pytest.fixture(autouse=True)
def mock_celery_apply_async():
    """
    Mock Celery task dispatch to isolate unit tests from external broker connectivity.
    """
    with patch(
        "backend.fastapi_app.services.orchestrator.run_training_task.apply_async",
        side_effect=lambda *args, **kwargs: DummyTaskResult()
    ):
        yield


fastapi_client = TestClient(fastapi_app)
flask_test_client = flask_app.test_client()


def test_manual_checkpoint_creation_and_checksum():
    """
    Verify creating and registering a model checkpoint generates a valid
    file artifact on disk and computes an accurate SHA-256 integrity hash.
    """
    weights = {
        "policy.fc1.weight": [[0.12, -0.34], [0.56, -0.78]],
        "policy.fc1.bias": [0.01, -0.02],
        "optimiser.lr": 0.0003,
    }
    payload = {
        "algo": "PPO",
        "env_name": "CartPole-v1",
        "epoch": 3,
        "step": 1500,
        "reward": 242.5,
        "loss": 0.035,
        "version": "v1.0",
        "weights": weights,
        "hyperparameters": {"clip_ratio": 0.2, "gamma": 0.99},
    }

    response = fastapi_client.post("/checkpoints", json=payload)
    assert response.status_code == 201, f"Failed: {response.text}"

    data = response.json()
    assert "checkpoint_id" in data
    assert data["algo"] == "PPO"
    assert data["env_name"] == "CartPole-v1"
    assert data["epoch"] == 3
    assert data["reward"] == 242.5
    assert data["is_best"] is True
    assert "checksum" in data
    assert "file_path" in data

    # Verify physical file existence and checksum recalculation
    artifact_path = Path(data["file_path"])
    assert artifact_path.exists(), "Checkpoint file was not written to storage"
    file_bytes = artifact_path.read_bytes()
    expected_checksum = hashlib.sha256(file_bytes).hexdigest()
    assert data["checksum"] == expected_checksum


def test_load_checkpoint_weights_and_tampering_detection():
    """
    Verify loading checkpoint weights dynamically, and ensure that any file
    corruption or tampering triggers a SHA-256 conflict error.
    """
    ckpt = save_model_checkpoint(
        algo="SAC",
        env_name="Pendulum-v1",
        epoch=2,
        reward=195.0,
        weights_dict={"layer1": [1.0, 2.0, 3.0]},
    )
    checkpoint_id = ckpt["checkpoint_id"]

    # 1. Successful weight loading
    res = fastapi_client.get(f"/checkpoints/{checkpoint_id}/weights")
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["checkpoint_id"] == checkpoint_id
    assert res_data["state_dict"]["layer1"] == [1.0, 2.0, 3.0]
    assert res_data["checksum"] == ckpt["checksum"]

    # 2. Simulate file tampering / bit rot on disk
    artifact_path = Path(ckpt["file_path"])
    original_bytes = artifact_path.read_bytes()
    tampered_bytes = original_bytes + b"tampered_data"
    artifact_path.write_bytes(tampered_bytes)

    # 3. Loading tampered artifact should return HTTP 409 Conflict
    tamper_res = fastapi_client.get(f"/checkpoints/{checkpoint_id}/weights")
    assert tamper_res.status_code == 409
    assert "integrity violation" in tamper_res.text.lower()

    # Restore original content for subsequent tests
    artifact_path.write_bytes(original_bytes)


def test_download_checkpoint_artifact():
    """
    Verify downloading the raw weight artifact file via HTTP streaming.
    """
    ckpt = save_model_checkpoint(
        algo="DQN",
        env_name="CartPole-v1",
        epoch=1,
        reward=160.0,
    )
    checkpoint_id = ckpt["checkpoint_id"]

    res = fastapi_client.get(f"/checkpoints/{checkpoint_id}/download")
    assert res.status_code == 200
    assert len(res.content) > 0
    calculated_hash = hashlib.sha256(res.content).hexdigest()
    assert calculated_hash == ckpt["checksum"]


def test_checkpoint_listing_and_filtering():
    """
    Verify querying paginated checkpoints with algorithm, task, and is_best filters.
    """
    task_filter_id = f"task_{uuid.uuid4().hex[:6]}"
    save_model_checkpoint(algo="DQN", env_name="CartPole-v1", epoch=1, task_id=task_filter_id, reward=120.0)
    save_model_checkpoint(algo="DQN", env_name="CartPole-v1", epoch=2, task_id=task_filter_id, reward=180.0)
    save_model_checkpoint(algo="PPO", env_name="CartPole-v1", epoch=1, task_id="other_task", reward=200.0)

    # 1. Filter by task_id
    res_task = fastapi_client.get(f"/checkpoints?task_id={task_filter_id}")
    assert res_task.status_code == 200
    data_task = res_task.json()
    assert data_task["total"] >= 2
    assert all(c["task_id"] == task_filter_id for c in data_task["checkpoints"])

    # 2. Filter by algorithm
    res_algo = fastapi_client.get("/checkpoints?algo=PPO")
    assert res_algo.status_code == 200
    data_algo = res_algo.json()
    assert all(c["algo"] == "PPO" for c in data_algo["checkpoints"])

    # 3. Filter by is_best
    res_best = fastapi_client.get(f"/checkpoints?task_id={task_filter_id}&is_best=true")
    assert res_best.status_code == 200
    data_best = res_best.json()
    assert len(data_best["checkpoints"]) == 1
    assert data_best["checkpoints"][0]["epoch"] == 2
    assert data_best["checkpoints"][0]["reward"] == 180.0


def test_best_checkpoint_tracking():
    """
    Verify that sequential checkpoint saves accurately track the single
    highest-performing checkpoint for a given training run.
    """
    unique_task = f"task_eval_{uuid.uuid4().hex[:6]}"
    save_model_checkpoint(algo="PPO", env_name="LunarLander-v2", epoch=1, task_id=unique_task, reward=150.0)
    save_model_checkpoint(algo="PPO", env_name="LunarLander-v2", epoch=2, task_id=unique_task, reward=235.0)
    save_model_checkpoint(algo="PPO", env_name="LunarLander-v2", epoch=3, task_id=unique_task, reward=210.0)

    res = fastapi_client.get(f"/checkpoints/best?task_id={unique_task}")
    assert res.status_code == 200
    best_data = res.json()
    assert best_data["task_id"] == unique_task
    assert best_data["epoch"] == 2
    assert best_data["reward"] == 235.0
    assert best_data["is_best"] is True


def test_resume_training_from_checkpoint():
    """
    Verify dynamically initiating continued training from a restored checkpoint.
    """
    ckpt = save_model_checkpoint(
        algo="SAC",
        env_name="Hopper-v3",
        epoch=4,
        reward=280.0,
        experiment_id=12,
    )
    checkpoint_id = ckpt["checkpoint_id"]

    resume_payload = {
        "resume_epochs": 4,
        "override_hyperparameters": {"learning_rate": 0.0001}
    }

    res = fastapi_client.post(f"/checkpoints/{checkpoint_id}/resume", json=resume_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["checkpoint_id"] == checkpoint_id
    assert data["start_epoch"] == 4
    assert data["target_epochs"] == 8
    assert data["status"] == "QUEUED"
    assert "task_id" in data


def test_flask_gateway_checkpoint_proxy():
    """
    Verify Flask API gateway forwards checkpoint queries, detail fetches,
    and resume requests to the underlying FastAPI backend.
    """
    mock_detail = {
        "checkpoint_id": "ckpt_gateway_1",
        "task_id": "task_gw",
        "algo": "PPO",
        "env_name": "CartPole-v1",
        "epoch": 2,
        "step": 1000,
        "reward": 210.0,
        "loss": 0.04,
        "file_path": "/storage/checkpoints/ckpt_gateway_1.pt",
        "file_size_bytes": 512,
        "checksum": "abc123hash",
        "version": "v1.0",
        "is_best": True,
        "metadata": {},
        "created_at": "2026-10-04T12:00:00"
    }

    mock_list = {
        "total": 1,
        "checkpoints": [mock_detail]
    }

    mock_resume = {
        "task_id": "task_resumed_99",
        "checkpoint_id": "ckpt_gateway_1",
        "algo": "PPO",
        "env_name": "CartPole-v1",
        "start_epoch": 2,
        "target_epochs": 7,
        "status": "QUEUED",
        "resumed_at": "2026-10-04T12:05:00"
    }

    with patch(
        "backend.flask_app.services.api_proxy.FastAPIProxy.get_checkpoints",
        new=AsyncMock(return_value=mock_list)
    ), patch(
        "backend.flask_app.services.api_proxy.FastAPIProxy.get_checkpoint_by_id",
        new=AsyncMock(return_value=mock_detail)
    ), patch(
        "backend.flask_app.services.api_proxy.FastAPIProxy.get_best_checkpoint",
        new=AsyncMock(return_value=mock_detail)
    ), patch(
        "backend.flask_app.services.api_proxy.FastAPIProxy.post_resume_checkpoint",
        new=AsyncMock(return_value=mock_resume)
    ):
        # 1. GET /api/v1/checkpoints
        res_list = flask_test_client.get("/api/v1/checkpoints?limit=10")
        assert res_list.status_code == 200
        assert res_list.get_json()["total"] == 1

        # 2. GET /api/v1/checkpoints/<checkpoint_id>
        res_item = flask_test_client.get("/api/v1/checkpoints/ckpt_gateway_1")
        assert res_item.status_code == 200
        assert res_item.get_json()["checkpoint_id"] == "ckpt_gateway_1"

        # 3. GET /api/v1/checkpoints/best
        res_best = flask_test_client.get("/api/v1/checkpoints/best?algo=PPO")
        assert res_best.status_code == 200
        assert res_best.get_json()["is_best"] is True

        # 4. POST /api/v1/checkpoints/<checkpoint_id>/resume
        res_resume = flask_test_client.post(
            "/api/v1/checkpoints/ckpt_gateway_1/resume",
            json={"resume_epochs": 5}
        )
        assert res_resume.status_code == 200
        assert res_resume.get_json()["task_id"] == "task_resumed_99"


def test_checkpoint_error_handling():
    """
    Verify that requests for missing checkpoints return HTTP 404 and
    validation errors return HTTP 422.
    """
    # 1. Non-existent checkpoint ID
    res_missing = fastapi_client.get("/checkpoints/ckpt_non_existent_99999")
    assert res_missing.status_code == 404
    error_msg = res_missing.json().get("error") or res_missing.json().get("detail", "")
    assert "not found" in error_msg.lower()

    # 2. Non-existent best checkpoint query
    res_no_best = fastapi_client.get("/checkpoints/best?task_id=task_imaginary_000")
    assert res_no_best.status_code == 404

    # 3. Invalid resume epochs (< 1)
    res_bad_epochs = fastapi_client.post(
        "/checkpoints/ckpt_non_existent_99999/resume",
        json={"resume_epochs": 0}
    )
    assert res_bad_epochs.status_code == 422
