"""
Simulator Bridge gRPC Servicer Implementation.

Provides high-throughput, low-latency Protocol Buffers execution for
reinforcement learning simulation environments and observation streaming.
"""

import time
import math
import random
import threading
from typing import Dict, List, Optional, Tuple, Any

import grpc
from shared.proto import simulator_pb2, simulator_pb2_grpc


class EnvironmentSession:
    """
    Manages in-memory state and physics integration for an active environment instance.
    """

    def __init__(self, env_id: str, seed: Optional[int] = None) -> None:
        self.env_id = env_id
        self.seed = seed
        self.rng = random.Random(seed)
        self.step_count = 0
        self.cumulative_reward = 0.0
        self.done = False
        self.state: List[float] = []
        self._initialise_state()

    def _initialise_state(self) -> None:
        """Initialise environment state vector according to environment type."""
        self.step_count = 0
        self.cumulative_reward = 0.0
        self.done = False

        if "CartPole" in self.env_id:
            # [cart_position, cart_velocity, pole_angle, pole_velocity]
            self.state = [self.rng.uniform(-0.05, 0.05) for _ in range(4)]
        elif "LunarLander" in self.env_id:
            # [x, y, vx, vy, angle, angular_velocity, left_leg_contact, right_leg_contact]
            self.state = [
                self.rng.uniform(-0.1, 0.1),
                1.4,
                self.rng.uniform(-0.05, 0.05),
                -0.1,
                self.rng.uniform(-0.02, 0.02),
                0.0,
                0.0,
                0.0,
            ]
        elif "Pendulum" in self.env_id:
            # [cos(theta), sin(theta), theta_dot]
            theta = self.rng.uniform(-math.pi, math.pi)
            theta_dot = self.rng.uniform(-1.0, 1.0)
            self.state = [math.cos(theta), math.sin(theta), theta_dot]
        elif "Acrobot" in self.env_id:
            # [cos(th1), sin(th1), cos(th2), sin(th2), dth1, dth2]
            th1 = self.rng.uniform(-0.1, 0.1)
            th2 = self.rng.uniform(-0.1, 0.1)
            self.state = [math.cos(th1), math.sin(th1), math.cos(th2), math.sin(th2), 0.0, 0.0]
        else:
            # Generic 4-dimensional continuous state vector
            self.state = [self.rng.uniform(-1.0, 1.0) for _ in range(4)]

    def reset(self, seed: Optional[int] = None) -> List[float]:
        """Reset environment session to starting state."""
        if seed is not None:
            self.seed = seed
            self.rng = random.Random(seed)
        self._initialise_state()
        return list(self.state)

    def step(
        self,
        discrete_action: int = 0,
        continuous_action: Optional[List[float]] = None,
        is_discrete: bool = True,
    ) -> Tuple[List[float], float, bool, bool, Dict[str, str]]:
        """
        Execute a simulation step and advance physical state.
        Returns (observation, reward, done, truncated, info).
        """
        self.step_count += 1
        truncated = False
        info = {
            "step_count": str(self.step_count),
            "env_id": self.env_id,
        }

        if "CartPole" in self.env_id:
            x, x_dot, theta, theta_dot = self.state
            force = 10.0 if discrete_action == 1 else -10.0
            costheta = math.cos(theta)
            sintheta = math.sin(theta)

            gravity = 9.8
            masscart = 1.0
            masspole = 0.1
            total_mass = masscart + masspole
            length = 0.5
            polemass_length = masspole * length

            temp = (force + polemass_length * theta_dot**2 * sintheta) / total_mass
            thetaacc = (gravity * sintheta - costheta * temp) / (
                length * (4.0 / 3.0 - masspole * costheta**2 / total_mass)
            )
            xacc = temp - polemass_length * thetaacc * costheta / total_mass

            dt = 0.02
            x = x + dt * x_dot
            x_dot = x_dot + dt * xacc
            theta = theta + dt * theta_dot
            theta_dot = theta_dot + dt * thetaacc

            self.state = [x, x_dot, theta, theta_dot]
            done = bool(x < -2.4 or x > 2.4 or theta < -0.2095 or theta > 0.2095)
            if self.step_count >= 500:
                truncated = True
                done = True

            reward = 1.0 if not done else 0.0
            self.cumulative_reward += reward
            self.done = done
            info["cumulative_reward"] = f"{self.cumulative_reward:.1f}"
            return list(self.state), reward, done, truncated, info

        elif "Pendulum" in self.env_id:
            cos_th, sin_th, th_dot = self.state
            u = continuous_action[0] if continuous_action else 0.0
            u = max(-2.0, min(2.0, float(u)))

            dt = 0.05
            g = 10.0
            m = 1.0
            length = 1.0

            current_th = math.atan2(sin_th, cos_th)
            new_th_dot = th_dot + (-3.0 * g / (2 * length) * math.sin(current_th + math.pi) + 3.0 / (m * length**2) * u) * dt
            new_th_dot = max(-8.0, min(8.0, new_th_dot))
            new_th = current_th + new_th_dot * dt

            self.state = [math.cos(new_th), math.sin(new_th), new_th_dot]
            norm_th = ((new_th + math.pi) % (2 * math.pi)) - math.pi
            costs = norm_th**2 + 0.1 * new_th_dot**2 + 0.001 * (u**2)
            reward = -float(costs)
            done = bool(self.step_count >= 200)
            truncated = done
            self.cumulative_reward += reward
            self.done = done
            info["cumulative_reward"] = f"{self.cumulative_reward:.2f}"
            return list(self.state), reward, done, truncated, info

        elif "LunarLander" in self.env_id:
            x, y, vx, vy, ang, ang_v, l_leg, r_leg = self.state
            dt = 0.02
            # Discrete actions: 0: do nothing, 1: fire left engine, 2: fire main engine, 3: fire right engine
            thrust = 0.0
            side_thrust = 0.0
            if discrete_action == 2:
                thrust = 0.3
            elif discrete_action == 1:
                side_thrust = -0.1
            elif discrete_action == 3:
                side_thrust = 0.1

            vy = vy - 0.05 * dt + thrust * dt
            vx = vx + side_thrust * dt
            y = max(0.0, y + vy)
            x = x + vx
            ang = ang + ang_v * dt

            done = False
            reward = 0.1
            if y <= 0.0:
                done = True
                reward = 100.0 if abs(vx) < 0.1 and abs(ang) < 0.1 else -100.0
            elif self.step_count >= 1000:
                done = True
                truncated = True

            self.state = [x, y, vx, vy, ang, ang_v, 1.0 if y <= 0 else 0.0, 1.0 if y <= 0 else 0.0]
            self.cumulative_reward += reward
            self.done = done
            info["cumulative_reward"] = f"{self.cumulative_reward:.2f}"
            return list(self.state), reward, done, truncated, info

        else:
            # Generic simulated dynamics
            step_noise = [self.rng.gauss(0.0, 0.02) for _ in self.state]
            action_val = float(discrete_action) if is_discrete else (continuous_action[0] if continuous_action else 0.0)
            self.state = [s * 0.95 + action_val * 0.01 + n for s, n in zip(self.state, step_noise)]
            reward = 1.0 - sum(abs(s) for s in self.state) * 0.1
            done = bool(self.step_count >= 100)
            truncated = done
            self.cumulative_reward += reward
            self.done = done
            info["cumulative_reward"] = f"{self.cumulative_reward:.2f}"
            return list(self.state), reward, done, truncated, info


