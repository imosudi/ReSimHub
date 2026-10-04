# tests/test_grpc_bridge.py
"""
Unit and integration test suite for gRPC Simulator Bridge.
Validates:
  1. Servicer health inspection and environment discovery
  2. Deterministic environment initialisation and reset
  3. Single-step transitions for discrete and continuous action spaces
  4. Vectorised batch step execution and timing metrics
  5. Live observation streaming over gRPC generator streams
  6. Simulator throughput benchmarking routine
  7. Live gRPC server and client network communication on ephemeral ports
  8. FastAPI REST-to-gRPC simulator endpoints
  9. Flask API gateway simulator proxy routes
"""

from unittest.mock import patch
from fastapi.testclient import TestClient

from shared.proto import simulator_pb2
from backend.grpc_service.simulator_service import SimulatorBridgeServicer
from backend.grpc_service.server import GRPCServerRunner
from backend.grpc_service.client import SimulatorGRPCClient
from backend.fastapi_app.main import app as fastapi_app
from backend.flask_app import app as flask_app

fastapi_client = TestClient(fastapi_app)
flask_test_client = flask_app.test_client()


def test_grpc_servicer_health():
    """Verify SimulatorBridgeServicer health status and supported environments."""
    servicer = SimulatorBridgeServicer()
    req = simulator_pb2.HealthRequest(client_id="test-client")
    resp = servicer.CheckHealth(req, None)

    assert resp.status == "SERVING"
    assert resp.version == "1.0.0"
    assert "CartPole-v1" in resp.available_environments
    assert "LunarLander-v2" in resp.available_environments
    assert resp.uptime_seconds >= 0


def test_grpc_servicer_reset():
    """Verify environment reset initialisation and observation dimensionality."""
    servicer = SimulatorBridgeServicer()
    req = simulator_pb2.ResetRequest(
        env_id="CartPole-v1",
        seed=42,
        options={"difficulty": "normal"},
    )
    resp = servicer.Reset(req, None)

    assert resp.env_id == "CartPole-v1"
    assert resp.success is True
    assert len(resp.observation) == 4
    assert resp.info["initialised"] == "true"
    assert resp.info["seed"] == "42"
    assert resp.info["opt_difficulty"] == "normal"


def test_grpc_servicer_step_discrete():
    """Verify single step transition in discrete action space."""
    servicer = SimulatorBridgeServicer()
    # Reset first
    reset_req = simulator_pb2.ResetRequest(env_id="CartPole-v1", seed=10)
    servicer.Reset(reset_req, None)

    step_req = simulator_pb2.StepRequest(
        env_id="CartPole-v1",
        discrete_action=1,
        is_discrete=True,
        step_index=1,
    )
    step_resp = servicer.Step(step_req, None)

    assert step_resp.env_id == "CartPole-v1"
    assert len(step_resp.observation) == 4
    assert step_resp.reward >= 0.0
    assert isinstance(step_resp.done, bool)
    assert step_resp.step_count == 1
    assert step_resp.latency_ms >= 0.0


def test_grpc_servicer_step_continuous():
    """Verify single step transition in continuous action space (Pendulum-v1)."""
    servicer = SimulatorBridgeServicer()
    reset_req = simulator_pb2.ResetRequest(env_id="Pendulum-v1", seed=7)
    reset_resp = servicer.Reset(reset_req, None)
    assert len(reset_resp.observation) == 3

    step_req = simulator_pb2.StepRequest(
        env_id="Pendulum-v1",
        continuous_action=[-1.5],
        is_discrete=False,
        step_index=1,
    )
    step_resp = servicer.Step(step_req, None)

    assert step_resp.env_id == "Pendulum-v1"
    assert len(step_resp.observation) == 3
    assert step_resp.reward < 0.0  # Pendulum costs are negative
    assert step_resp.step_count == 1


def test_grpc_servicer_batch_step():
    """Verify high-throughput batch stepping execution and latency aggregation."""
    servicer = SimulatorBridgeServicer()
    reset_req = simulator_pb2.ResetRequest(env_id="CartPole-v1", seed=1)
    servicer.Reset(reset_req, None)

    steps = [
        simulator_pb2.StepRequest(
            env_id="CartPole-v1",
            discrete_action=i % 2,
            is_discrete=True,
            step_index=i,
        )
        for i in range(10)
    ]
    batch_req = simulator_pb2.BatchStepRequest(steps=steps, batch_id="batch-test-01")
    batch_resp = servicer.BatchStep(batch_req, None)

    assert batch_resp.batch_id == "batch-test-01"
    assert batch_resp.total_steps == 10
    assert len(batch_resp.responses) == 10
    assert batch_resp.elapsed_ms > 0.0
    assert batch_resp.average_step_latency_ms >= 0.0


