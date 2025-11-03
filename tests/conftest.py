"""
conftest.py
-----------
Shared pytest fixtures and environment setup for Stage 6 Benchmarking tests.

This ensures:
  - Redis (if running) is cleared between test sessions.
  - The local storage/models directory is reset.
  - Test logging is initialised.
"""

import os
import pytest
import shutil
import redis
from pathlib import Path

from backend.fastapi_app.core.config import CacheConfig

cache_config = CacheConfig()


# -------------------------------------------------------------------
# GLOBAL CONFIG
# -------------------------------------------------------------------
STORAGE_DIR = Path("storage/models")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

REDIS_URL = os.getenv("REDIS_URL", cache_config.url+'3') # "redis://localhost:6379/3")


@pytest.fixture(scope="session", autouse=True)
def clean_test_environment():
    """
    Automatically runs once per test session before any test.
    Cleans Redis DB (if reachable) and resets storage directory.
    """
    print("\n🔧 Cleaning test environment...")

    # 1️⃣ Clean Redis (if available)
    try:
        redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
        redis_client.flushdb()
        print("🧹 Redis database flushed (db=3)")
    except Exception as e:
        print(f"⚠️ Redis unavailable or not running: {e}")

    # 2️⃣ Clean storage/models directory
    if STORAGE_DIR.exists():
        shutil.rmtree(STORAGE_DIR)
        print(f"🧹 Removed old storage directory: {STORAGE_DIR}")

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📂 Created fresh storage directory: {STORAGE_DIR}")

    yield

    # Post-test cleanup (optional)
    print("\n🧩 Tests completed — environment teardown done.")
