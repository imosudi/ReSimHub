# tests/test_integration.py
import time
import requests

FASTAPI_BASE = "http://127.0.0.1:8000"
FLASK_BASE = "http://127.0.0.1:5000"

def test_health_endpoints():
    r1 = requests.get(f"{FASTAPI_BASE}/health", timeout=5)
    assert r1.status_code == 200
    r2 = requests.get(f"{FLASK_BASE}/health", timeout=5)
    assert r2.status_code == 200

def test_register_and_train_flow():
    # Register an environment
    env_payload = {"env_name": "CartPole-v1", "version": "v1"}
    r = requests.post(f"{FASTAPI_BASE}/environments/", json=env_payload, timeout=5)
    assert r.status_code in (200, 201)

    # Create an experiment
    exp_payload = {"name": "CartPole-v1", "algo": "DQN"}
    r = requests.post(f"{FASTAPI_BASE}/experiments/", json=exp_payload, timeout=5)
    assert r.status_code in (200, 201)
    exp = r.json()
    exp_id = exp.get("id") or 1

    # Start training through Flask bridge
    train_payload = {"experiment_id": exp_id, "env_name": "CartPole-v1", "algo": "DQN"}
    r = requests.post(f"{FLASK_BASE}/api/v1/start_training", json=train_payload, timeout=10)
    assert r.status_code == 200
    j = r.json()
    assert "task_id" in j or "status" in j

def test_metrics_endpoint_exposed():
    r = requests.get(f"{FASTAPI_BASE}/metrics/", timeout=5)
    assert r.status_code == 200
    assert "rl_experiments_active" in r.text
