"""
FastAPI gRPC Client Service for Simulator Communication.

Provides connection management, fallback handling, and high-throughput stepping
wrappers for ReSimHub simulator interactions.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Iterator
import grpc

from backend.grpc_service.client import SimulatorGRPCClient
from backend.grpc_service.simulator_service import SimulatorBridgeServicer
from shared.proto import simulator_pb2

logger = logging.getLogger("SimulatorGRPCClientService")

DEFAULT_GRPC_TARGET = os.getenv("GRPC_SIMULATOR_TARGET", "127.0.0.1:50051")


class SimulatorServiceGateway:
    """
    Gateway coordinating simulator stepping via external gRPC server or in-process servicer fallback.
    """

    def __init__(self, target: Optional[str] = None) -> None:
        self.target = target or DEFAULT_GRPC_TARGET
        self._fallback_servicer: Optional[SimulatorBridgeServicer] = None

    def _get_fallback_servicer(self) -> SimulatorBridgeServicer:
        """Lazily initialise an in-process servicer fallback if external gRPC is unavailable."""
        if self._fallback_servicer is None:
            self._fallback_servicer = SimulatorBridgeServicer()
        return self._fallback_servicer

    def check_health(self) -> Dict[str, Any]:
        """Check simulator service health via gRPC, falling back to local servicer if offline."""
        try:
            with SimulatorGRPCClient(self.target) as client:
                return client.check_health()
        except (grpc.RpcError, Exception) as exc:
            logger.debug(f"gRPC server unreachable on {self.target}, using local servicer: {exc}")
            servicer = self._get_fallback_servicer()
            resp = servicer.CheckHealth(simulator_pb2.HealthRequest(client_id="fastapi-fallback"), None)
            return {
                "status": "SERVING (in-process fallback)",
                "version": resp.version,
                "available_environments": list(resp.available_environments),
                "uptime_seconds": resp.uptime_seconds,
            }

    def reset(
        self,
        env_id: str = "CartPole-v1",
        seed: Optional[int] = None,
        options: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Reset simulator environment via gRPC or local fallback."""
        try:
            with SimulatorGRPCClient(self.target) as client:
                return client.reset(env_id=env_id, seed=seed, options=options)
        except (grpc.RpcError, Exception) as exc:
            logger.debug(f"gRPC reset fallback: {exc}")
            servicer = self._get_fallback_servicer()
            req = simulator_pb2.ResetRequest(
                env_id=env_id,
                seed=seed if seed is not None else 0,
                options=options or {},
            )
            resp = servicer.Reset(req, None)
            return {
                "env_id": resp.env_id,
                "observation": list(resp.observation),
                "info": dict(resp.info),
                "success": resp.success,
            }

    def step(
        self,
        env_id: str = "CartPole-v1",
        action: Any = 0,
        is_discrete: bool = True,
        step_index: int = 0,
    ) -> Dict[str, Any]:
        """Execute single environment step via gRPC or local fallback."""
        try:
            with SimulatorGRPCClient(self.target) as client:
                return client.step(
                    env_id=env_id,
                    action=action,
                    is_discrete=is_discrete,
                    step_index=step_index,
                )
        except (grpc.RpcError, Exception) as exc:
            logger.debug(f"gRPC step fallback: {exc}")
            servicer = self._get_fallback_servicer()
            continuous_vals = []
            discrete_val = 0
            if is_discrete:
                discrete_val = int(action)
            else:
                continuous_vals = [float(x) for x in (action if isinstance(action, (list, tuple)) else [action])]

            req = simulator_pb2.StepRequest(
                env_id=env_id,
                discrete_action=discrete_val,
                continuous_action=continuous_vals,
                is_discrete=is_discrete,
                step_index=step_index,
            )
            resp = servicer.Step(req, None)
            return {
                "env_id": resp.env_id,
                "observation": list(resp.observation),
                "reward": resp.reward,
                "done": resp.done,
                "truncated": resp.truncated,
                "info": dict(resp.info),
                "step_count": resp.step_count,
                "latency_ms": resp.latency_ms,
            }

    def batch_step(
        self,
        steps: List[Dict[str, Any]],
        batch_id: str = "",
    ) -> Dict[str, Any]:
        """Execute batch environment steps via gRPC or local fallback."""
        try:
            with SimulatorGRPCClient(self.target) as client:
                return client.batch_step(steps=steps, batch_id=batch_id)
        except (grpc.RpcError, Exception) as exc:
            logger.debug(f"gRPC batch step fallback: {exc}")
            servicer = self._get_fallback_servicer()
            proto_steps = []
            for s in steps:
                is_discrete = s.get("is_discrete", True)
                action = s.get("action", 0)
                if is_discrete:
                    d_act = int(action)
                    c_act = []
                else:
                    d_act = 0
                    c_act = [float(x) for x in (action if isinstance(action, (list, tuple)) else [action])]

                proto_steps.append(
                    simulator_pb2.StepRequest(
                        env_id=s.get("env_id", "CartPole-v1"),
                        discrete_action=d_act,
                        continuous_action=c_act,
                        is_discrete=is_discrete,
                        step_index=s.get("step_index", 0),
                    )
                )

            req = simulator_pb2.BatchStepRequest(steps=proto_steps, batch_id=batch_id)
            resp = servicer.BatchStep(req, None)
            return {
                "batch_id": resp.batch_id,
                "total_steps": resp.total_steps,
                "elapsed_ms": resp.elapsed_ms,
                "average_step_latency_ms": resp.average_step_latency_ms,
                "responses": [
                    {
                        "env_id": r.env_id,
                        "observation": list(r.observation),
                        "reward": r.reward,
                        "done": r.done,
                        "truncated": r.truncated,
                        "info": dict(r.info),
                        "step_count": r.step_count,
                        "latency_ms": r.latency_ms,
                    }
                    for r in resp.responses
                ],
            }

    def stream_observations(
        self,
        env_id: str = "CartPole-v1",
        max_steps: int = 50,
        seed: Optional[int] = None,
        policy_type: str = "heuristic",
    ) -> List[Dict[str, Any]]:
        """Collect observation stream steps via gRPC or local fallback."""
        try:
            with SimulatorGRPCClient(self.target) as client:
                return list(client.stream_observations(
                    env_id=env_id,
                    max_steps=max_steps,
                    seed=seed,
                    policy_type=policy_type,
                ))
        except (grpc.RpcError, Exception) as exc:
            logger.debug(f"gRPC stream fallback: {exc}")
            servicer = self._get_fallback_servicer()
            req = simulator_pb2.StreamObservationsRequest(
                env_id=env_id,
                max_steps=max_steps,
                seed=seed if seed is not None else 0,
                policy_type=policy_type,
            )
            responses = []
            for resp in servicer.StreamObservations(req, None):
                responses.append({
                    "env_id": resp.env_id,
                    "observation": list(resp.observation),
                    "reward": resp.reward,
                    "done": resp.done,
                    "truncated": resp.truncated,
                    "info": dict(resp.info),
                    "step_count": resp.step_count,
                    "latency_ms": resp.latency_ms,
                })
            return responses

    def benchmark_throughput(
        self,
        env_id: str = "CartPole-v1",
        num_steps: int = 1000,
        batch_size: int = 32,
    ) -> Dict[str, Any]:
        """Perform throughput benchmarking via gRPC or local fallback."""
        try:
            with SimulatorGRPCClient(self.target) as client:
                return client.benchmark_throughput(
                    env_id=env_id,
                    num_steps=num_steps,
                    batch_size=batch_size,
                )
        except (grpc.RpcError, Exception) as exc:
            logger.debug(f"gRPC benchmark fallback: {exc}")
            servicer = self._get_fallback_servicer()
            req = simulator_pb2.BenchmarkThroughputRequest(
                env_id=env_id,
                num_steps=num_steps,
                batch_size=batch_size,
            )
            resp = servicer.BenchmarkThroughput(req, None)
            return {
                "env_id": resp.env_id,
                "total_steps": resp.total_steps,
                "elapsed_seconds": resp.elapsed_seconds,
                "steps_per_second": resp.steps_per_second,
                "protocol": f"{resp.protocol} (in-process fallback)",
                "mean_latency_ms": resp.mean_latency_ms,
            }


_gateway_instance: Optional[SimulatorServiceGateway] = None


def get_simulator_gateway() -> SimulatorServiceGateway:
    """Retrieve singleton simulator service gateway instance."""
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = SimulatorServiceGateway()
    return _gateway_instance
