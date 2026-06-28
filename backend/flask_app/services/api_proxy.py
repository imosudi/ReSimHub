# backend/flask_app/services/api_proxy.py
import httpx
from typing import Dict, Optional

FASTAPI_BASE_URL = "http://127.0.0.1:8000"  # Update if deployed elsewhere

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
