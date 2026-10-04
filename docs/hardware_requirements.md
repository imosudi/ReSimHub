# ReSimHub Hardware Requirements and Sizing Guide

This document provides comprehensive hardware specifications, resource allocation guidelines, and architectural bottleneck analyses for deploying **ReSimHub** across local development, multi-agent research workstations, and distributed cluster environments.

---

## 1. Architectural Resource Characteristics

ReSimHub's decoupled microservice architecture divides operational workloads across distinct functional tiers, each exhibiting specific computational, memory, and I/O profiles:

- **API Gateways & Control Plane**: FastAPI and Flask handle asynchronous and synchronous HTTP/REST requests, WebSocket telemetry broadcasts, and proxy routing. These services are primarily I/O-bound with modest memory and CPU utilization.
- **High-Throughput Simulator Bridge**: The gRPC Protocol Buffers engine (`SimulatorBridgeServicer`) handles environment state stepping, vectorised batch transitions, and observation streaming. This tier is CPU-bound and memory-bandwidth sensitive, requiring low scheduling latency.
- **Distributed Worker Plane**: Celery workers execute reinforcement learning training loops (PPO, DQN, SAC), agent rollouts, trajectory processing, and multi-agent batch scheduling. Physics simulations and environment transitions run on the CPU, while neural policy optimizations and gradient updates can be accelerated on GPUs.
- **State Persistence & Message Broker**: Redis coordinates Celery task distribution, pub/sub telemetry, and benchmark result caching. PostgreSQL persists experiment records, batch schedules, model metadata, and metrics.
- **Observability Stack**: Prometheus scrapes metric time-series data and Grafana renders live dashboards, requiring dedicated SSD space for time-series database (TSDB) storage.
- **Model Storage & Artifact Persistence**: Checkpoints and model weights are serialised to disk with SHA-256 cryptographic hashes for tamper detection, requiring fast sequential write speeds.

---

## 2. Hardware Requirements Matrix

| Deployment Tier | Primary Workload | CPU | System Memory (RAM) | Storage (SSD/NVMe) | Accelerator (GPU) | Network |
|:---|:---|:---|:---|:---|:---|:---|
| **Tier 1: Minimal / Local Development** | Unit tests, single-agent training, lightweight evaluation, API testing. | 2 to 4 Cores (x86_64 or ARM64) | 4 GB to 8 GB | 15 GB SSD | Optional (CPU execution for classic control) | Local Loopback (`127.0.0.1`) |
| **Tier 2: Research Workstation** | Multi-agent batch scheduling, 4 to 8 Celery workers, live checkpointing, local gRPC simulator. | 8 to 16 Cores (AMD Ryzen 7/9, Intel i7/i9, Apple M-series Pro/Max) | 16 GB to 32 GB DDR4 / DDR5 | 50 GB to 100 GB NVMe SSD | 1x NVIDIA GPU (8 GB to 16 GB VRAM, e.g. RTX 3070/4070 or T4) | 1 Gbps Ethernet |
| **Tier 3: Distributed Cluster / Production** | Multi-node Kubernetes deployment, large-scale sweeps, high-concurrency multi-agent batches. | 16 to 64+ vCPUs per compute node | 32 GB to 128+ GB per node | 200 GB+ High-IOPS NVMe / Shared SAN / Ceph / S3 | Multi-GPU (NVIDIA A10 / A100 / L4 / H100 with PCIe Gen 4/5) | 10 Gbps to 25 Gbps Low-Latency Interconnect |

---

## 3. Subsystem Resource Breakdown

### A. API Control Plane & Gateway Services (`backend/fastapi_app/`, `backend/flask_app/`)
- **Role**: Ingestion of experiment configurations, dashboard WebSocket telemetry, and REST endpoints.
- **CPU**: 1 to 2 vCPUs per replica.
- **RAM**: 512 MB to 1 GB per replica.
- **Scaling Strategy**: Horizontally scalable behind an ingress load balancer.

### B. High-Throughput gRPC Simulator Bridge (`backend/grpc_service/`)
- **Role**: Sub-millisecond environment stepping and observation streaming over Protocol Buffers.
- **CPU**: 2 to 4 dedicated CPU cores per simulator instance to maintain sub-millisecond transition latency without thread pre-emption.
- **RAM**: 1 GB to 2 GB per active simulation session pool.
- **Network**: Co-locating the simulator bridge on the same node or local virtual network as the worker pool minimizes network hop overhead.

