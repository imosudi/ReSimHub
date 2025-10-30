# 🧠 ReSimHub

**ReSimHub** is a **scalable, research-grade backend framework** designed for **reinforcement learning (RL)** experimentation, simulation, and benchmarking.  
It provides **RESTful** and **asynchronous APIs** for managing **simulation environments**, **training orchestration**, and **agent evaluation** — all optimised for distributed systems and reproducible research.

> Built for modern RL pipelines — where **experimentation**, **asynchronous training**, and **performance evaluation** converge.

---

## 🚀 Key Features

- **Hybrid Flask–FastAPI Framework** — Combines Flask’s flexibility with FastAPI’s async capabilities.
- **Experiment Management APIs** — Create, register, and manage experiments programmatically.
- **Distributed Orchestration** — Scalable Celery + Redis job queues for RL training workloads.
- **Data Processing Layer** — NumPy/Pandas-powered analytics for logs, metrics, and benchmarking.
- **Unified API Gateway** — Seamless bridge between Flask and FastAPI services.
- **Evaluation & Benchmarking APIs** — Compare and score RL agents using consistent metrics.
- **Observability Stack** — Prometheus and Grafana integration for monitoring.
- **Containerised Deployment** — Docker- and Kubernetes-ready for research clusters.

---

## 🧩 Development Roadmap

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

## 🧱 Architecture Overview

```
                        ┌──────────────────────────────┐
                        │        REST Clients          │
                        └─────────────┬────────────────┘
                                      │
          ┌───────────────────────────┼────────────────────────┐
          │                           │                        │
  ┌───────▼────────┐        ┌─────────▼────────┐       ┌───────▼────────┐
  │    Flask API   │ ◄────► │FastAPI Core Logic│ ◄────►│ Celery Workers │
  │ (Legacy/Sync)  │        │ (Async Gateway)  │       │ (Distributed)  │
  └───────┬────────┘        └─────────┬────────┘       └───────┬────────┘
          │                           │                        │
    ┌─────▼──────┐              ┌─────▼─────┐        ┌─────────▼──────────┐
    │ PostgreSQL │              │ Redis MQ  │        │ Prometheus/Grafana │
    └────────────┘              └───────────┘        └────────────────────┘
```

---

## 🛠️ Installation

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

## ⚙️ Running the Project

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

## 📊 Example Usage

### 1️⃣ Register an Environment
```bash
curl -X POST http://localhost:8000/api/environments      -H "Content-Type: application/json"      -d '{"env_name": "CartPole-v1", "version": "v1"}'
```
**Output**
```json
{"id":1,"env_name":"CartPole-v1","version":"v1","registered_at":"2025-10-29T06:00:00"}
```

---

### 2️⃣ Create a New Experiment
```bash
curl -X POST http://localhost:8000/api/experiments      -H "Content-Type: application/json"      -d '{"name": "CartPole-v1", "agent": "DQN", "episodes": 500}'
```
**Output**
```json
{"id":1,"name":"CartPole-v1","agent":"DQN","episodes":500,"status":"created","created_at":"2025-10-29T06:01:00"}
```

---

### 3️⃣ Launch Training via Flask Proxy
```bash
curl -X POST http://localhost:5000/api/v1/start_training   -H "Content-Type: application/json"   -d '{"experiment_id": 1, "env_name": "CartPole-v1", "algo": "DQN"}'

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

### 4️⃣ Retrieve Analytics for All Experiments
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

### 5️⃣ Retrieve Analytics for a Specific Experiment - say experiment id: 1
```bash
curl http://127.0.0.1:5000/api/v1/analytics/experiment/2
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

## 🧪 Testing

```bash
pytest tests/ --disable-warnings
```

---

## 🧭 Road Ahead

- [ ] Multi-agent orchestration and scheduling
- [ ] REST → gRPC bridge
- [ ] ReSimHub Dashboard (React + WebSocket visualisation)
- [ ] Plugin system for custom RL environments
- [ ] Automated benchmark publishing (OpenAI Gym, PettingZoo)

---

## 🪪 License

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
🌐 [https://github.com/imosudi](https://github.com/imosudi  
🌐 [https://github.com/imosudi](https://github.com/imosudi))

---

## ⭐ Contributing

Contributions are welcome!  
Please open an issue or pull request to suggest new features, improvements, or bug fixes.

---

## 💡 Citation (Academic Use)

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

> “ReSimHub bridges simulation, orchestration, and reproducible reinforcement learning — for scalable research you can trust.”