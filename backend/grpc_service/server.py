"""
gRPC Server Runner and Lifecycle Management for ReSimHub Simulator Bridge.

Binds the SimulatorBridgeServicer to a high-concurrency ThreadPoolExecutor and
manages graceful startup and shutdown.
"""

import sys
import time
import logging
from concurrent import futures
from typing import Optional, Tuple

import grpc
from shared.proto import simulator_pb2_grpc
from backend.grpc_service.simulator_service import SimulatorBridgeServicer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("SimulatorGRPCServer")


class GRPCServerRunner:
    """
    Manages the lifecycle of the gRPC Simulator Bridge server.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 50051, max_workers: int = 10) -> None:
        self.host = host
        self.port = port
        self.max_workers = max_workers
        self.server: Optional[grpc.Server] = None
        self.servicer: Optional[SimulatorBridgeServicer] = None
        self._actual_port: int = port

    def start(self) -> int:
        """
        Initialise and start the gRPC server asynchronously.
        Returns the bound port (especially useful when port 0 is passed for testing).
        """
        self.server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=self.max_workers),
            options=[
                ("grpc.max_send_message_length", 50 * 1024 * 1024),
                ("grpc.max_receive_message_length", 50 * 1024 * 1024),
            ],
        )
        self.servicer = SimulatorBridgeServicer()
        simulator_pb2_grpc.add_SimulatorBridgeServicer_to_server(self.servicer, self.server)

        bind_addr = f"{self.host}:{self.port}"
        self._actual_port = self.server.add_insecure_port(bind_addr)
        self.server.start()
        logger.info(f"SimulatorBridge gRPC server active on {self.host}:{self._actual_port}")
        return self._actual_port

    def stop(self, grace: float = 2.0) -> None:
        """Gracefully stop the server with designated grace period in seconds."""
        if self.server:
            logger.info("Stopping SimulatorBridge gRPC server...")
            self.server.stop(grace=grace)
            self.server = None
            logger.info("SimulatorBridge gRPC server stopped.")

    @property
    def bound_port(self) -> int:
        """Return the active bound port."""
        return self._actual_port


def create_grpc_server(
    host: str = "0.0.0.0", port: int = 50051, max_workers: int = 10
) -> Tuple[grpc.Server, int, SimulatorBridgeServicer]:
    """
    Convenience factory to construct, bind, and return an unstarted or started gRPC server.
    """
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=max_workers),
        options=[
            ("grpc.max_send_message_length", 50 * 1024 * 1024),
            ("grpc.max_receive_message_length", 50 * 1024 * 1024),
        ],
    )
    servicer = SimulatorBridgeServicer()
    simulator_pb2_grpc.add_SimulatorBridgeServicer_to_server(servicer, server)
    bound_port = server.add_insecure_port(f"{host}:{port}")
    return server, bound_port, servicer


def serve(host: str = "0.0.0.0", port: int = 50051, max_workers: int = 10) -> None:
    """
    Blocking server runner for production or standalone process deployment.
    """
    runner = GRPCServerRunner(host=host, port=port, max_workers=max_workers)
    runner.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        runner.stop(grace=1.0)
        sys.exit(0)


if __name__ == "__main__":
    serve()
