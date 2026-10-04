# tests/test_integration.py
import pytest
import requests

FASTAPI_BASE = "http://127.0.0.1:8000"
FLASK_BASE = "http://127.0.0.1:5000"


def _services_available():
    try:
        r1 = requests.get(f"{FASTAPI_BASE}/health", timeout=1)
        r2 = requests.get(f"{FLASK_BASE}/health", timeout=1)
        return r1.status_code == 200 and r2.status_code == 200
    except Exception:
        return False


skip_if_no_live_services = pytest.mark.skipif(
    not _services_available(),
    reason="Live FastAPI/Flask services not running on ports 8000 and 5000"
)


@skip_if_no_live_services
def test_health_endpoints():
    r1 = requests.get(f"{FASTAPI_BASE}/health", timeout=5)
    assert r1.status_code == 200
    r2 = requests.get(f"{FLASK_BASE}/health", timeout=5)
    assert r2.status_code == 200


import uuid

@skip_if_no_live_services
def test_register_and_train_flow():
    unique_suffix = uuid.uuid4().hex[:6]
    env_name = f"CartPole-{unique_suffix}"
    exp_name = f"Exp-{unique_suffix}"

    # Register an environment
    env_payload = {"env_name": env_name, "version": "v1"}
    r = requests.post(f"{FASTAPI_BASE}/environments/", json=env_payload, timeout=5)
    assert r.status_code in (200, 201)

    # Create an experiment
    exp_payload = {"name": exp_name, "algo": "DQN"}
    r = requests.post(f"{FASTAPI_BASE}/experiments/", json=exp_payload, timeout=5)
    assert r.status_code in (200, 201)
    exp = r.json()
    exp_id = exp.get("id") or 1

    # Start training through Flask bridge
    train_payload = {"experiment_id": exp_id, "env_name": env_name, "algo": "DQN"}
    r = requests.post(f"{FLASK_BASE}/api/v1/start_training", json=train_payload, timeout=10)
    assert r.status_code == 200
    j = r.json()
    assert "task_id" in j or "status" in j


@skip_if_no_live_services
def test_metrics_endpoint_exposed():
    r = requests.get(f"{FASTAPI_BASE}/metrics/", timeout=5)
    assert r.status_code == 200
    assert "rl_experiments_active" in r.text
