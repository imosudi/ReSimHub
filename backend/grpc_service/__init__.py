"""
ReSimHub gRPC Simulator Service Package.

Exposes high-throughput Protocol Buffers interfaces for reinforcement learning
environment execution and observation streaming.
"""

from backend.grpc_service.simulator_service import SimulatorBridgeServicer
from backend.grpc_service.server import create_grpc_server, serve, GRPCServerRunner
from backend.grpc_service.client import SimulatorGRPCClient

__all__ = [
    "SimulatorBridgeServicer",
    "create_grpc_server",
    "serve",
    "GRPCServerRunner",
    "SimulatorGRPCClient",
]
