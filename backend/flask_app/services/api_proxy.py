
# backend/flask_app/services/api_proxy.py
import httpx
from typing import Dict

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