### C. Distributed Worker Plane (`backend/fastapi_app/services/orchestrator.py`)
- **Role**: Execution of RL training tasks, multi-agent trials, and evaluation rollouts.
- **CPU**: 1 dedicated CPU core per concurrent worker thread (`--concurrency=N`). For a batch of 8 parallel agents, 8 physical cores prevent CPU contention.
- **RAM**: 2 GB to 4 GB per worker process. If utilizing large experience replay buffers (e.g. 500,000 to 1,000,000 transitions), allocate 4 GB to 8 GB per worker.
- **GPU Acceleration**: Recommended for deep neural policy backpropagation and image-based observations (e.g. Atari, visual robotics).

### D. Message Broker & Database (`docker/docker-compose.yml`)
- **Role**: Redis task queue management and PostgreSQL relational persistence.
- **CPU**: 2 vCPUs.
- **RAM**:
  - **Redis**: 1 GB to 4 GB (sized based on queue throughput and cached benchmark evaluations).
  - **PostgreSQL**: 2 GB to 4 GB (configured with balanced `shared_buffers` and `work_mem`).
- **Disk**: 10 GB to 30 GB SSD with consistent write IOPS for transaction logs.

### E. Observability Stack (`monitoring/`)
- **Role**: Prometheus metrics scraping and Grafana dashboard visualization.
- **CPU**: 1 to 2 vCPUs.
- **RAM**: 1 GB to 2 GB for active metric series retention.
- **Disk**: 10 GB to 20 GB dedicated TSDB volume for historical trends.

### F. Model Storage & Checkpoint Persistence (`storage/models/`, `storage/checkpoints/`)
- **Role**: Storage of neural network weights, configuration states, and SHA-256 integrity checksums.
- **Storage Type**: NVMe solid-state storage to prevent disk write bottlenecks during periodic epoch checkpointing.
- **Capacity**: Sized according to:
  $$\text{Storage Budget} = \text{Model Size} \times \text{Checkpoints Retained} \times \text{Active Experiments}$$

---

## 4. Bottleneck Analysis & Hardware Tuning Strategies

### 1. CPU Core Count (The Primary Simulation Bottleneck)
In reinforcement learning, environment physics and state transitions run primarily on the CPU. When executing multi-agent batch schedules, overall throughput scales linearly with available CPU cores up to the worker concurrency limit. High single-core clock frequencies (3.5 GHz+) reduce individual step latency.

### 2. RAM Capacity & Memory Bus Bandwidth
Algorithms relying on off-policy experience replay buffers (such as DQN, SAC, or DDPG) continuously sample random mini-batches from system RAM. Multi-channel DDR4-3200+ or DDR5-4800+ memory significantly decreases memory bus contention during simultaneous multi-agent updates.

### 3. Disk Write Latency for Checkpointing
Dynamic model checkpointing serialises model weights and computes SHA-256 integrity checksums on the fly. Fast NVMe drives ensure that weight writes complete in milliseconds, eliminating pauses in the simulation training loop.

### 4. GPU Acceleration Guidelines
- **Vector / Classic Control (`CartPole-v1`, `LunarLander-v2`, `Pendulum-v1`)**: Multi-core CPU execution is highly efficient. For small multi-layer perceptrons (MLPs), PCIe bus transfer latency between CPU and GPU may exceed CPU calculation time.
- **High-Dimensional & Visual Domains (Convolutional policies, MuJoCo, Isaac Gym)**: A dedicated GPU with Tensor Cores is essential to parallelise tensor operations, batched forward passes, and gradient updates.

---

## 5. Recommended Deployment Profiles

### Profile A: Local Developer Machine
- **Hardware**: Quad-core or 8-core CPU, 16 GB RAM, 256 GB SSD.
- **Setup**: Standalone Python virtual environment, SQLite database, in-process fallback simulator, single Celery worker.

### Profile B: Dedicated Research Server
- **Hardware**: 16-Core AMD Ryzen 9 7950X or Intel Core i9-14900K, 64 GB DDR5 RAM, 1 TB NVMe SSD, 1x NVIDIA RTX 4080 (16 GB VRAM).
- **Setup**: Full Docker Compose stack running 8 concurrent Celery workers, Redis, PostgreSQL, Prometheus, Grafana, and high-frequency gRPC stepping.

### Profile C: Distributed Kubernetes Cluster (`k8s/deployment.yaml`)
- **Hardware**: Master plane (4 vCPU, 8 GB RAM), compute worker pool (e.g. AWS `c6i.4xlarge` for CPU-heavy simulators or `g5.2xlarge` for GPU-accelerated policies).
- **Setup**: Cluster autoscaling with persistent volume claims (PVC) backed by high-IOPS cloud block storage or shared network file systems.
