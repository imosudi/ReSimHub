# Tier 1: Minimal / Local Development - First-Time User Manual

This manual provides an end-to-end operational guide for researchers and developers deploying **ReSimHub** in a **Tier 1: Minimal / Local Development** environment (2 to 4 CPU cores, 4 GB to 8 GB RAM, local SSD storage).

It covers all operational stages from initial repository configuration to final experiment evaluation, including complete sample JSON payloads, command-line inputs, and expected responses.

---

## Architecture Overview in Tier 1

In Tier 1, ReSimHub executes locally without requiring distributed container clusters:
- **FastAPI Control Plane**: Runs locally via Uvicorn on port `8000`.
- **Database**: Embedded SQLite database (`resimhub.db`).
- **Simulator Bridge**: High-throughput gRPC service on port `50051` (with transparent in-process fallback).
- **Storage**: Local directory paths (`storage/models/` and `storage/checkpoints/`).

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Tier 1 Local Workstation (Localhost)                 │
│                                                                        │
│   ┌───────────────────┐    REST / WebSocket     ┌──────────────────┐   │
│   │   REST Client     │ ──────────────────────> │ FastAPI Service  │   │
│   │ (curl / browser)  │                         │   (Port 8000)    │   │
│   └───────────────────┘                         └────────┬─────────┘   │
│                                                          │             │
│                ┌─────────────────────────────────────────┼──────────┐  │
│                │                                         │          │  │
│                ▼                                         ▼          ▼  │
│   ┌─────────────────────────┐                   ┌──────────────┐ ┌───┐ │
│   │ gRPC Simulator Bridge   │                   │ SQLite DB    │ │FS │ │
│   │ (Port 50051 / In-Proc)  │                   │(resimhub.db) │ └───┘ │
│   └─────────────────────────┘                   └──────────────┘       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Stage 1: Environment Setup and Initialisation

### 1.1 Clone Repository and Prepare Virtual Environment

```bash
git clone https://github.com/imosudi/ReSimHub.git
cd ReSimHub

# Create and activate Python 3.12 virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies including gRPC and Protobuf libraries
pip install -r requirements.txt
```

### 1.2 Initialise Storage Folders and Configuration

```bash
# Ensure local artifact directories exist
mkdir -p storage/models storage/checkpoints logs

# Create .env file configured for local SQLite execution
cat << 'EOF' > .env
APP_ENV=development
SECRET_KEY=local-dev-secret-key-32-chars-minimum
DATABASE_URL=sqlite:///./resimhub.db
LOG_FILE=logs/resimhub.log
PROMETHEUS_ENDPOINT=/metrics
GRPC_SIMULATOR_TARGET=127.0.0.1:50051
EOF
```

---

## Stage 2: Launching Backend Services

In Tier 1, open two terminal tabs (or run the gRPC server in the background):

### Tab 1: Start gRPC Simulator Bridge
```bash
source venv/bin/activate
python -m backend.grpc_service.server
```
*Expected log output:*
```
SimulatorBridge gRPC server active on 0.0.0.0:50051
```

### Tab 2: Start FastAPI Application
```bash
source venv/bin/activate
uvicorn backend.fastapi_app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Expected log output:*
```
INFO: Application startup complete.
INFO: Uvicorn running on http://127.0.0.1:8000
```

### 2.1 Verify Service Health
```bash
curl -s http://127.0.0.1:8000/health
```
**Expected Response:**
```json
{
  "status": "ok",
  "service": "backend fastapi service",
  "version": "0.7.0"
}
```

```bash
curl -s http://127.0.0.1:8000/simulator/health
```
**Expected Response:**
```json
{
  "status": "SERVING",
  "version": "1.0.0",
  "available_environments": [
    "CartPole-v1",
    "LunarLander-v2",
    "Pendulum-v1",
    "Acrobot-v1",
    "MountainCar-v0"
  ],
  "uptime_seconds": 12
}
```

---

## Stage 3: Registering a Simulation Environment

Every experiment requires a registered simulation environment entry.

### 3.1 Register `CartPole-v1`
```bash
curl -s -X POST http://127.0.0.1:8000/environments/ \
  -H "Content-Type: application/json" \
  -d '{
    "env_name": "CartPole-v1",
    "version": "v1"
  }'
```
**Expected Response:**
```json
{
  "id": 1,
  "env_name": "CartPole-v1",
  "version": "v1",
  "registered_at": "2026-10-04T13:00:00.000000"
}
```

---

## Stage 4: Creating an Experiment Record

An experiment groups training runs, algorithm hyperparameter choices, and evaluation metrics.

### 4.1 Create Experiment
```bash
curl -s -X POST http://127.0.0.1:8000/experiments/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CartPole-DQN-Baseline",
    "description": "Baseline Deep Q-Network trial on CartPole-v1 environment"
  }'
