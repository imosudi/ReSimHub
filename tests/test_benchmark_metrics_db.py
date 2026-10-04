"""
tests/test_benchmark_metrics_db.py
----------------------------------
Validates advanced reinforcement learning benchmark metrics and
database persistence for benchmark records, model metadata, and training runs.
"""

import io
import pytest
from fastapi.testclient import TestClient

from backend.fastapi_app.main import app
from backend.fastapi_app.services.benchmark_service import BenchmarkService
from backend.fastapi_app.core.db import SessionLocal
from shared.models.benchmark_model import BenchmarkRecord, ModelMetadata

client = TestClient(app)


def test_advanced_benchmark_metrics_computation():
    """Verify calculation of statistical RL metrics (IQM, Success Rate, CVaR, Stability Score)."""
    model_id = "mdl_metrics_eval"
    env_name = "CartPole-v1"
    episodes = 60

    result = BenchmarkService.run_benchmark_simulation(model_id, env_name, episodes=episodes)

    # Core metrics
    assert "mean_reward" in result and result["mean_reward"] > 0
    assert "std_reward" in result and result["std_reward"] >= 0
    assert "median_reward" in result and result["median_reward"] > 0

    # Range metrics
    assert "min_reward" in result and "max_reward" in result
    assert result["min_reward"] <= result["max_reward"]
    assert result["min_reward"] <= result["mean_reward"] <= result["max_reward"]

    # Advanced RL robustness & distribution metrics
    assert "iqm_reward" in result
    assert result["iqm_reward"] > 0, "Interquartile Mean must be greater than zero"

    assert "success_rate" in result
    assert 0.0 <= result["success_rate"] <= 100.0, "Success rate must be a valid percentage"

    assert "cvar_reward" in result
    assert result["cvar_reward"] <= result["mean_reward"], "CVaR (worst 10% tail) must be <= overall mean"

    assert "stability_score" in result
    assert result["stability_score"] > 0, "Stability score (Sharpe-like ratio) must be positive"


def test_benchmark_database_persistence_and_history():
    """Verify that benchmark simulations persist records to database and are queryable via /benchmark/history."""
    model_id = "mdl_history_test"
    env_name = "Acrobot-v1"

    # Trigger simulation
    sim_data = BenchmarkService.run_benchmark_simulation(model_id, env_name, episodes=30)
    assert sim_data["status"] == "completed"

    # Query via API history endpoint
    resp = client.get(f"/benchmark/history?env_name={env_name}&model_id={model_id}")
    assert resp.status_code == 200
    data = resp.json()

    assert "total" in data
    assert data["total"] >= 1
    assert "results" in data
    assert len(data["results"]) >= 1

    first = data["results"][0]
    assert first["model_id"] == model_id
    assert first["env_name"] == env_name
    assert "iqm_reward" in first
    assert "cvar_reward" in first
    assert "stability_score" in first


def test_model_metadata_persistence_and_detail_endpoint():
    """Verify model upload persists metadata to DB and is retrievable via /benchmark/model/{model_id}."""
    file_bytes = b"Simulated PyTorch / ONNX model weights content"
    files = {"file": ("test_policy.pt", io.BytesIO(file_bytes), "application/octet-stream")}

    upload_resp = client.post("/benchmark/upload_model", files=files)
    assert upload_resp.status_code == 200
    upload_data = upload_resp.json()
    model_id = upload_data["model_id"]

    # Run one benchmark for this model
    BenchmarkService.run_benchmark_simulation(model_id, "CartPole-v1", episodes=20)

    # Query model details from DB
    detail_resp = client.get(f"/benchmark/model/{model_id}")
    assert detail_resp.status_code == 200
    details = detail_resp.json()

    assert details["model_id"] == model_id
    assert details["filename"] == "test_policy.pt"
    assert details["file_size_bytes"] == len(file_bytes)
    assert details["benchmarks_count"] >= 1
    assert details["best_mean_reward"] is not None


def test_orchestrate_tasks_listing_endpoint():
    """Verify /orchestrate/tasks endpoint queries training run records from the database."""
    resp = client.get("/orchestrate/tasks?limit=10")
    assert resp.status_code == 200
    data = resp.json()

    assert "total" in data
    assert "tasks" in data
    assert isinstance(data["tasks"], list)
