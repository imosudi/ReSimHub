"""
Python gRPC Client for ReSimHub Simulator Bridge.

Provides high-level programmatic access to the simulator service for training
workers, benchmarking routines, and FastAPI gateway proxy handlers.
"""

from typing import Dict, List, Optional, Any, Iterator
import grpc

from shared.proto import simulator_pb2, simulator_pb2_grpc


class SimulatorGRPCClient:
    """
    Client interface for interacting with the ReSimHub gRPC Simulator Bridge.
    """

    def __init__(
        self,
        target: str = "127.0.0.1:50051",
        channel: Optional[grpc.Channel] = None,
    ) -> None:
        self.target = target
        if channel is not None:
            self._channel = channel
            self._owns_channel = False
        else:
            self._channel = grpc.insecure_channel(
                self.target,
                options=[
                    ("grpc.max_send_message_length", 50 * 1024 * 1024),
                    ("grpc.max_receive_message_length", 50 * 1024 * 1024),
                ],
            )
            self._owns_channel = True

        self._stub = simulator_pb2_grpc.SimulatorBridgeStub(self._channel)

    def __enter__(self) -> "SimulatorGRPCClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def close(self) -> None:
        """Close communication channel if owned by this client instance."""
        if self._owns_channel and self._channel is not None:
            self._channel.close()

    def check_health(self, client_id: str = "python-client") -> Dict[str, Any]:
        """Query health and supported environment capabilities from the gRPC server."""
        request = simulator_pb2.HealthRequest(client_id=client_id)
        response: simulator_pb2.HealthResponse = self._stub.CheckHealth(request)
        return {
            "status": response.status,
            "version": response.version,
            "available_environments": list(response.available_environments),
            "uptime_seconds": response.uptime_seconds,
        }

    def reset(
        self,
        env_id: str = "CartPole-v1",
        seed: Optional[int] = None,
        options: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Reset the simulation environment and retrieve initial observation vector."""
        request = simulator_pb2.ResetRequest(
            env_id=env_id,
            seed=seed if seed is not None else 0,
            options=options or {},
        )
        response: simulator_pb2.ResetResponse = self._stub.Reset(request)
        return {
            "env_id": response.env_id,
            "observation": list(response.observation),
            "info": dict(response.info),
            "success": response.success,
        }

    def step(
        self,
        env_id: str = "CartPole-v1",
        action: Any = 0,
        is_discrete: bool = True,
        step_index: int = 0,
    ) -> Dict[str, Any]:
        """Execute a single simulation step with designated action."""
        if is_discrete:
            discrete_val = int(action)
            continuous_vals = []
        else:
            discrete_val = 0
            continuous_vals = [float(x) for x in (action if isinstance(action, (list, tuple)) else [action])]

        request = simulator_pb2.StepRequest(
            env_id=env_id,
            discrete_action=discrete_val,
            continuous_action=continuous_vals,
            is_discrete=is_discrete,
            step_index=step_index,
        )
        response: simulator_pb2.StepResponse = self._stub.Step(request)
        return {
            "env_id": response.env_id,
            "observation": list(response.observation),
            "reward": response.reward,
            "done": response.done,
            "truncated": response.truncated,
            "info": dict(response.info),
            "step_count": response.step_count,
            "latency_ms": response.latency_ms,
        }

    def batch_step(
        self,
        steps: List[Dict[str, Any]],
        batch_id: str = "",
    ) -> Dict[str, Any]:
        """Execute multiple environment steps concurrently in batch."""
        proto_steps = []
        for s in steps:
            env_id = s.get("env_id", "CartPole-v1")
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
                    env_id=env_id,
                    discrete_action=d_act,
                    continuous_action=c_act,
                    is_discrete=is_discrete,
                    step_index=s.get("step_index", 0),
                )
            )

        request = simulator_pb2.BatchStepRequest(
            steps=proto_steps,
            batch_id=batch_id,
        )
        response: simulator_pb2.BatchStepResponse = self._stub.BatchStep(request)

        formatted_responses = [
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
            for r in response.responses
        ]

        return {
            "batch_id": response.batch_id,
            "total_steps": response.total_steps,
            "elapsed_ms": response.elapsed_ms,
            "average_step_latency_ms": response.average_step_latency_ms,
            "responses": formatted_responses,
        }

    def stream_observations(
        self,
        env_id: str = "CartPole-v1",
        max_steps: int = 50,
        seed: Optional[int] = None,
        policy_type: str = "heuristic",
    ) -> Iterator[Dict[str, Any]]:
        """Yield streamed observation steps from the server."""
        request = simulator_pb2.StreamObservationsRequest(
            env_id=env_id,
            max_steps=max_steps,
            seed=seed if seed is not None else 0,
            policy_type=policy_type,
        )
        for response in self._stub.StreamObservations(request):
            yield {
                "env_id": response.env_id,
                "observation": list(response.observation),
                "reward": response.reward,
                "done": response.done,
                "truncated": response.truncated,
                "info": dict(response.info),
                "step_count": response.step_count,
                "latency_ms": response.latency_ms,
            }

    def benchmark_throughput(
        self,
        env_id: str = "CartPole-v1",
        num_steps: int = 1000,
        batch_size: int = 32,
    ) -> Dict[str, Any]:
        """Perform end-to-end throughput measurement over gRPC."""
        request = simulator_pb2.BenchmarkThroughputRequest(
            env_id=env_id,
            num_steps=num_steps,
            batch_size=batch_size,
        )
        response: simulator_pb2.BenchmarkThroughputResponse = self._stub.BenchmarkThroughput(request)
        return {
            "env_id": response.env_id,
            "total_steps": response.total_steps,
            "elapsed_seconds": response.elapsed_seconds,
            "steps_per_second": response.steps_per_second,
            "protocol": response.protocol,
            "mean_latency_ms": response.mean_latency_ms,
        }