```
**Expected Response:**
```json
{
  "id": 1,
  "name": "CartPole-DQN-Baseline",
  "description": "Baseline Deep Q-Network trial on CartPole-v1 environment",
  "status": "CREATED",
  "created_at": "2026-10-04T13:01:00.000000"
}
```

---

## Stage 5: High-Throughput Stepping via Simulator Bridge

Before training, verify simulator interaction through the Protocol Buffers bridge.

### 5.1 Deterministic Environment Reset
```bash
curl -s -X POST http://127.0.0.1:8000/simulator/reset \
  -H "Content-Type: application/json" \
  -d '{
    "env_id": "CartPole-v1",
    "seed": 42,
    "options": {
      "difficulty": "standard"
    }
  }'
```
**Expected Response:**
```json
{
  "env_id": "CartPole-v1",
  "observation": [-0.0037, 0.0125, -0.0211, 0.0048],
  "info": {
    "initialised": "true",
    "seed": "42",
    "opt_difficulty": "standard"
  },
  "success": true
}
```

### 5.2 Execute Single Step Transition
```bash
curl -s -X POST http://127.0.0.1:8000/simulator/step \
  -H "Content-Type: application/json" \
  -d '{
    "env_id": "CartPole-v1",
    "action": 1,
    "is_discrete": true,
    "step_index": 1
  }'
```
**Expected Response:**
```json
{
  "env_id": "CartPole-v1",
  "observation": [-0.0034, 0.2078, -0.0209, -0.2861],
  "reward": 1.0,
  "done": false,
  "truncated": false,
  "info": {
    "step_count": "1",
    "env_id": "CartPole-v1",
    "cumulative_reward": "1.0"
  },
  "step_count": 1,
  "latency_ms": 0.042
}
```

### 5.3 Profile Stepping Throughput
```bash
curl -s -X POST http://127.0.0.1:8000/simulator/benchmark \
  -H "Content-Type: application/json" \
  -d '{
    "env_id": "CartPole-v1",
    "num_steps": 2000,
    "batch_size": 32
  }'
```
**Expected Response:**
```json
{
  "env_id": "CartPole-v1",
  "total_steps": 2000,
  "elapsed_seconds": 0.0185,
  "steps_per_second": 108108.1,
  "protocol": "gRPC/Protobuf",
  "mean_latency_ms": 0.0089
}
```

---

## Stage 6: Dispatching and Monitoring a Training Run

### 6.1 Dispatch Single-Agent Training Run
```bash
curl -s -X POST http://127.0.0.1:8000/orchestrate/train \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_id": 1,
    "env_name": "CartPole-v1",
    "algo": "DQN",
    "resume_epochs": 5
  }'
```
**Expected Response:**
```json
{
  "task_id": "task_e489a1c0",
  "status": "QUEUED",
  "queued_at": "2026-10-04T13:02:15.000000"
}
```

### 6.2 Dispatch Multi-Agent Batch Run (Parallel Scheduling)
To execute multiple agent trials concurrently:
```bash
curl -s -X POST http://127.0.0.1:8000/orchestrate/batch \
  -H "Content-Type: application/json" \
  -d '{
    "batch_name": "CartPole-MultiAgent-Sweep",
    "experiment_id": 1,
    "priority": 1,
    "agent_trials": [
      {
        "trial_name": "Trial-DQN-Seed10",
        "algo": "DQN",
        "env_name": "CartPole-v1",
        "seed": 10,
        "epochs": 5,
        "hyperparameters": {"learning_rate": 0.001, "gamma": 0.99}
      },
      {
        "trial_name": "Trial-PPO-Seed20",
        "algo": "PPO",
        "env_name": "CartPole-v1",
        "seed": 20,
        "epochs": 5,
        "hyperparameters": {"learning_rate": 0.0003, "clip_eps": 0.2}
      }
    ]
  }'
```
**Expected Response:**
```json
{
  "batch_id": "batch_7a2bf10d",
  "status": "QUEUED",
  "total_agents": 2,
  "submitted_at": "2026-10-04T13:03:00.000000"
}
```

### 6.3 Query Batch Status and Aggregate Metrics
```bash
curl -s http://127.0.0.1:8000/orchestrate/batch/batch_7a2bf10d
```

---

## Stage 7: Dynamic Model Checkpointing and Verification

ReSimHub automatically saves weight checkpoints during training, and also allows manual checkpoint registration.

### 7.1 Register Model Checkpoint
```bash
curl -s -X POST http://127.0.0.1:8000/checkpoints/ \
  -H "Content-Type: application/json" \
  -d '{
    "algo": "DQN",
    "env_name": "CartPole-v1",
    "epoch": 5,
    "experiment_id": 1,
    "step": 2500,
    "reward": 485.5,
    "loss": 0.0124,
    "version": "v1.0",
    "weights": {
      "layer1_weights": [0.12, -0.45, 0.78, 0.23],
      "layer2_weights": [-0.31, 0.88, 0.05, -0.19],
      "bias": [0.01, -0.02]
    },
    "hyperparameters": {
      "learning_rate": 0.001,
      "gamma": 0.99,
      "epsilon": 0.05
    }
  }'