class SimulatorBridgeServicer(simulator_pb2_grpc.SimulatorBridgeServicer):
    """
    gRPC Servicer handling simulator environments with high throughput.
    """

    AVAILABLE_ENVIRONMENTS = [
        "CartPole-v1",
        "LunarLander-v2",
        "Pendulum-v1",
        "Acrobot-v1",
        "MountainCar-v0",
    ]

    def __init__(self) -> None:
        self._sessions: Dict[str, EnvironmentSession] = {}
        self._lock = threading.Lock()
        self._start_time = time.time()

    def _get_or_create_session(self, env_id: str, seed: Optional[int] = None) -> EnvironmentSession:
        """Thread-safe retrieval or initialisation of an environment session."""
        with self._lock:
            if env_id not in self._sessions:
                self._sessions[env_id] = EnvironmentSession(env_id, seed=seed)
            return self._sessions[env_id]

    def CheckHealth(
        self,
        request: simulator_pb2.HealthRequest,
        context: grpc.ServicerContext,
    ) -> simulator_pb2.HealthResponse:
        """Respond with service operational health and supported environments."""
        uptime = int(time.time() - self._start_time)
        return simulator_pb2.HealthResponse(
            status="SERVING",
            version="1.0.0",
            available_environments=self.AVAILABLE_ENVIRONMENTS,
            uptime_seconds=uptime,
        )

    def Reset(
        self,
        request: simulator_pb2.ResetRequest,
        context: grpc.ServicerContext,
    ) -> simulator_pb2.ResetResponse:
        """Reset the designated environment and provide initial observation."""
        env_id = request.env_id or "CartPole-v1"
        seed = int(request.seed) if request.seed != 0 else None

        with self._lock:
            session = EnvironmentSession(env_id, seed=seed)
            self._sessions[env_id] = session

        observation = session.reset(seed=seed)
        info = {
            "initialised": "true",
            "seed": str(seed) if seed is not None else "none",
        }
        for k, v in request.options.items():
            info[f"opt_{k}"] = str(v)

        return simulator_pb2.ResetResponse(
            env_id=env_id,
            observation=observation,
            info=info,
            success=True,
        )

    def Step(
        self,
        request: simulator_pb2.StepRequest,
        context: grpc.ServicerContext,
    ) -> simulator_pb2.StepResponse:
        """Perform a single environment transition step."""
        t_start = time.perf_counter()
        env_id = request.env_id or "CartPole-v1"
        session = self._get_or_create_session(env_id)

        obs, reward, done, truncated, info = session.step(
            discrete_action=int(request.discrete_action),
            continuous_action=list(request.continuous_action),
            is_discrete=request.is_discrete,
        )
        latency_ms = (time.perf_counter() - t_start) * 1000.0

        return simulator_pb2.StepResponse(
            env_id=env_id,
            observation=obs,
            reward=float(reward),
            done=done,
            truncated=truncated,
            info=info,
            step_count=session.step_count,
            latency_ms=latency_ms,
        )

    def BatchStep(
        self,
        request: simulator_pb2.BatchStepRequest,
        context: grpc.ServicerContext,
    ) -> simulator_pb2.BatchStepResponse:
        """Execute multiple environment steps in rapid batch execution."""
        t_start = time.perf_counter()
        responses: List[simulator_pb2.StepResponse] = []

        for step_req in request.steps:
            env_id = step_req.env_id or "CartPole-v1"
            session = self._get_or_create_session(env_id)
            step_t0 = time.perf_counter()

            obs, reward, done, truncated, info = session.step(
                discrete_action=int(step_req.discrete_action),
                continuous_action=list(step_req.continuous_action),
                is_discrete=step_req.is_discrete,
            )
            step_latency_ms = (time.perf_counter() - step_t0) * 1000.0

            responses.append(
                simulator_pb2.StepResponse(
                    env_id=env_id,
                    observation=obs,
                    reward=float(reward),
                    done=done,
                    truncated=truncated,
                    info=info,
                    step_count=session.step_count,
                    latency_ms=step_latency_ms,
                )
            )

        elapsed_ms = (time.perf_counter() - t_start) * 1000.0
        total_steps = len(responses)
        avg_latency_ms = (elapsed_ms / total_steps) if total_steps > 0 else 0.0

        return simulator_pb2.BatchStepResponse(
            responses=responses,
            total_steps=total_steps,
            elapsed_ms=elapsed_ms,
            average_step_latency_ms=avg_latency_ms,
            batch_id=request.batch_id,
        )

    def StreamObservations(
        self,
        request: simulator_pb2.StreamObservationsRequest,
        context: grpc.ServicerContext,
    ):
        """Stream consecutive state transitions and observations over gRPC."""
        env_id = request.env_id or "CartPole-v1"
        max_steps = request.max_steps if request.max_steps > 0 else 50
        seed = int(request.seed) if request.seed != 0 else None
        policy_type = request.policy_type or "heuristic"

        session = self._get_or_create_session(env_id, seed=seed)
        session.reset(seed=seed)

        for step_idx in range(max_steps):
            t_start = time.perf_counter()

            # Determine action based on policy
            if policy_type == "random":
                action = session.rng.randint(0, 1)
            elif policy_type == "zero":
                action = 0
            else:
                # Heuristic policy for balancing CartPole
                if "CartPole" in env_id and len(session.state) >= 4:
                    theta = session.state[2]
                    action = 1 if theta > 0 else 0
                else:
                    action = session.rng.randint(0, 1)

            obs, reward, done, truncated, info = session.step(
                discrete_action=action,
                is_discrete=True,
            )
            latency_ms = (time.perf_counter() - t_start) * 1000.0

            yield simulator_pb2.StepResponse(
                env_id=env_id,
                observation=obs,
                reward=float(reward),
                done=done,
                truncated=truncated,
                info=info,
                step_count=session.step_count,
                latency_ms=latency_ms,
            )

            if done:
                break

    def BenchmarkThroughput(
        self,
        request: simulator_pb2.BenchmarkThroughputRequest,
        context: grpc.ServicerContext,
    ) -> simulator_pb2.BenchmarkThroughputResponse:
        """Measure end-to-end simulator stepping throughput."""
        env_id = request.env_id or "CartPole-v1"
        num_steps = max(1, request.num_steps or 1000)
        session = self._get_or_create_session(env_id)
        session.reset()

        t_start = time.perf_counter()
        latencies_ms = []

        for _ in range(num_steps):
            s_t0 = time.perf_counter()
            action = 1 if session.step_count % 2 == 0 else 0
            session.step(discrete_action=action, is_discrete=True)
            if session.done:
                session.reset()
            latencies_ms.append((time.perf_counter() - s_t0) * 1000.0)

        elapsed = time.perf_counter() - t_start
        steps_per_sec = num_steps / elapsed if elapsed > 0 else 0.0
        mean_lat = sum(latencies_ms) / len(latencies_ms) if latencies_ms else 0.0

        return simulator_pb2.BenchmarkThroughputResponse(
            env_id=env_id,
            total_steps=num_steps,
            elapsed_seconds=elapsed,
            steps_per_second=steps_per_sec,
            protocol="gRPC/Protobuf",
            mean_latency_ms=mean_lat,
        )
