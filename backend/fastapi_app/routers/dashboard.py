# backend/fastapi_app/routers/dashboard.py
import asyncio
import json
import random
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from backend.fastapi_app.services.progress_broadcast import get_broadcast_service
from shared.utils.logger import get_logger

log = get_logger("DashboardRouter")
router = APIRouter(tags=["Visualisation & Dashboard"])

broadcast_service = get_broadcast_service()
TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "dashboard.html"


# -------------------------------------------------------------------------
# 🖥️ Interactive Web Dashboard
# -------------------------------------------------------------------------
@router.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    """
    Renders the ReSimHub real-time RL visualizer & benchmarking dashboard.
    """
    if TEMPLATE_PATH.exists():
        html_content = TEMPLATE_PATH.read_text(encoding="utf-8")
    else:
        html_content = "<h1>Dashboard template not found</h1>"
    return HTMLResponse(content=html_content)


# -------------------------------------------------------------------------
# 📡 WebSocket: Task Progress Stream (/ws/tasks/{task_id})
# -------------------------------------------------------------------------
@router.websocket("/ws/tasks/{task_id}")
async def websocket_task_progress(websocket: WebSocket, task_id: str):
    """
    Subscribes to live progress updates for an arbitrary Celery or training task.
    Streams events as JSON messages over WebSocket.
    """
    await websocket.accept()
    log.info(f"WebSocket client connected to /ws/tasks/{task_id}")

    # Initial acknowledgement
    await websocket.send_json({
        "event": "connected",
        "task_id": task_id,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "LISTENING"
    })

    stop_event = asyncio.Event()

    async def incoming_listener():
        try:
            while not stop_event.is_set():
                data = await websocket.receive_text()
                try:
                    payload = json.loads(data)
                    action = payload.get("action")
                    if action == "ping":
                        await websocket.send_json({"action": "pong", "timestamp": datetime.utcnow().isoformat()})
                except Exception:
                    pass
        except WebSocketDisconnect:
            stop_event.set()
        except Exception:
            stop_event.set()

    async def stream_broadcaster():
        try:
            async for message in broadcast_service.subscribe(task_id):
                if stop_event.is_set():
                    break
                await websocket.send_text(message)
        except WebSocketDisconnect:
            stop_event.set()
        except Exception as exc:
            log.warning(f"Error streaming to websocket for task {task_id}: {exc}")
            stop_event.set()

    listener_task = asyncio.create_task(incoming_listener())
    broadcaster_task = asyncio.create_task(stream_broadcaster())

    # Wait until either disconnects
    done, pending = await asyncio.wait(
        [listener_task, broadcaster_task],
        return_when=asyncio.FIRST_COMPLETED
    )
    for t in pending:
        t.cancel()

    log.info(f"WebSocket client disconnected from /ws/tasks/{task_id}")