```
**Expected Response:**
```json
{
  "checkpoint_id": "ckpt_8f19da21",
  "task_id": null,
  "experiment_id": 1,
  "algo": "DQN",
  "env_name": "CartPole-v1",
  "epoch": 5,
  "step": 2500,
  "reward": 485.5,
  "loss": 0.0124,
  "file_path": "~/Documents/dev/ReSimHub/storage/checkpoints/ckpt_8f19da21.pt",
  "file_size_bytes": 1024,
  "checksum": "a3b2c1d0e5f6...",
  "version": "v1.0",
  "is_best": true,
  "created_at": "2026-10-04T13:05:00.000000"
}
```

### 7.2 Inspect Top-Performing Policy Checkpoint
```bash
curl -s "http://127.0.0.1:8000/checkpoints/best?algo=DQN&env_name=CartPole-v1"
```

### 7.3 Load Weights and Verify Integrity
```bash
curl -s http://127.0.0.1:8000/checkpoints/ckpt_8f19da21/weights
```
**Expected Response:**
```json
{
  "checkpoint_id": "ckpt_8f19da21",
  "checksum_verified": true,
  "weights": {
    "layer1_weights": [0.12, -0.45, 0.78, 0.23],
    "layer2_weights": [-0.31, 0.88, 0.05, -0.19],
    "bias": [0.01, -0.02]
  }
}
```

---

## Stage 8: Policy Evaluation and Benchmarking

Evaluate the trained policy against standard benchmark trials.

### 8.1 Upload Trained Model Artifact
```bash
curl -s -X POST http://127.0.0.1:8000/benchmark/upload_model \
  -F "file=@docs/dqn_model.pkl"
```
**Expected Response:**
```json
{
  "model_id": "mdl_2538f16a",
  "status": "uploaded",
  "uploaded_at": "2026-10-04T13:08:00.000000",
  "filename": "dqn_model.pkl"
}
```

### 8.2 Execute Benchmark Run
```bash
curl -s -X POST http://127.0.0.1:8000/benchmark/run \
  -F "model_id=mdl_2538f16a" \
  -F "env_name=CartPole-v1" \
  -F "episodes=20"
```
**Expected Response:**
```json
{
  "model_id": "mdl_2538f16a",
  "env_name": "CartPole-v1",
  "mean_reward": 210.23,
  "std_reward": 25.02,
  "median_reward": 211.25,
  "min_reward": 162.09,
  "max_reward": 246.79,
  "iqm_reward": 210.26,
  "success_rate": 65.0,
  "cvar_reward": 169.57,
  "stability_score": 8.4,
  "latency_ms": 21.67,
  "total_episodes": 20,
  "status": "completed",
  "evaluated_at": "2026-10-04T13:08:15.000000"
}
```

### 8.3 Query Historical Benchmark Leaderboards
```bash
curl -s "http://127.0.0.1:8000/benchmark/recent?limit=5"
```

---

## Stage 9: Telemetry Analytics and Live Dashboard

### 9.1 Query Experiment Analytics
```bash
curl -s http://127.0.0.1:8000/analytics/experiment/1
```
**Expected Response:**
```json
{
  "experiment_id": 1,
  "total_runs": 1,
  "latest_accuracy": 0.985,
  "latest_reward": 492.3,
  "mean_reward": 492.3,
  "status": "SUCCESS"
}
```

### 9.2 Inspect WebSocket Dashboard
Open your web browser and navigate to:
```
http://127.0.0.1:8000/dashboard
```
Features available in Tier 1:
- **Live Training Visualiser**: WebSocket streaming on `/ws/live-train`.
- **Telemetry Gauge**: Real-time snapshots on `/ws/live-metrics`.
- **Batch Inspector**: Parallel batch telemetry on `/ws/batch/{batch_id}`.

---

## Stage 10: Training Resumption and Conclusion

### 10.1 Dynamically Resume Training from Checkpoint
Resume the policy training for an additional 5 epochs:
```bash
curl -s -X POST http://127.0.0.1:8000/checkpoints/ckpt_8f19da21/resume \
  -H "Content-Type: application/json" \
  -d '{
    "resume_epochs": 5
  }'
```
**Expected Response:**
```json
{
  "task_id": "task_c910a28f",
  "checkpoint_id": "ckpt_8f19da21",
  "algo": "DQN",
  "env_name": "CartPole-v1",
  "start_epoch": 5,
  "target_epochs": 10,
  "status": "QUEUED",
  "resumed_at": "2026-10-04T13:12:00.000000"
}
```

### 10.2 Review Persisted Audit Records
```bash
curl -s "http://127.0.0.1:8000/orchestrate/tasks?limit=10"
```

---

## Automated Walkthrough Script

An automated Python script executing all 10 stages sequentially is available at [`scripts/run_tier1_walkthrough.py`](../scripts/run_tier1_walkthrough.py) (located at `~/Documents/dev/ReSimHub/scripts/run_tier1_walkthrough.py`).

To execute the complete lifecycle in a single command:
```bash
source venv/bin/activate
python scripts/run_tier1_walkthrough.py
```
This script initialises the environment, registers models, steps simulators, saves checkpoints, verifies cryptographic integrity, runs benchmark evaluations, and outputs a formatted terminal report.
