# backend/flask_app/services/api_proxy.py
import os
import httpx
from typing import Dict, Optional

FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8000")

class FastAPIProxy:
    """
    Async proxy to communicate with FastAPI backend.
    """

    @staticmethod
    async def post_train(payload: Dict):
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{FASTAPI_BASE_URL}/orchestrate/train", json=payload)
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def get_task_status(task_id: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FASTAPI_BASE_URL}/orchestrate/tasks/{task_id}")
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def get_experiment_analytics(experiment_id: int):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FASTAPI_BASE_URL}/analytics/experiment/{experiment_id}")
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def get_recent_analytics(limit: int = 5):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FASTAPI_BASE_URL}/analytics/recent?limit={limit}")
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def post_environment(payload: Dict):
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{FASTAPI_BASE_URL}/environments/", json=payload)
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def get_environments():
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FASTAPI_BASE_URL}/environments/")
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def post_experiment(payload: Dict):
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{FASTAPI_BASE_URL}/experiments/", json=payload)
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def get_experiments():
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FASTAPI_BASE_URL}/experiments/")
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def post_benchmark_upload(files: Dict):
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{FASTAPI_BASE_URL}/benchmark/upload_model", files=files)
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def post_benchmark_run(payload: Dict):
        async with httpx.AsyncClient() as client:
            # Note: run expects Form parameters in FastAPI, not JSON!
            # Form params are passed via the 'data' argument in httpx.
            response = await client.post(f"{FASTAPI_BASE_URL}/benchmark/run", data=payload)
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def get_benchmark_recent(limit: int = 10):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FASTAPI_BASE_URL}/benchmark/recent?limit={limit}")
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def get_benchmark_compare(model_ids: str, env: Optional[str] = None):
        async with httpx.AsyncClient() as client:
            url = f"{FASTAPI_BASE_URL}/benchmark/compare?model_ids={model_ids}"
            if env:
                url += f"&env={env}"
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def post_schedule_batch(payload: Dict):
        """
        Dispatch a multi-agent parallel batch schedule request to FastAPI orchestrator.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{FASTAPI_BASE_URL}/orchestrate/batch", json=payload)
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def get_batch_status(batch_id: str):
        """
        Retrieve real-time consolidated status and metrics for a scheduled batch.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FASTAPI_BASE_URL}/orchestrate/batch/{batch_id}")
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def get_batches(limit: int = 20, offset: int = 0):
        """
        Retrieve paginated list of multi-agent batch schedules.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FASTAPI_BASE_URL}/orchestrate/batches?limit={limit}&offset={offset}")
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def get_checkpoints(
        task_id: Optional[str] = None,
        algo: Optional[str] = None,
        is_best: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0,
    ):
        """
        Retrieve paginated model checkpoints from FastAPI backend.
        """
        params = {"limit": limit, "offset": offset}
        if task_id:
            params["task_id"] = task_id
        if algo:
            params["algo"] = algo
        if is_best is not None:
            params["is_best"] = is_best

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FASTAPI_BASE_URL}/checkpoints", params=params)
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def get_checkpoint_by_id(checkpoint_id: str):
        """
        Retrieve model checkpoint details and integrity hash from FastAPI backend.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FASTAPI_BASE_URL}/checkpoints/{checkpoint_id}")
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def get_best_checkpoint(
        task_id: Optional[str] = None,
        algo: Optional[str] = None,
        env_name: Optional[str] = None,
    ):
        """
        Retrieve top-performing checkpoint from FastAPI backend.
        """
        params = {}
        if task_id:
            params["task_id"] = task_id
        if algo:
            params["algo"] = algo
        if env_name:
            params["env_name"] = env_name

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FASTAPI_BASE_URL}/checkpoints/best", params=params)
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def post_resume_checkpoint(checkpoint_id: str, payload: Dict):
        """
        Trigger training resumption from a model checkpoint.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{FASTAPI_BASE_URL}/checkpoints/{checkpoint_id}/resume",
                json=payload
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def get_simulator_health():
        """
        Query gRPC simulator health status via FastAPI bridge.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FASTAPI_BASE_URL}/simulator/health")
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def get_simulator_environments():
        """
        Query available simulation environments via FastAPI bridge.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FASTAPI_BASE_URL}/simulator/environments")
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def post_simulator_reset(payload: Dict):
        """
        Trigger environment reset via FastAPI bridge.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{FASTAPI_BASE_URL}/simulator/reset", json=payload)
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def post_simulator_step(payload: Dict):
        """
        Trigger single environment step via FastAPI bridge.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{FASTAPI_BASE_URL}/simulator/step", json=payload)
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def post_simulator_batch_step(payload: Dict):
        """
        Trigger batch step execution via FastAPI bridge.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{FASTAPI_BASE_URL}/simulator/batch_step", json=payload)
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def post_simulator_stream(payload: Dict):
        """
        Trigger observation trajectory stream via FastAPI bridge.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{FASTAPI_BASE_URL}/simulator/stream", json=payload)
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def post_simulator_benchmark(payload: Dict):
        """
        Trigger throughput benchmarking via FastAPI bridge.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{FASTAPI_BASE_URL}/simulator/benchmark", json=payload)
            response.raise_for_status()
            return response.json()


