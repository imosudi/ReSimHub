
# backend/fastapi_app/services/benchmark_service.py
import uuid
from pathlib import Path
from datetime import datetime
import random
import pandas as pd
import redis
import json
from backend.fastapi_app.core.config import CacheConfig
from shared.utils.logger import get_logger

log = get_logger("BenchmarkService")


cache_config = CacheConfig()

# Storage paths
UPLOAD_DIR = Path("storage/models")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Lightweight Redis metadata store (optional - used if Redis available)
try:
    redis_client = redis.Redis.from_url(cache_config.url+'3', decode_resposes=True) # "redis://localhost:6379/3", decode_responses=True)
    redis_client.ping()
    USE_REDIS = True
except Exception:
    redis_client = None
    USE_REDIS = False
    log.warning("Redis not available; benchmark metadata will only live on disk (no Redis sync).")


class BenchmarkService:
    @staticmethod
    def save_model_file(upload_file) -> str:
        """
        Save uploaded file to storage and return a generated model_id.
        """
        model_id = f"mdl_{uuid.uuid4().hex[:8]}"
        extension = Path(upload_file.filename).suffix or ".bin"
        out_path = UPLOAD_DIR / f"{model_id}{extension}"

        # write the file
        with open(out_path, "wb") as f:
            content = upload_file.file.read()
            f.write(content)

        uploaded_at = datetime.utcnow().isoformat()
        metadata = {
            "model_id": model_id,
            "filename": upload_file.filename,
            "path": str(out_path),
            "uploaded_at": uploaded_at,
        }

        if USE_REDIS:
            redis_client.hset(f"benchmark:meta:{model_id}", mapping=metadata)
        else:
            # fallback: write small metadata file
            meta_path = UPLOAD_DIR / f"{model_id}.meta.json"
            meta_path.write_text(json.dumps(metadata))

        log.info(f"Model saved: {out_path} (model_id={model_id})")
        return model_id, metadata

    @staticmethod
    def run_benchmark_simulation(model_id: str, env_name: str, episodes: int = 50):
        """
        Run a simulated evaluation for a model.
        Produces a list of per-episode rewards (for demonstration).
        In real use-case, load model and run environment episodes to collect rewards & latencies.
        """
        # Simulate per-episode rewards and per-episode latency
        rewards = [round(random.uniform(150, 260) + random.gauss(0, 8), 2) for _ in range(episodes)]
        latencies = [round(random.uniform(10, 40) + random.gauss(0, 2), 2) for _ in range(episodes)]

        df = pd.DataFrame({"reward": rewards, "latency_ms": latencies})
        mean_reward = round(df["reward"].mean(), 2)
        std_reward = round(df["reward"].std(), 2)
        median_reward = round(df["reward"].median(), 2)
        avg_latency = round(df["latency_ms"].mean(), 2)

        result = {
            "model_id": model_id,
            "env_name": env_name,
            "mean_reward": mean_reward,
            "std_reward": std_reward,
            "median_reward": median_reward,
            "latency_ms": avg_latency,
            "total_episodes": episodes,
            "status": "completed",
            "evaluated_at": datetime.utcnow().isoformat(),
        }

        # Store result in Redis for quick lookup (optional)
        if USE_REDIS:
            redis_client.hset(f"benchmark:result:{model_id}:{env_name}", mapping=result)
            redis_client.lpush("benchmark:recent_results", json.dumps(result))
        else:
            # fallback to file
            out = UPLOAD_DIR / f"{model_id}_{env_name}_result.json"
            out.write_text(json.dumps(result))

        log.info(f"Benchmark simulated for model={model_id} env={env_name}: mean_reward={mean_reward}")
        return result

    @staticmethod
    def list_recent_results(limit: int = 10):
        """
        Return recent benchmark results from Redis or local storage.
        """
        if USE_REDIS:
            items = redis_client.lrange("benchmark:recent_results", 0, limit - 1)
            return [json.loads(i) for i in items]
        else:
            results = []
            for p in sorted(UPLOAD_DIR.glob("*_result.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
                try:
                    results.append(json.loads(p.read_text()))
                except Exception:
                    continue
            return results

    @staticmethod
    def compare_models(model_ids: list, env_name: str = None):
        """
        Compare a list of model_ids by mean_reward. If env_name provided, compare results for that env.
        Safely handles np.float64(...) strings and missing values.
        """

        def _safe_float(value):
                """Convert np.float64(...) or str to plain float safely."""
                if isinstance(value, (float, int)):
                    return float(value)
                if isinstance(value, str):
                    # Clean up common NumPy-like string wrappers
                    value = (
                        value.replace("np.float64(", "")
                            .replace("np.float32(", "")
                            .replace("Decimal(", "")
                            .replace(")", "")
                            .strip()
                    )
                    try:
                        return float(value)
                    except ValueError:
                        return 0.0
                return 0.0

        records = []

        if USE_REDIS:
            for mid in model_ids:
                if env_name:
                    key = f"benchmark:result:{mid}:{env_name}"
                    row = redis_client.hgetall(key)
                    if row:
                        # Normalise numeric fields
                        row["mean_reward"] = _safe_float(row.get("mean_reward", 0))
                        row["std_reward"] = _safe_float(row.get("std_reward", 0))
                        row["median_reward"] = _safe_float(row.get("median_reward", 0))
                        row["latency_ms"] = _safe_float(row.get("latency_ms", 0))
                        records.append(row)
                else:
                    # Retrieve all results for this model
                    pattern = f"benchmark:result:{mid}:*"
                    for k in redis_client.keys(pattern):
                        row = redis_client.hgetall(k)
                        if row:
                            row["mean_reward"] = _safe_float(row.get("mean_reward", 0))
                            row["std_reward"] = _safe_float(row.get("std_reward", 0))
                            row["median_reward"] = _safe_float(row.get("median_reward", 0))
                            row["latency_ms"] = _safe_float(row.get("latency_ms", 0))
                            records.append(row)
        else:
            # Fallback: read JSON result files
            for mid in model_ids:
                for p in UPLOAD_DIR.glob(f"{mid}_*_result.json"):
                    try:
                        r = json.loads(p.read_text())
                        # Normalise numeric fields from JSON
                        r["mean_reward"] = _safe_float(r.get("mean_reward", 0))
                        r["std_reward"] = _safe_float(r.get("std_reward", 0))
                        r["median_reward"] = _safe_float(r.get("median_reward", 0))
                        r["latency_ms"] = _safe_float(r.get("latency_ms", 0))
                        records.append(r)
                    except Exception as e:
                        log.warning(f"Skipping invalid benchmark file {p}: {e}")
                        continue

        if not records:
            return {"error": "No benchmark records found for given model_ids"}

        # Convert to DataFrame and sort
        df = pd.DataFrame(records)
        df_sorted = df.sort_values(by="mean_reward", ascending=False)

        # Optional: add summary
        summary = {
            "env_name": env_name or "mixed",
            "metric": "mean_reward",
            "best_model": df_sorted.iloc[0]["model_id"],
            "best_score": float(df_sorted.iloc[0]["mean_reward"]),
        }

        return {
            "comparison_summary": summary,
            "models": df_sorted.to_dict(orient="records")
        }

