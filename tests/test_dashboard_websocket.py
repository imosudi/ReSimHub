"""
tests/test_dashboard_websocket.py
---------------------------------
Validates the ReSimHub real-time visualisation dashboard and WebSocket
streaming endpoints:
  - GET /dashboard (HTML interface)
  - WebSocket /ws/tasks/{task_id} (arbitrary task streaming)
  - WebSocket /ws/live-train (interactive training simulation)
  - WebSocket /ws/live-metrics (telemetry stream)
"""

import json
import asyncio
import pytest
from fastapi.testclient import TestClient

from backend.fastapi_app.main import app
from backend.fastapi_app.services.progress_broadcast import get_broadcast_service


client = TestClient(app)


def test_dashboard_endpoint_html():
    """Verify that the /dashboard route serves the interactive HTML interface."""
    response = client.get("/dashboard")
    assert response.status_code == 200, f"Unexpected status: {response.status_code}"
    assert "text/html" in response.headers.get("content-type", "")
    assert "ReSimHub" in response.text
    assert "rewardChart" in response.text
    assert "benchmarkChart" in response.text
    assert "live-train" in response.text


def test_websocket_task_progress_stream():
    """Verify WebSocket connection and message subscription for a specific task."""
    task_id = "test_celery_task_42"
    broadcaster = get_broadcast_service()

    with client.websocket_connect(f"/ws/tasks/{task_id}") as websocket:
        # Initial greeting / connection event
        init_data = websocket.receive_json()
        assert init_data.get("event") == "connected"
        assert init_data.get("task_id") == task_id

        # Test ping / pong
        websocket.send_text(json.dumps({"action": "ping"}))
        pong_data = websocket.receive_json()
        assert pong_data.get("action") == "pong"

        # Publish a simulated Celery progress event to the broadcaster
        test_payload = {
            "task_id": task_id,
            "status": "PROGRESS",
            "epoch": 3,
            "total_epochs": 5,
            "reward": 218.4
        }
        asyncio.run(broadcaster.publish(task_id, test_payload))

        # WebSocket should receive the published message
        msg_text = websocket.receive_text()
        received_data = json.loads(msg_text)
        assert received_data.get("epoch") == 3
        assert received_data.get("reward") == 218.4
        assert received_data.get("status") == "PROGRESS"


def test_websocket_live_training_simulation():
    """Verify interactive live training control and streaming over WebSocket."""
    with client.websocket_connect("/ws/live-train") as websocket:
        # Trigger training run with 2 epochs for fast test execution
        cmd = {
            "action": "start",
            "algo": "PPO",
            "env": "CartPole-v1",
            "epochs": 2,
            "experiment_id": 888
        }
        websocket.send_text(json.dumps(cmd))

        # 1. Expect training_started
        start_event = websocket.receive_json()
        assert start_event.get("event") == "training_started"
        assert start_event.get("algo") == "PPO"
        assert start_event.get("total_epochs") == 2

        # 2. Expect epoch 1 progress
        ep1 = websocket.receive_json()
        assert ep1.get("event") == "epoch_progress"
        assert ep1.get("epoch") == 1
        assert "reward" in ep1
        assert "loss" in ep1

        # 3. Expect epoch 2 progress
        ep2 = websocket.receive_json()
        assert ep2.get("event") == "epoch_progress"
        assert ep2.get("epoch") == 2

        # 4. Expect training_completed
        completion = websocket.receive_json()
        assert completion.get("event") == "training_completed"
        assert completion.get("status") == "SUCCESS"
        assert "final_accuracy" in completion


def test_websocket_live_metrics():
    """Verify /ws/live-metrics emits telemetry snapshots."""
    with client.websocket_connect("/ws/live-metrics") as websocket:
        snapshot = websocket.receive_json()
        assert "active_experiments" in snapshot
        assert "completed_training" in snapshot
        assert "avg_latency_ms" in snapshot
        assert snapshot["broker"] == "CONNECTED"
