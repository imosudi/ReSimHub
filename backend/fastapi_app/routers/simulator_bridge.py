# backend/fastapi_app/routers/simulator_bridge.py
"""
FastAPI Router for Simulator Bridge & gRPC Interoperability.

Exposes REST endpoints allowing agent runners, testing clients, and external
dashboards to execute environment transitions and throughput benchmarks.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List

from shared.schemas.simulator_schema import (
    SimulatorResetRequest,
    SimulatorResetResponse,
    SimulatorStepRequest,
    SimulatorStepResponse,
    SimulatorBatchStepRequest,
    SimulatorBatchStepResponse,
    SimulatorStreamRequest,
    SimulatorStreamResponse,
    SimulatorBenchmarkRequest,
    SimulatorBenchmarkResponse,
)
from backend.fastapi_app.services.grpc_client import get_simulator_gateway, SimulatorServiceGateway

router = APIRouter(prefix="/simulator", tags=["Simulator Bridge"])


@router.get("/health", summary="Check simulator service status")
async def get_health(gateway: SimulatorServiceGateway = Depends(get_simulator_gateway)):
    """Check health, operational status, and supported environments of the simulator service."""
    return gateway.check_health()


@router.get("/environments", response_model=List[str], summary="List supported simulation environments")
async def get_environments(gateway: SimulatorServiceGateway = Depends(get_simulator_gateway)):
    """Return available simulation environments supported by the gRPC bridge."""
    health_data = gateway.check_health()
    return health_data.get("available_environments", [])


@router.post("/reset", response_model=SimulatorResetResponse, summary="Reset simulation environment")
async def reset_environment(
    payload: SimulatorResetRequest,
    gateway: SimulatorServiceGateway = Depends(get_simulator_gateway),
):
    """Initialise or reset a simulation environment instance and return starting observation."""
    try:
        res = gateway.reset(
            env_id=payload.env_id,
            seed=payload.seed,
            options=payload.options,
        )
        return SimulatorResetResponse(**res)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to reset environment: {str(exc)}")


@router.post("/step", response_model=SimulatorStepResponse, summary="Execute single simulation step")
async def step_environment(
    payload: SimulatorStepRequest,
    gateway: SimulatorServiceGateway = Depends(get_simulator_gateway),
):
    """Execute a single transition step in the environment using specified action."""
    try:
        res = gateway.step(
            env_id=payload.env_id,
            action=payload.action,
            is_discrete=payload.is_discrete,
            step_index=payload.step_index,
        )
        return SimulatorStepResponse(**res)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to step environment: {str(exc)}")


@router.post("/batch_step", response_model=SimulatorBatchStepResponse, summary="Execute batch environment steps")
async def batch_step_environment(
    payload: SimulatorBatchStepRequest,
    gateway: SimulatorServiceGateway = Depends(get_simulator_gateway),
):
    """Execute a batch of environment transitions concurrently or in vectorised sequence."""
    try:
        steps_dicts = [s.dict() for s in payload.steps]
        res = gateway.batch_step(steps=steps_dicts, batch_id=payload.batch_id or "")
        return SimulatorBatchStepResponse(**res)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to execute batch steps: {str(exc)}")


@router.post("/stream", response_model=SimulatorStreamResponse, summary="Run observation stream sequence")
async def stream_observations(
    payload: SimulatorStreamRequest,
    gateway: SimulatorServiceGateway = Depends(get_simulator_gateway),
):
    """Execute an automated trajectory sequence and stream observations."""
    try:
        steps = gateway.stream_observations(
            env_id=payload.env_id,
            max_steps=payload.max_steps,
            seed=payload.seed,
            policy_type=payload.policy_type,
        )
        total_steps = len(steps)
        cum_reward = sum(s.get("reward", 0.0) for s in steps)
        formatted_steps = [SimulatorStepResponse(**s) for s in steps]
        return SimulatorStreamResponse(
            env_id=payload.env_id,
            total_steps=total_steps,
            cumulative_reward=cum_reward,
            steps=formatted_steps,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to stream observations: {str(exc)}")


@router.post("/benchmark", response_model=SimulatorBenchmarkResponse, summary="Run throughput benchmark")
async def benchmark_throughput(
    payload: SimulatorBenchmarkRequest,
    gateway: SimulatorServiceGateway = Depends(get_simulator_gateway),
):
    """Profile simulator stepping throughput and calculate mean latency metrics."""
    try:
        res = gateway.benchmark_throughput(
            env_id=payload.env_id,
            num_steps=payload.num_steps,
            batch_size=payload.batch_size,
        )
        return SimulatorBenchmarkResponse(**res)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to benchmark throughput: {str(exc)}")
