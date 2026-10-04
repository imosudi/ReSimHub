

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
It provides **RESTful** and **asynchronous APIs** for managing **simulation environments**, **training orchestration**, and **agent evaluation** — all optimised for distributed systems and reproducible research.

> Built for modern RL pipelines — where **experimentation**, **asynchronous training**, and **performance evaluation** converge.

---

## Key Features

- **Hybrid Flask–FastAPI Framework** — Combines Flask’s flexibility with FastAPI’s async capabilities.
- **Experiment Management APIs** — Create, register, and manage experiments programmatically.
- **Distributed Orchestration** — Scalable Celery + Redis job queues for RL training workloads.
- **Data Processing Layer** — NumPy/Pandas-powered analytics for logs, metrics, and benchmarking.
- **Unified API Gateway** — Seamless bridge between Flask and FastAPI services.
- **Evaluation & Benchmarking APIs** — Compare and score RL agents using consistent metrics.
- **Observability Stack** — Prometheus and Grafana integration for monitoring.
- **Containerised Deployment** — Docker- and Kubernetes-ready for research clusters.

---

## Development Roadmap

| **Stage** | **Focus Area** | **Objective** |
|:-----------|:----------------|:---------------|
| **Stage 1** | Project Bootstrap | Initialise structure, dependencies, hybrid Flask–FastAPI framework, and CI pipeline. |
| **Stage 2** | Core Experimentation APIs | Create experiment management, environment registration, and metadata models. |
| **Stage 3** | Async Orchestration | Integrate Celery + Redis for distributed training tasks. |
| **Stage 4** | Data Processing Layer | Add NumPy/Pandas-powered services for results and benchmarking. |
| **Stage 5** | Flask–FastAPI Bridge | Implement communication bridge and unified API gateway. |
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

### Real-Time Visualisation & WebSocket Dashboard
Open your browser and navigate to:
```
http://127.0.0.1:8000/dashboard
```

**Key Dashboard Features:**
- **Live Training Visualizer**: Launch interactive training sessions via WebSocket (`/ws/live-train`) and watch real-time reward convergence, moving averages, loss decay, and exploration rate.
- **Task Stream Inspector**: Connect directly to arbitrary Celery tasks via WebSocket (`/ws/tasks/{task_id}`).
- **Interactive Benchmark Suite**: Trigger policy evaluations on environments (`CartPole-v1`, `LunarLander-v2`) and compare multi-agent performances dynamically.
- **Real-Time Telemetry**: Live metric snapshots via WebSocket (`/ws/live-metrics`) and Prometheus metrics gauges.

---
## Research Context — RL Infrastructure Landscape

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
- [ ] Multi-agent orchestration and scheduling
- [ ] REST → gRPC bridge
- [ ] Plugin system for custom RL environments
- [ ] Automated benchmark publishing (OpenAI Gym, PettingZoo)

---

## License

This project is licensed under the **BSD 3-Clause License** — see the [LICENSE](./LICENSE) file for details.

```
BSD 3-Clause License

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