# -------------------------------------------------------------------------
# ⚡ WebSocket: Interactive Live Training Simulation (/ws/live-train)
# -------------------------------------------------------------------------
@router.websocket("/ws/live-train")
async def websocket_live_training(websocket: WebSocket):
    """
    Allows clients to interactively trigger and monitor a live reinforcement
    learning training process with simulated real-time policy convergence,
    reward progressions, losses, and exploration decay.
    """
    await websocket.accept()
    log.info("Client connected to /ws/live-train")

    training_active = False
    active_train_task: Optional[asyncio.Task] = None

    async def run_training_loop(algo: str, env: str, epochs: int, experiment_id: int):
        nonlocal training_active
        training_active = True
        task_id = f"sim_{experiment_id}_{int(datetime.utcnow().timestamp())}"

        base_reward = random.uniform(80, 120)
        target_reward = random.uniform(220, 260)
        current_loss = round(random.uniform(1.2, 2.5), 4)
        current_eps = 1.0

        await websocket.send_json({
            "event": "training_started",
            "task_id": task_id,
            "experiment_id": experiment_id,
            "algo": algo,
            "env": env,
            "total_epochs": epochs,
            "status": "RUNNING",
            "timestamp": datetime.utcnow().isoformat()
        })

        for epoch in range(1, epochs + 1):
            if not training_active:
                break

            await asyncio.sleep(0.4)  # Simulate step / epoch compute duration

            # Realistic RL progression curves:
            progress_ratio = epoch / epochs
            # Sigmoid / asymptotic reward gain with gaussian noise
            gain = (target_reward - base_reward) * (1 - (1 - progress_ratio) ** 2)
            noise = random.gauss(0, 7.5)
            epoch_reward = round(max(10.0, base_reward + gain + noise), 2)

            # Decay loss and epsilon
            current_loss = round(max(0.015, current_loss * random.uniform(0.85, 0.95)), 4)
            current_eps = round(max(0.05, 1.0 - progress_ratio * 0.95), 3)

            epoch_payload = {
                "event": "epoch_progress",
                "task_id": task_id,
                "experiment_id": experiment_id,
                "algo": algo,
                "env": env,
                "epoch": epoch,
                "total_epochs": epochs,
                "reward": epoch_reward,
                "loss": current_loss,
                "epsilon": current_eps,
                "status": "PROGRESS",
                "timestamp": datetime.utcnow().isoformat()
            }

            await websocket.send_json(epoch_payload)
            # Also notify any task listeners subscribed to broadcast_service
            await broadcast_service.publish(task_id, epoch_payload)

        if training_active:
            final_accuracy = round(random.uniform(0.88, 0.99), 4)
            finish_payload = {
                "event": "training_completed",
                "task_id": task_id,
                "experiment_id": experiment_id,
                "algo": algo,
                "env": env,
                "status": "SUCCESS",
                "final_accuracy": final_accuracy,
                "completed_at": datetime.utcnow().isoformat()
            }
            await websocket.send_json(finish_payload)
            await broadcast_service.publish(task_id, finish_payload)
            training_active = False

    try:
        while True:
            text = await websocket.receive_text()
            try:
                cmd = json.loads(text)
                action = cmd.get("action")

                if action == "start":
                    if active_train_task and not active_train_task.done():
                        active_train_task.cancel()

                    algo = cmd.get("algo", "PPO")
                    env = cmd.get("env", "CartPole-v1")
                    epochs = int(cmd.get("epochs", 15))
                    exp_id = int(cmd.get("experiment_id", 101))

                    active_train_task = asyncio.create_task(run_training_loop(algo, env, epochs, exp_id))

                elif action == "stop":
                    training_active = False
                    if active_train_task and not active_train_task.done():
                        active_train_task.cancel()
                    await websocket.send_json({"event": "training_stopped", "status": "STOPPED"})

                elif action == "ping":
                    await websocket.send_json({"action": "pong"})

            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON message format"})

    except WebSocketDisconnect:
        training_active = False
        if active_train_task and not active_train_task.done():
            active_train_task.cancel()
        log.info("Client disconnected from /ws/live-train")


# -------------------------------------------------------------------------
# 📊 WebSocket: Live Cluster & Telemetry Stream (/ws/live-metrics)
# -------------------------------------------------------------------------
@router.websocket("/ws/live-metrics")
async def websocket_live_metrics(websocket: WebSocket):
    """
    Emits real-time cluster metrics, active experiments gauge, and latency
    measurements periodically to connected dashboards.
    """
    await websocket.accept()
    log.info("Dashboard connected to /ws/live-metrics")

    try:
        while True:
            # Gauge snapshot (can read from prometheus or internal stats)
            snapshot = {
                "timestamp": datetime.utcnow().isoformat(),
                "active_experiments": random.choice([2, 3, 4]),
                "completed_training": random.choice([5, 6, 7]),
                "avg_latency_ms": round(23.5 + random.uniform(-1.5, 2.0), 2),
                "broker": "CONNECTED",
                "uptime": "operational"
            }
            await websocket.send_json(snapshot)
            await asyncio.sleep(2.5)
    except WebSocketDisconnect:
        log.info("Client disconnected from /ws/live-metrics")
    except Exception as exc:
        log.warning(f"Error in /ws/live-metrics stream: {exc}")
