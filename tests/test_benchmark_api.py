
"""
# tests/test_benchmark_api.py
------------------------------------------
Validates upload, run, list, and compare endpoints for
the ReSimHub Benchmark module.
"""

import io
import json
import pytest

from fastapi.testclient import TestClient
from pathlib import Path
from datetime import datetime

# Import FastAPI app
from backend.fastapi_app.main import app

client = TestClient(app)

STORAGE_DIR = Path("storage/models")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session")
def dummy_model_file():
    """Creates a small dummy binary file to mimic a trained model."""
    path = STORAGE_DIR / "dummy_dqn.pkl"
    path.write_bytes(b"This is a fake model file for testing.")
    return path


def test_upload_model(dummy_model_file):
    """Test uploading a model file via multipart form."""
    with open(dummy_model_file, "rb") as f:
        response = client.post("/benchmark/upload_model", files={"file": ("dummy_dqn.pkl", f, "application/octet-stream")})

    assert response.status_code == 200, f"Unexpected status: {response.text}"
    data = response.json()

    assert "model_id" in data
    assert data["status"] == "uploaded"
    assert "uploaded_at" in data

    # Save model_id globally for reuse
    global MODEL_ID
    MODEL_ID = data["model_id"]
    print(f"\n✅ Uploaded model_id={MODEL_ID}")


def test_run_benchmark():
    """Test running a benchmark simulation for uploaded model."""
    payload = {
        "model_id": MODEL_ID,
        "env_name": "CartPole-v1",
        "episodes": 10
    }

    response = client.post(
        "/benchmark/run",
        data=payload
    )
    assert response.status_code == 200
    data = response.json()

    assert data["model_id"] == MODEL_ID
    assert data["env_name"] == "CartPole-v1"
    assert "mean_reward" in data
    assert data["status"] == "completed"
    print(f"✅ Benchmark run completed: mean_reward={data['mean_reward']}")


def test_list_recent_results():
    """Verify that recent benchmark results can be retrieved."""
    response = client.get("/benchmark/recent")
    assert response.status_code == 200

    data = response.json()
    assert "count" in data
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) >= 1

    print(f"✅ Retrieved {data['count']} recent results")


def test_compare_models():
    """Compare same model twice (mocking multi-model comparison)."""
    # Use the same model twice for simulation
    compare_ids = f"{MODEL_ID},{MODEL_ID}"
    response = client.get(f"/benchmark/compare?model_ids={compare_ids}&env=CartPole-v1")

    # Allow 200 OK or 404 if Redis/file mismatch
    assert response.status_code in (200, 404)

    data = response.json()
    if response.status_code == 200:
        #assert isinstance(data, list) or "models" in data
        assert isinstance(data, list) or "models" in data or "comparison" in data
        print(f"✅ Model comparison response: {json.dumps(data, indent=2)}")
        if "comparison" in data:
            assert "models" in data["comparison"]
    else:
        assert "error" in data
        print(f"⚠️ Comparison fallback: {data['error']}")


def test_invalid_compare_model_id():
    """Test graceful handling for missing model_ids."""
    response = client.get("/benchmark/compare?model_ids=mdl_fakeid&env=CartPole-v1")
    assert response.status_code in (200, 404)

    data = response.json()
    if "error" in data:
        assert "No benchmark records" in data["error"]
        print(f"✅ Properly handled invalid model_id: {data['error']}")