def test_grpc_servicer_stream_observations():
    """Verify observation stream generation and sequence termination."""
    servicer = SimulatorBridgeServicer()
    stream_req = simulator_pb2.StreamObservationsRequest(
        env_id="CartPole-v1",
        max_steps=15,
        seed=123,
        policy_type="heuristic",
    )
    stream_generator = servicer.StreamObservations(stream_req, None)
    collected_steps = list(stream_generator)

    assert len(collected_steps) > 0
    assert len(collected_steps) <= 15
    first_step = collected_steps[0]
    assert first_step.env_id == "CartPole-v1"
    assert len(first_step.observation) == 4


def test_grpc_servicer_benchmark_throughput():
    """Verify throughput profiling computes valid steps per second."""
    servicer = SimulatorBridgeServicer()
    bench_req = simulator_pb2.BenchmarkThroughputRequest(
        env_id="CartPole-v1",
        num_steps=100,
        batch_size=10,
    )
    bench_resp = servicer.BenchmarkThroughput(bench_req, None)

    assert bench_resp.env_id == "CartPole-v1"
    assert bench_resp.total_steps == 100
    assert bench_resp.elapsed_seconds > 0.0
    assert bench_resp.steps_per_second > 0.0
    assert bench_resp.protocol == "gRPC/Protobuf"
    assert bench_resp.mean_latency_ms >= 0.0


def test_grpc_live_server_and_client_over_wire():
    """Verify live gRPC server execution and client remote procedure calls on an ephemeral port."""
    # Use port 0 to bind to an available ephemeral port
    runner = GRPCServerRunner(host="127.0.0.1", port=0)
    bound_port = runner.start()
    assert bound_port > 0

    try:
        with SimulatorGRPCClient(target=f"127.0.0.1:{bound_port}") as client:
            # 1. Health
            health = client.check_health()
            assert health["status"] == "SERVING"
            assert "CartPole-v1" in health["available_environments"]

            # 2. Reset
            reset_data = client.reset(env_id="CartPole-v1", seed=99)
            assert reset_data["success"] is True
            assert len(reset_data["observation"]) == 4

            # 3. Single step
            step_data = client.step(env_id="CartPole-v1", action=1, is_discrete=True)
            assert len(step_data["observation"]) == 4
            assert step_data["step_count"] == 1

            # 4. Batch step
            batch_data = client.batch_step(
                steps=[
                    {"env_id": "CartPole-v1", "action": 0, "is_discrete": True},
                    {"env_id": "CartPole-v1", "action": 1, "is_discrete": True},
                ],
                batch_id="wire-batch-1",
            )
            assert batch_data["total_steps"] == 2
            assert len(batch_data["responses"]) == 2

            # 5. Observation stream
            stream_steps = list(client.stream_observations(env_id="CartPole-v1", max_steps=10))
            assert len(stream_steps) > 0
            assert len(stream_steps) <= 10

            # 6. Benchmark
            bench = client.benchmark_throughput(env_id="CartPole-v1", num_steps=50, batch_size=10)
            assert bench["total_steps"] == 50
            assert bench["steps_per_second"] > 0.0
    finally:
        runner.stop(grace=0.5)


def test_fastapi_simulator_endpoints():
    """Verify FastAPI REST bridge endpoints interacting with the simulator service."""
    # 1. Health
    res_health = fastapi_client.get("/simulator/health")
    assert res_health.status_code == 200
    assert "status" in res_health.json()

    # 2. Environments
    res_envs = fastapi_client.get("/simulator/environments")
    assert res_envs.status_code == 200
    envs = res_envs.json()
    assert isinstance(envs, list)
    assert "CartPole-v1" in envs

    # 3. Reset
    res_reset = fastapi_client.post(
        "/simulator/reset",
        json={"env_id": "CartPole-v1", "seed": 42, "options": {"mode": "eval"}},
    )
    assert res_reset.status_code == 200
    reset_data = res_reset.json()
    assert reset_data["env_id"] == "CartPole-v1"
    assert len(reset_data["observation"]) == 4
    assert reset_data["success"] is True

    # 4. Step
    res_step = fastapi_client.post(
        "/simulator/step",
        json={"env_id": "CartPole-v1", "action": 0, "is_discrete": True},
    )
    assert res_step.status_code == 200
    step_data = res_step.json()
    assert step_data["env_id"] == "CartPole-v1"
    assert len(step_data["observation"]) == 4
    assert "reward" in step_data

    # 5. Batch Step
    res_batch = fastapi_client.post(
        "/simulator/batch_step",
        json={
            "batch_id": "fastapi-batch-01",
            "steps": [
                {"env_id": "CartPole-v1", "action": 0, "is_discrete": True},
                {"env_id": "CartPole-v1", "action": 1, "is_discrete": True},
            ],
        },
    )
    assert res_batch.status_code == 200
    batch_data = res_batch.json()
    assert batch_data["total_steps"] == 2
    assert len(batch_data["responses"]) == 2

    # 6. Stream
    res_stream = fastapi_client.post(
        "/simulator/stream",
        json={"env_id": "CartPole-v1", "max_steps": 12, "policy_type": "heuristic"},
    )
    assert res_stream.status_code == 200
    stream_data = res_stream.json()
    assert stream_data["total_steps"] > 0
    assert len(stream_data["steps"]) == stream_data["total_steps"]

    # 7. Benchmark
    res_bench = fastapi_client.post(
        "/simulator/benchmark",
        json={"env_id": "CartPole-v1", "num_steps": 50, "batch_size": 10},
    )
    assert res_bench.status_code == 200
    bench_data = res_bench.json()
    assert bench_data["total_steps"] == 50
    assert bench_data["steps_per_second"] > 0.0


