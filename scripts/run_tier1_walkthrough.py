#!/usr/bin/env python3
"""
ReSimHub Tier 1 Walkthrough Script.

Executes the complete reinforcement learning experiment lifecycle end-to-end:
  1. Service Health Inspection
  2. Environment Registration
  3. Experiment Creation
  4. Simulator Bridge Stepping & Batching
  5. Throughput Benchmarking
  6. Multi-Agent Batch Dispatch
  7. Model Checkpointing & SHA-256 Verification
  8. Policy Evaluation & Scoring
  9. Analytics & Telemetry Inspection
  10. Dynamic Training Resumption
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Any

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from backend.fastapi_app.main import app

client = TestClient(app)


def print_stage(title: str, stage_num: int) -> None:
    print("\n" + "=" * 70)
    print(f"  STAGE {stage_num}: {title.upper()}")
    print("=" * 70)


def format_json(data: Any) -> str:
    return json.dumps(data, indent=2)


def main() -> None:
    print("\nStarting ReSimHub Tier 1 Lifecycle Walkthrough...")
    time.sleep(0.5)

    # -------------------------------------------------------------
    # Stage 1: Health Check
    # -------------------------------------------------------------
    print_stage("Service Health Inspection", 1)
    res_health = client.get("/health")
    res_sim_health = client.get("/simulator/health")
    print(f"[+] FastAPI Health: {res_health.status_code}")
    print(format_json(res_health.json()))
    print(f"[+] Simulator Health: {res_sim_health.status_code}")
    print(format_json(res_sim_health.json()))

    # -------------------------------------------------------------
    # Stage 2: Register Environment
    # -------------------------------------------------------------
    print_stage("Environment Registration", 2)
    env_payload = {"env_name": "CartPole-v1", "version": "v1"}
    print(f"[>] POST /environments/ with payload:\n{format_json(env_payload)}")
    res_env = client.post("/environments/", json=env_payload)
    print(f"[+] Response ({res_env.status_code}):\n{format_json(res_env.json())}")

    # -------------------------------------------------------------
    # Stage 3: Create Experiment
    # -------------------------------------------------------------
    print_stage("Experiment Initialisation", 3)
    exp_payload = {
        "name": "CartPole-DQN-Tier1-Run",
        "description": "Tier 1 local verification experiment using DQN on CartPole-v1",
    }
    print(f"[>] POST /experiments/ with payload:\n{format_json(exp_payload)}")
    res_exp = client.post("/experiments/", json=exp_payload)
    exp_data = res_exp.json()
    exp_id = exp_data.get("id", 1)
    print(f"[+] Response ({res_exp.status_code}):\n{format_json(exp_data)}")

    # -------------------------------------------------------------
    # Stage 4: Simulator Bridge Interaction
    # -------------------------------------------------------------
    print_stage("Simulator Bridge Stepping (Reset & Transition)", 4)
    reset_payload = {"env_id": "CartPole-v1", "seed": 42}
    res_reset = client.post("/simulator/reset", json=reset_payload)
    print(f"[+] Reset Response:\n{format_json(res_reset.json())}")

    step_payload = {"env_id": "CartPole-v1", "action": 1, "is_discrete": True}
    res_step = client.post("/simulator/step", json=step_payload)
    print(f"[+] Single Step Response:\n{format_json(res_step.json())}")

    # -------------------------------------------------------------
    # Stage 5: Throughput Benchmarking
    # -------------------------------------------------------------
    print_stage("Simulator Stepping Throughput Profiling", 5)
    bench_sim_payload = {"env_id": "CartPole-v1", "num_steps": 1000, "batch_size": 32}
    res_bench_sim = client.post("/simulator/benchmark", json=bench_sim_payload)
    print(f"[+] Simulator Throughput Benchmark:\n{format_json(res_bench_sim.json())}")

    # -------------------------------------------------------------
    # Stage 6: Multi-Agent Parallel Batch Scheduling
    # -------------------------------------------------------------
    print_stage("Multi-Agent Batch Scheduling", 6)
    batch_payload = {
        "batch_name": "Tier1-CartPole-Parallel-Batch",
        "experiment_id": exp_id,
        "priority": 1,
        "agent_trials": [
            {
                "trial_name": "Trial-Agent-1",
                "algo": "DQN",
                "env_name": "CartPole-v1",
                "seed": 42,
                "epochs": 3,
                "hyperparameters": {"lr": 0.001, "gamma": 0.99},
            },
            {
                "trial_name": "Trial-Agent-2",
                "algo": "PPO",
                "env_name": "CartPole-v1",
                "seed": 100,
                "epochs": 3,
                "hyperparameters": {"lr": 0.0003, "clip_eps": 0.2},
            },
        ],
    }
    res_batch = client.post("/orchestrate/batch", json=batch_payload)
    batch_data = res_batch.json()
    batch_id = batch_data.get("batch_id", "")
    print(f"[+] Batch Schedule Response:\n{format_json(batch_data)}")

    if batch_id:
        res_batch_status = client.get(f"/orchestrate/batch/{batch_id}")
        print(f"[+] Batch Status:\n{format_json(res_batch_status.json())}")

    # -------------------------------------------------------------
    # Stage 7: Model Checkpointing & SHA-256 Integrity
    # -------------------------------------------------------------
    print_stage("Model Checkpointing and Tamper Verification", 7)
    ckpt_payload = {
        "algo": "DQN",
        "env_name": "CartPole-v1",
        "epoch": 3,
        "experiment_id": exp_id,
        "step": 1500,
        "reward": 490.5,
        "loss": 0.0084,
        "version": "v1.0",
        "weights": {
            "fc1": [0.24, -0.15, 0.62, 0.08],
            "fc2": [-0.44, 0.71, 0.12, -0.35],
            "bias": [0.05, -0.01],
        },
        "hyperparameters": {"lr": 0.001, "gamma": 0.99},
    }
    res_ckpt = client.post("/checkpoints/", json=ckpt_payload)
    ckpt_data = res_ckpt.json()
    ckpt_id = ckpt_data.get("checkpoint_id", "")
    print(f"[+] Checkpoint Created:\n{format_json(ckpt_data)}")

    if ckpt_id:
        res_weights = client.get(f"/checkpoints/{ckpt_id}/weights")
        print(f"[+] Loaded Weights (Integrity Verified):\n{format_json(res_weights.json())}")

        res_best = client.get("/checkpoints/best?algo=DQN&env_name=CartPole-v1")
        print(f"[+] Top-Performing Checkpoint:\n{format_json(res_best.json())}")

    # -------------------------------------------------------------
    # Stage 8: Policy Evaluation & Scoring
    # -------------------------------------------------------------
    print_stage("Policy Evaluation and Benchmarking", 8)
    sample_model_path = Path("docs/dqn_model.pkl")
    if sample_model_path.exists():
        with open(sample_model_path, "rb") as f:
            res_upload = client.post("/benchmark/upload_model", files={"file": ("dqn_model.pkl", f, "application/octet-stream")})
            upload_data = res_upload.json()
            model_id = upload_data.get("model_id", "dqn_model.pkl")
            print(f"[+] Uploaded Policy Model:\n{format_json(upload_data)}")
    else:
        model_id = "dqn_model.pkl"

    bench_run_data = {
        "model_id": model_id,
        "env_name": "CartPole-v1",
        "episodes": 20,
    }
    res_bench_run = client.post("/benchmark/run", data=bench_run_data)
    print(f"[+] Benchmark Evaluation Result:\n{format_json(res_bench_run.json())}")

    res_bench_recent = client.get("/benchmark/recent?limit=5")
    print(f"[+] Recent Benchmark Leaderboard:\n{format_json(res_bench_recent.json())}")

    # -------------------------------------------------------------
    # Stage 9: Analytics Inspection
    # -------------------------------------------------------------
    print_stage("Experiment Analytics Inspection", 9)
    res_analytics = client.get(f"/analytics/experiment/{exp_id}")
    print(f"[+] Experiment Analytics:\n{format_json(res_analytics.json())}")

    # -------------------------------------------------------------
    # Stage 10: Training Resumption
    # -------------------------------------------------------------
    print_stage("Dynamic Training Resumption", 10)
    if ckpt_id:
        resume_payload = {"resume_epochs": 5}
        res_resume = client.post(f"/checkpoints/{ckpt_id}/resume", json=resume_payload)
        print(f"[+] Resumed Training Task:\n{format_json(res_resume.json())}")

    print("\n" + "=" * 70)
    print("  TIER 1 WALKTHROUGH COMPLETED SUCCESSFULLY!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
