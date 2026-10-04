

# ![alt text](ReSimHub_mini_icon.svg) ReSimHub
![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-async-green?logo=fastapi)
![Flask](https://img.shields.io/badge/Flask-sync-lightgrey?logo=flask)
![Celery](https://img.shields.io/badge/Celery-distributed-yellowgreen?logo=celery)
![Redis](https://img.shields.io/badge/Redis-message--broker-red?logo=redis)
![Pandas](https://img.shields.io/badge/Pandas-DataFrame--Analytics-150458?logo=pandas)
![NumPy](https://img.shields.io/badge/NumPy-Scientific%20Computing-blue?logo=numpy)
![Stage](https://img.shields.io/badge/Stage-6%20%2F%208%20--%20Benchmarking-orange)
![Status](https://img.shields.io/badge/Status-Active-success)
![License](https://img.shields.io/badge/License-BSD%203--Clause-blue)


**ReSimHub** is a **scalable, research-grade backend framework** designed for **reinforcement learning (RL)** experimentation, simulation, and benchmarking.  
It provides **RESTful** and **asynchronous APIs** for managing **simulation environments**, **training orchestration**, and **agent evaluation**, all optimised for distributed systems and reproducible research.

> Built for modern RL pipelines, where **experimentation**, **asynchronous training**, and **performance evaluation** converge.

---

## Key Features

- **Hybrid Flask-FastAPI Framework**: Combines Flask’s flexibility with FastAPI’s async capabilities.
- **Experiment Management APIs**: Create, register, and manage experiments programmatically.
- **Distributed Orchestration**: Scalable Celery + Redis job queues for RL training workloads.
- **Data Processing Layer**: NumPy/Pandas-powered analytics for logs, metrics, and benchmarking.
- **Unified API Gateway**: Seamless bridge between Flask and FastAPI services.
- **Evaluation & Benchmarking APIs**: Compare and score RL agents using consistent metrics.
- **Observability Stack**: Prometheus and Grafana integration for monitoring.
- **Containerised Deployment**: Docker- and Kubernetes-ready for research clusters.

---

## Development Roadmap

| **Stage** | **Focus Area** | **Objective** |
|:-----------|:----------------|:---------------|
| **Stage 1** | Project Bootstrap | Initialise structure, dependencies, hybrid Flask-FastAPI framework, and CI pipeline. |
| **Stage 2** | Core Experimentation APIs | Create experiment management, environment registration, and metadata models. |
| **Stage 3** | Async Orchestration | Integrate Celery + Redis for distributed training tasks. |
| **Stage 4** | Data Processing Layer | Add NumPy/Pandas-powered services for results and benchmarking. |
| **Stage 5** | Flask-FastAPI Bridge | Implement communication bridge and unified API gateway. |
| **Stage 6** | Evaluation & Benchmarking APIs | Develop endpoints for agent evaluation and comparative benchmarking. |
| **Stage 7** | Observability & Persistence | Integrate DB persistence, monitoring, and structured logging. |
| **Stage 8** | End-to-End Test & Deployment | Containerise, test, and deploy with Docker/Kubernetes. |

---

## Architecture Overview

```
                        ┌──────────────────────────────┐
                        │        REST Clients          │
                        └─────────────┬────────────────┘
                                      │
                                      │
          ┌───────────────────────────┼───────────────────────────────┐
          │                           │                               │
          │                           │                               │
  ┌───────▼────────┐        ┌─────────▼────────┐            ┌─────────▼─────────┐
  │    Flask API   │ ◄────► │ FastAPI Core     │ ◄─────────►│ Benchmarking API  │
  │ (Legacy/Sync)  │        │ (Async Gateway)  │            │ (Model Eval Layer)│
  └───────┬────────┘        └─────────┬────────┘            └─────────┬─────────┘
          │                           │                               │
          │                           │                               │
  ┌───────▼────────┐          ┌────────▼────────┐             ┌────────▼─────────┐
  │ Celery Workers │◄────────►│ Evaluation Queue│◄────────────│ Model Uploads    │
  │ (Distributed)  │          │ (Redis MQ)      │             │ & Orchestration  │
  └───────┬────────┘          └─────────────────┘             └──────────────────┘
          │
          │
    ┌─────▼──────┐              ┌───────────────┐        ┌────────────────────┐
    │ PostgreSQL │◄────────────►│ Redis Cache   │◄──────►│ Prometheus/Grafana │
    └────────────┘              └───────────────┘        └────────────────────┘

```

---

## Service Communication Flow

```
                 ┌────────────────────────────────────────────────────┐
                 │                    REST Clients                    │
                 │        (curl, Postman, Frontend, Notebooks)        │
                 └───────────────────────┬────────────────────────────┘
                                         │
                                         ▼
                          ┌──────────────────────────────┐
                          │       FastAPI Service        │
                          │ (Async REST + Training API)  │
                          └──────────────┬───────────────┘
                                         │
                                         ▼
                     ┌──────────────────────────────────────────┐
                     │           Benchmarking API               │
                     │ (Model Uploads + Eval Orchestration)     │
                     └───────────────────┬──────────────────────┘
                                         │
                                         ▼
                         ┌────────────────────────────────┐
                         │         Celery Workers         │
                         │ (Distributed RL orchestration) │
                         └───────────────┬────────────────┘
                                         │
                                         ▼
                         ┌───────────────────────────────┐
                         │          Redis MQ             │
                         │ (Job Queue + Task Results)    │
                         └───────────────────────────────┘
                                         │
   ┌────────────────────┐                │                 ┌────────────────────┐
   │   Flask Service    │◄───────────────┘────────────────►│   PostgreSQL DB    │
   │ (Frontend Gateway) │                │                 │ (Experiment Store) │
   └────────────────────┘                │                 └────────────────────┘
                                         │
                                         ▼
                         ┌───────────────────────────────┐
                         │   Prometheus / Grafana Stack  │
                         │   (Observability & Metrics)   │
                         └───────────────────────────────┘

```

---
## Installation

### Prerequisites

- Python **3.10+**
- Docker & Docker Compose (optional)
- Redis & PostgreSQL instances (local or containerised)

### Clone the Repository

```bash
git clone https://github.com/imosudi/ReSimHub.git
cd ReSimHub
```

### Setup Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```bash
# Flask & FastAPI
APP_ENV=development
SECRET_KEY=changeme

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/resimhub

# Redis & Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}
```

---

## Running the Project

### Run Flask & FastAPI Services

```bash
# In separate terminals
python backend/main.py 

uvicorn backend.fastapi_app.main:app --reload --port 8000
```

or, with Docker:

```bash
docker-compose up --build
```

### Launch Celery Workers

```bash
celery -A backend.fastapi_app.services.orchestrator.celery_app worker --loglevel=info
```

---

## Example Usage


---

### Register an Environment
```bash
curl -X POST http://localhost:8000/api/environments \
     -H "Content-Type: application/json" \
     -d '{"env_name": "CartPole-v1", "version": "v1"}'
```
**Output**
```json
{"id":1,"env_name":"CartPole-v1","version":"v1","registered_at":"2025-10-29T06:00:00"}
```

---

### Create a New Experiment
```bash
curl -X POST http://localhost:8000/api/experiments \
     -H "Content-Type: application/json" \
     -d '{"name": "CartPole-v1", "agent": "DQN", "episodes": 500}'
```
**Output**
```json
{"id":1,"name":"CartPole-v1","agent":"DQN","episodes":500,"status":"created","created_at":"2025-10-29T06:01:00"}
```

---

### Launch Training via Flask Proxy
```bash
curl -X POST http://localhost:5000/api/v1/start_training \
     -H "Content-Type: application/json" \
     -d '{"experiment_id": 1, "env_name": "CartPole-v1", "algo": "DQN"}'
```
**Output**
```json
{
  "queued_at": "2025-10-30T06:07:06.472880",
  "status": "queued",
  "task_id": "9821142c-3450-4bba-84af-7df037705bb6"
}
```

---

### Retrieve Analytics for All Experiments
```bash
curl http://127.0.0.1:5000/api/v1/analytics/recent
```
**Output**
```json
{
  "summary": {
    "total_experiments": 3,
    "avg_reward": 182.4,
    "avg_duration": 47.2
  },
  "experiments": [
    {"id":1,"agent":"DQN","avg_reward":190.2},
    {"id":2,"agent":"PPO","avg_reward":176.0},
    {"id":3,"agent":"A2C","avg_reward":181.0}
  ]
}
```

---

### Retrieve Analytics for a Specific Experiment (experiment_id: 1)
```bash
curl http://127.0.0.1:5000/api/v1/analytics/experiment/1
```
**Output**
```json
{
  "experiment_id":1,
  "agent":"DQN",
  "avg_reward":190.2,
  "episodes":500,
  "status":"completed"
}
```

---

### Upload a Model (multipart/form-data)
```bash
# upload sample model ReSimHub/docs/dqn_model.pkl
# replace with actual intended model path
curl -F "file=@docs/dqn_model.pkl" \
     http://127.0.0.1:8000/benchmark/upload_model
```
**Output**
```json
{
  "model_id": "mdl_afdbb795",
  "status": "uploaded",
  "uploaded_at": "2025-10-30T14:16:26.241943"
}
```

---

### Simulate Evaluation of an Uploaded Model
```bash
curl -X POST http://127.0.0.1:8000/benchmark/run \
     -F "model_id=mdl_afdbb795" \
     -F "env_name=CartPole-v1" \
     -F "episodes=50"
```
**Output**
```json
{
  "model_id": "mdl_afdbb795",
  "env_name": "CartPole-v1",
  "mean_reward": 203.68,
  "std_reward": 34.65,
  "median_reward": 204.18,
  "min_reward": 142.10,
  "max_reward": 278.40,
  "iqm_reward": 202.95,
  "success_rate": 86.0,
  "cvar_reward": 151.32,
  "stability_score": 5.88,
  "latency_ms": 26.02,
  "total_episodes": 50,
  "status": "completed",
  "evaluated_at": "2025-10-30T14:23:19.748328"
}
```

---

### List Recent Benchmark Results (Redis Cache / Disk)
```bash
curl http://127.0.0.1:8000/benchmark/recent
```
**Output**
```json
{
  "count": 2,
  "results": [
    {
      "model_id": "mdl_afdbb795",
      "env_name": "CartPole-v1",
      "mean_reward": 203.68,
      "std_reward": 34.65,
      "median_reward": 204.18,
      "min_reward": 142.10,
      "max_reward": 278.40,
      "iqm_reward": 202.95,
      "success_rate": 86.0,
      "cvar_reward": 151.32,
      "stability_score": 5.88,
      "latency_ms": 26.02,
      "total_episodes": 50,
      "status": "completed",
      "evaluated_at": "2025-10-30T14:23:19.748328"
    }
  ]
}
```

---

### Query Historical Benchmarks from Database (Paginated)
```bash
curl "http://127.0.0.1:8000/benchmark/history?model_id=mdl_afdbb795&limit=20&offset=0"
```
**Output**
```json
{
  "total": 1,
  "limit": 20,
  "offset": 0,
  "results": [
    {
      "id": 1,
      "model_id": "mdl_afdbb795",
      "env_name": "CartPole-v1",
      "mean_reward": 203.68,
      "std_reward": 34.65,
      "median_reward": 204.18,
      "min_reward": 142.10,
      "max_reward": 278.40,
      "iqm_reward": 202.95,
      "success_rate": 86.0,
      "cvar_reward": 151.32,
      "stability_score": 5.88,
      "latency_ms": 26.02,
      "total_episodes": 50,
      "status": "completed",
      "evaluated_at": "2025-10-30T14:23:19.748328"
    }
  ]
}
```

---

### Inspect Model Metadata & Top Evaluation Score
```bash
curl "http://127.0.0.1:8000/benchmark/model/mdl_afdbb795"
```
**Output**
```json
{
  "model_id": "mdl_afdbb795",
  "filename": "dqn_cartpole.pkl",
  "size_bytes": 1024,
  "uploaded_at": "2025-10-30T14:16:26.241943",
  "top_score": 203.68,
  "top_score_env": "CartPole-v1",
  "total_benchmarks": 1
}
```

---

### Query Training Run Records & Orchestrator Tasks (DB Persisted)
```bash
curl "http://127.0.0.1:8000/orchestrate/tasks?status=COMPLETED&limit=10"
```
**Output**
```json
{
  "total": 1,
  "tasks": [
    {
      "task_id": "sim_exp1_1729000000",
      "experiment_id": "exp1",
      "algo": "PPO",
      "env_name": "CartPole-v1",
      "status": "COMPLETED",
      "current_epoch": 15,
      "total_epochs": 15,
      "latest_reward": 248.5,
      "latest_loss": 0.021,
      "created_at": "2025-10-30T14:10:00.000000",
      "completed_at": "2025-10-30T14:10:30.000000"
    }
  ]
}
```

---

### Compare Models
```bash
curl "http://127.0.0.1:8000/benchmark/compare?model_ids=mdl_afdbb795,mdl_12345678&env=CartPole-v1"
```
**Output**
```json
{
  "count": 1,
  "comparison": [
    {
      "model_id": "mdl_afdbb795",
      "env_name": "CartPole-v1",
      "mean_reward": 204.06,
      "std_reward": 31.64,
      "median_reward": 197.33,
      "min_reward": 150.2,
      "max_reward": 280.1,
      "iqm_reward": 203.4,
      "success_rate": 88.0,
      "cvar_reward": 155.0,
      "stability_score": 6.45,
      "latency_ms": 25.53,
      "total_episodes": 50,
      "status": "completed",
      "evaluated_at": "2025-10-30T14:32:39.036548"
    }
  ]
}
```

---

### Multi-Agent Parallel Batch Scheduling
Schedule a batch of diverse agent trials (DQN, PPO, SAC, A2C) with distinct seeds and hyperparameters to run concurrently across Celery workers:

```bash
curl -X POST http://127.0.0.1:8000/orchestrate/batch \
     -H "Content-Type: application/json" \
     -d '{
       "name": "CartPole Multi-Agent Parallel Sweep",
       "env_name": "CartPole-v1",
       "priority": 7,
       "agents": [
         {"algo": "DQN", "seed": 101, "total_epochs": 5, "hyperparameters": {"learning_rate": 0.001}},
         {"algo": "PPO", "seed": 202, "total_epochs": 5, "hyperparameters": {"clip_ratio": 0.2}},
         {"algo": "SAC", "seed": 303, "total_epochs": 5, "hyperparameters": {"tau": 0.005}}
       ]
     }'
```
**Output**
```json
{
  "batch_id": "batch_9a2f1c84",
  "name": "CartPole Multi-Agent Parallel Sweep",
  "env_name": "CartPole-v1",
  "status": "SCHEDULED",
  "total_trials": 3,
  "task_ids": [
    "c8a14b0e-9273-42e1-b4d2-f54215ad9001",
    "d7e29a1b-1038-41c3-8f01-e83719bc4229",
    "b3f912c0-7719-4822-9df1-a20188bc3104"
  ],
  "scheduled_at": "2026-10-04T10:30:00.000000"
}
```

---

### Query Multi-Agent Batch Status & Aggregate Metrics
Inspect real-time consolidated status, trial progression, and mathematical metric aggregation (mean, maximum, and minimum rewards):

```bash
curl http://127.0.0.1:8000/orchestrate/batch/batch_9a2f1c84
```
**Output**
```json
{
  "batch_id": "batch_9a2f1c84",
  "name": "CartPole Multi-Agent Parallel Sweep",
  "env_name": "CartPole-v1",
  "status": "COMPLETED",
  "total_trials": 3,
  "completed_trials": 3,
  "failed_trials": 0,
  "priority": 7,
  "created_at": "2026-10-04T10:30:00.000000",
  "completed_at": "2026-10-04T10:30:15.000000",
  "trials": [
    {
      "trial_id": "trial_d14e02",
      "task_id": "c8a14b0e-9273-42e1-b4d2-f54215ad9001",
      "algo": "DQN",
      "seed": 101,
      "status": "SUCCESS",
      "current_epoch": 5,
      "total_epochs": 5,
      "latest_reward": 218.4,
      "final_accuracy": 0.9412
    },
    {
      "trial_id": "trial_f82a19",
      "task_id": "d7e29a1b-1038-41c3-8f01-e83719bc4229",
      "algo": "PPO",
      "seed": 202,
      "status": "SUCCESS",
      "current_epoch": 5,
      "total_epochs": 5,
      "latest_reward": 235.1,
      "final_accuracy": 0.9634
    },
    {
      "trial_id": "trial_b77e30",
      "task_id": "b3f912c0-7719-4822-9df1-a20188bc3104",
      "algo": "SAC",
      "seed": 303,
      "status": "SUCCESS",
      "current_epoch": 5,
      "total_epochs": 5,
      "latest_reward": 242.8,
      "final_accuracy": 0.9821
    }
  ],
  "summary_metrics": {
    "avg_reward": 232.1,
    "max_reward": 242.8,
    "min_reward": 218.4,
    "active_trials": 0,
    "completed_trials": 3
  }
}
```

---

### List Multi-Agent Batch Schedules (Paginated)
```bash
curl "http://127.0.0.1:8000/orchestrate/batches?limit=10&offset=0"
```
**Output**
```json
{
  "total": 1,
  "batches": [
    {
      "batch_id": "batch_9a2f1c84",
      "name": "CartPole Multi-Agent Parallel Sweep",
      "env_name": "CartPole-v1",
      "status": "COMPLETED",
      "total_trials": 3,
      "completed_trials": 3,
      "failed_trials": 0,
      "priority": 7
    }
  ]
}
```

---

### Stream Batch Telemetry via WebSocket
Connect directly to `/ws/batch/{batch_id}` for live event streaming from Celery workers:

```javascript
const ws = new WebSocket("ws://127.0.0.1:8000/ws/batch/batch_9a2f1c84");
ws.onmessage = (event) => {
  const telemetry = JSON.parse(event.data);
  console.log("Live trial update:", telemetry);
};
```

---

### Model Checkpointing & Artifact Versioning
Capture, verify, and restore model weight snapshots dynamically during or after training:

#### 1. Save or Register a Model Checkpoint
```bash
curl -X POST http://127.0.0.1:8000/checkpoints \
     -H "Content-Type: application/json" \
     -d '{
       "algo": "PPO",
       "env_name": "CartPole-v1",
       "epoch": 5,
       "step": 2500,
       "reward": 248.5,
       "loss": 0.021,
       "version": "v1.0",
       "weights": {
         "policy.fc1.weight": [[0.15, -0.22], [0.41, -0.63]],
         "policy.fc1.bias": [0.01, -0.01],
         "optimiser.lr": 0.0003
       },
       "hyperparameters": {"clip_ratio": 0.2, "gamma": 0.99}
     }'
```
**Output**
```json
{
  "checkpoint_id": "ckpt_8f19da21",
  "algo": "PPO",
  "env_name": "CartPole-v1",
  "epoch": 5,
  "step": 2500,
  "reward": 248.5,
  "loss": 0.021,
  "file_path": "storage/checkpoints/manual/ckpt_8f19da21_v1.0.pt",
  "file_size_bytes": 384,
  "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "version": "v1.0",
  "is_best": true,
  "created_at": "2026-10-04T12:00:00.000000"
}
```

#### 2. Inspect Weights & Verify SHA-256 Checksum
```bash
curl http://127.0.0.1:8000/checkpoints/ckpt_8f19da21/weights
```

#### 3. Fetch Top-Performing Checkpoint
```bash
curl "http://127.0.0.1:8000/checkpoints/best?algo=PPO&env_name=CartPole-v1"
```

#### 4. Resume Training Dynamically from Checkpoint
```bash
curl -X POST http://127.0.0.1:8000/checkpoints/ckpt_8f19da21/resume \
     -H "Content-Type: application/json" \
     -d '{
       "resume_epochs": 5,
       "override_hyperparameters": {"learning_rate": 0.0001}
     }'
```
**Output**
```json
{
  "task_id": "task_a928e104",
  "checkpoint_id": "ckpt_8f19da21",
  "algo": "PPO",
  "env_name": "CartPole-v1",
  "start_epoch": 5,
  "target_epochs": 10,
  "status": "QUEUED",
  "resumed_at": "2026-10-04T12:05:00.000000"
}
```

---

### High-Throughput gRPC & Protocol Buffers Simulator Bridge

ReSimHub provides a high-throughput, low-latency gRPC and Protocol Buffers interface enabling efficient communication between RL agent runners and simulation environments. This architecture eliminates HTTP and JSON serialisation overhead, supporting sub-millisecond stepping, observation streaming, and vectorised batch stepping across distributed workers.

#### 1. Protocol Buffers Schema (`shared/proto/simulator.proto`)

The interface defines strongly-typed messages and RPC methods:
- **`CheckHealth`**: Queries service operational status and supported environments (`CartPole-v1`, `LunarLander-v2`, `Pendulum-v1`, `Acrobot-v1`).
- **`Reset`**: Initialises or resets an environment with optional random seed and configuration parameters.
- **`Step`**: Executes a single transition step with discrete action integer or continuous action vector.
- **`BatchStep`**: Vectorised batch stepping executing multiple environment transitions concurrently.
- **`StreamObservations`**: Server-side streaming RPC yielding successive state transitions and observations.
- **`BenchmarkThroughput`**: Profiles stepping throughput in transitions per second.

#### 2. Starting the gRPC Server

Run the gRPC simulator service on the default port (`50051`):
```bash
python -m backend.grpc_service.server
```

#### 3. Python gRPC Client Usage

```python
from backend.grpc_service.client import SimulatorGRPCClient

with SimulatorGRPCClient(target="127.0.0.1:50051") as client:
    # Reset environment
    reset_data = client.reset(env_id="CartPole-v1", seed=42)
    obs = reset_data["observation"]

    # Execute single step
    step_data = client.step(env_id="CartPole-v1", action=1, is_discrete=True)
    next_obs, reward, done = step_data["observation"], step_data["reward"], step_data["done"]

    # Batch step execution
    batch_data = client.batch_step(
        steps=[
            {"env_id": "CartPole-v1", "action": 0, "is_discrete": True},
            {"env_id": "CartPole-v1", "action": 1, "is_discrete": True},
        ],
        batch_id="batch-001",
    )

    # Stream observation trajectory
    for transition in client.stream_observations(env_id="CartPole-v1", max_steps=50):
        print(f"Step {transition['step_count']}: reward={transition['reward']}")

    # Profile throughput
    perf = client.benchmark_throughput(env_id="CartPole-v1", num_steps=1000, batch_size=32)
    print(f"Throughput: {perf['steps_per_second']:.1f} steps/sec")
```

#### 4. REST to gRPC Gateway Endpoints

For HTTP clients and web dashboards, FastAPI and Flask expose transparent REST endpoints bridging directly to the gRPC service:

| Endpoint | Method | Description |
|:---|:---:|:---|
| `/simulator/health` | GET | Inspect simulator service operational status |
| `/simulator/environments` | GET | List supported simulation environments |
| `/simulator/reset` | POST | Initialise or reset environment with optional seed |
| `/simulator/step` | POST | Execute a single transition step |
| `/simulator/batch_step` | POST | Execute vectorised batch stepping |
| `/simulator/stream` | POST | Stream consecutive observation steps |
| `/simulator/benchmark` | POST | Profile simulator throughput and latency |

---

### Real-Time Visualisation & WebSocket Dashboard
Open your browser and navigate to:
```
http://127.0.0.1:8000/dashboard
```

**Key Dashboard Features:**
- **Live Training Visualiser**: Launch interactive training sessions via WebSocket (`/ws/live-train`) and watch real-time reward convergence, moving averages, loss decay, and exploration rate.
- **Task Stream Inspector**: Connect directly to arbitrary Celery tasks via WebSocket (`/ws/tasks/{task_id}`).
- **Interactive Benchmark Suite**: Trigger policy evaluations on environments (`CartPole-v1`, `LunarLander-v2`) and compare multi-agent performances dynamically.
- **Real-Time Telemetry**: Live metric snapshots via WebSocket (`/ws/live-metrics`) and Prometheus metrics gauges.

---
## Research Context: RL Infrastructure Landscape

The **ReSimHub** framework emerges from an analysis of the **Reinforcement Learning (RL) infrastructure landscape**, 
as documented in [`docs/rl_landscape.md`](./docs/rl_landscape.md).

This contextual study explores:
- Current gaps between RL research tools and production-grade simulation systems  
- The fragmentation of orchestration and analytics workflows in existing frameworks  
- The need for **unified experiment orchestration**, **analytics pipelines**, and **scalable evaluation layers**  

By addressing these gaps, **ReSimHub** provides a bridge between academic experimentation and scalable applied RL systems.
This background analysis establishes the motivation for ReSimHub’s architecture, ensuring that design choices align with real-world reproducibility and scalability challenges.
📖 For full details, see: [RL Landscape Analysis →](./docs/rl_landscape.md)

---

## Testing

ReSimHub includes a comprehensive testing suite for API validation, benchmark execution, and quality assurance.

### Quick Test Run

```bash
# Install dependencies
pip install -r requirements.txt

# Prepare storage
mkdir -p storage/models

# Run tests
python -m pytest tests/test_benchmark_api.py -v --disable-warnings
```

### Expected Results

```
tests/test_benchmark_api.py::test_upload_model PASSED                    [ 20%]
tests/test_benchmark_api.py::test_run_benchmark PASSED                   [ 40%]
tests/test_benchmark_api.py::test_list_recent_results PASSED             [ 60%]
tests/test_benchmark_api.py::test_compare_models PASSED                  [ 80%]
tests/test_benchmark_api.py::test_invalid_compare_model_id PASSED        [100%]

================================================= 5 passed in 1.33s ==================================================
```

### Complete Testing Documentation

For detailed setup instructions, configuration options, CI/CD integration, and troubleshooting guides, see:

**→ [Complete Testing Guide](docs/benchmark_api_tests.md)**


---

## Road Ahead

- [x] ReSimHub Dashboard (WebSocket streaming & real-time RL visualisation)
- [x] Multi-agent orchestration and scheduling (parallel batch execution across Celery workers)
- [x] Model checkpointing and artifact versioning (dynamic saving and loading of model weights)
- [x] REST to gRPC bridge (high-throughput simulator communication via Protocol Buffers)
- [ ] Plugin system for custom RL environments
- [ ] Automated benchmark publishing (OpenAI Gym, PettingZoo)

---

## Licence

This project is licensed under the **BSD 3-Clause Licence**. See the [LICENSE](./LICENSE) file for details.

```
BSD 3-Clause Licence

Copyright (c) 2025, Mosudi Isiaka
All rights reserved.
```

---

## 👤 Author

**Mosudi Isiaka**  
📧 [mosudi.isiaka@gmail.com](mailto:mosudi.isiaka@gmail.com)  
🌐 [https://mioemi.com](https://mioemi.com)   
💻 [https://github.com/imosudi](https://github.com/imosudi)

---

## Contributing

Contributions are welcome!  
Please open an issue or pull request to suggest new features, improvements, or bug fixes.

---

## Citation (Academic Use)

If you use ReSimHub in your research, please cite as:

```bibtex
@software{ReSimHub2025,
  author = {Isiaka, Mosudi},
  title = {ReSimHub: Scalable Research Backend for Reinforcement Learning Experimentation},
  year = {2025},
  url = {https://github.com/imosudi/ReSimHub},
  license = {BSD-3-Clause}
}
```

---

> “ReSimHub bridges simulation, orchestration, and reproducible reinforcement learning - for scalable research you can trust.”