def test_flask_gateway_simulator_proxy():
    """Verify Flask gateway proxy routes to FastAPI simulator endpoints."""
    # Mock FastAPI responses for Flask proxy tests
    with patch(
        "backend.flask_app.services.api_proxy.FastAPIProxy.get_simulator_health",
        return_value={"status": "SERVING", "version": "1.0.0", "available_environments": ["CartPole-v1"]},
    ), patch(
        "backend.flask_app.services.api_proxy.FastAPIProxy.get_simulator_environments",
        return_value=["CartPole-v1", "LunarLander-v2"],
    ), patch(
        "backend.flask_app.services.api_proxy.FastAPIProxy.post_simulator_reset",
        return_value={"env_id": "CartPole-v1", "observation": [0.0, 0.0, 0.0, 0.0], "info": {}, "success": True},
    ), patch(
        "backend.flask_app.services.api_proxy.FastAPIProxy.post_simulator_step",
        return_value={"env_id": "CartPole-v1", "observation": [0.0, 0.0, 0.0, 0.0], "reward": 1.0, "done": False, "truncated": False, "info": {}, "step_count": 1, "latency_ms": 0.1},
    ), patch(
        "backend.flask_app.services.api_proxy.FastAPIProxy.post_simulator_batch_step",
        return_value={"batch_id": "flask-batch", "total_steps": 1, "elapsed_ms": 0.5, "average_step_latency_ms": 0.5, "responses": []},
    ), patch(
        "backend.flask_app.services.api_proxy.FastAPIProxy.post_simulator_stream",
        return_value={"env_id": "CartPole-v1", "total_steps": 10, "cumulative_reward": 10.0, "steps": []},
    ), patch(
        "backend.flask_app.services.api_proxy.FastAPIProxy.post_simulator_benchmark",
        return_value={"env_id": "CartPole-v1", "total_steps": 100, "elapsed_seconds": 0.01, "steps_per_second": 10000.0, "protocol": "gRPC/Protobuf", "mean_latency_ms": 0.1},
    ):
        # 1. Health
        res_health = flask_test_client.get("/api/v1/simulator/health")
        assert res_health.status_code == 200
        assert res_health.get_json()["status"] == "SERVING"

        # 2. Environments
        res_envs = flask_test_client.get("/api/v1/simulator/environments")
        assert res_envs.status_code == 200
        assert "CartPole-v1" in res_envs.get_json()

        # 3. Reset
        res_reset = flask_test_client.post("/api/v1/simulator/reset", json={"env_id": "CartPole-v1"})
        assert res_reset.status_code == 200
        assert res_reset.get_json()["success"] is True

        # 4. Step
        res_step = flask_test_client.post("/api/v1/simulator/step", json={"env_id": "CartPole-v1", "action": 1})
        assert res_step.status_code == 200
        assert res_step.get_json()["step_count"] == 1

        # 5. Batch Step
        res_batch = flask_test_client.post("/api/v1/simulator/batch_step", json={"steps": []})
        assert res_batch.status_code == 200
        assert res_batch.get_json()["batch_id"] == "flask-batch"

        # 6. Stream
        res_stream = flask_test_client.post("/api/v1/simulator/stream", json={"env_id": "CartPole-v1"})
        assert res_stream.status_code == 200
        assert res_stream.get_json()["total_steps"] == 10

        # 7. Benchmark
        res_bench = flask_test_client.post("/api/v1/simulator/benchmark", json={"env_id": "CartPole-v1"})
        assert res_bench.status_code == 200
        assert res_bench.get_json()["steps_per_second"] == 10000.0
