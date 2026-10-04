# backend/fastapi_app/services/benchmark_service.py
import uuid
from pathlib import Path
from datetime import datetime
import random
import pandas as pd
import redis
import json
from typing import Optional, List, Dict, Any

from backend.fastapi_app.core.config import CacheConfig
from backend.fastapi_app.core.db import SessionLocal
from shared.models.benchmark_model import BenchmarkRecord, ModelMetadata
from shared.utils.logger import get_logger

log = get_logger("BenchmarkService")

cache_config = CacheConfig()

# Storage paths
UPLOAD_DIR = Path("storage/models")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Lightweight Redis metadata store (optional - used if Redis available)
try:
    base_url = cache_config.url
    if not base_url.endswith("/"):
        base_url += "/"
    redis_client = redis.Redis.from_url(f"{base_url}3", decode_responses=True)
    redis_client.ping()
    USE_REDIS = True
except Exception:
    redis_client = None
    USE_REDIS = False
    log.warning("Redis not available; benchmark metadata will only live on disk and DB.")


class BenchmarkService:
    @staticmethod
    def save_model_file(upload_file) -> tuple:
        """
        Save uploaded file to storage and persist metadata to DB and Redis.
        """
        model_id = f"mdl_{uuid.uuid4().hex[:8]}"
        extension = Path(upload_file.filename).suffix or ".bin"
        out_path = UPLOAD_DIR / f"{model_id}{extension}"

        # Write the file
        content = upload_file.file.read()
        with open(out_path, "wb") as f:
            f.write(content)

        uploaded_at = datetime.utcnow().isoformat()
        metadata = {
            "model_id": model_id,
            "filename": upload_file.filename,
            "path": str(out_path),
            "file_size": len(content),
            "uploaded_at": uploaded_at,
        }

        # 1. Persist to Database
        try:
            db = SessionLocal()
            meta_record = ModelMetadata(
                model_id=model_id,
                filename=upload_file.filename,
                file_path=str(out_path),
                file_size_bytes=len(content),
                uploaded_at=datetime.utcnow()
            )
            db.add(meta_record)
            db.commit()
            db.close()
            log.info(f"Model metadata persisted to database: {model_id}")
        except Exception as e:
            log.warning(f"Could not persist ModelMetadata to database: {e}")

        # 2. Persist to Redis (fast cache)
        if USE_REDIS:
            try:
                redis_client.hset(f"benchmark:meta:{model_id}", mapping=metadata)
            except Exception as e:
                log.warning(f"Failed to cache model metadata in Redis: {e}")
        else:
            # Fallback: write small metadata file
            meta_path = UPLOAD_DIR / f"{model_id}.meta.json"
            meta_path.write_text(json.dumps(metadata))

        log.info(f"Model saved: {out_path} (model_id={model_id})")
        return model_id, metadata

    @staticmethod
    def run_benchmark_simulation(model_id: str, env_name: str, episodes: int = 50) -> Dict[str, Any]:
        """
        Run a simulated evaluation for a model computing comprehensive RL metrics:
        - Mean, Standard Deviation, Median
        - Min & Max reward bounds
        - Interquartile Mean (IQM - 25% trimmed mean across interquartile range)
        - Success Rate (% episodes >= benchmark threshold)
        - Conditional Value-at-Risk (CVaR - mean of bottom 10% worst-case episodes)
        - Stability Score (Sharpe-like ratio: mean / (std + 1e-5))
        """
        # Simulate realistic RL reward distribution with occasional tail variations
        rewards = [round(random.uniform(150, 260) + random.gauss(0, 8), 2) for _ in range(episodes)]
        latencies = [round(random.uniform(10, 40) + random.gauss(0, 2), 2) for _ in range(episodes)]

        df = pd.DataFrame({"reward": rewards, "latency_ms": latencies})

        # Core statistics
        mean_reward = round(float(df["reward"].mean()), 2)
        std_reward = round(float(df["reward"].std()), 2)
        median_reward = round(float(df["reward"].median()), 2)
        min_reward = round(float(df["reward"].min()), 2)
        max_reward = round(float(df["reward"].max()), 2)
        avg_latency = round(float(df["latency_ms"].mean()), 2)

        # Advanced RL benchmark metrics
        # 1. Interquartile Mean (IQM)
        q25 = df["reward"].quantile(0.25)
        q75 = df["reward"].quantile(0.75)
        iqm_subset = df["reward"][(df["reward"] >= q25) & (df["reward"] <= q75)]
        iqm_reward = round(float(iqm_subset.mean()), 2) if not iqm_subset.empty else mean_reward

        # 2. Success rate (episodes >= 195 reward)
        threshold = 195.0
        success_rate = round(float((df["reward"] >= threshold).mean() * 100.0), 2)

        # 3. CVaR (Conditional Value-at-Risk - worst 10% episodes)
        tail_k = max(1, int(episodes * 0.10))
        cvar_reward = round(float(df["reward"].nsmallest(tail_k).mean()), 2)

        # 4. Stability score (signal-to-noise ratio)
        stability_score = round(float(mean_reward / (std_reward + 1e-5)), 2)

        now_str = datetime.utcnow().isoformat()
        result = {
            "model_id": model_id,
            "env_name": env_name,
            "mean_reward": mean_reward,
            "std_reward": std_reward,
            "median_reward": median_reward,
            "min_reward": min_reward,
            "max_reward": max_reward,
            "iqm_reward": iqm_reward,
            "success_rate": success_rate,
            "cvar_reward": cvar_reward,
            "stability_score": stability_score,
            "latency_ms": avg_latency,
            "total_episodes": episodes,
            "status": "completed",
            "evaluated_at": now_str,
        }

        # 1. Persist to Database (PostgreSQL / SQLite)
        try:
            db = SessionLocal()
            record = BenchmarkRecord(
                model_id=model_id,
                env_name=env_name,
                total_episodes=episodes,
                mean_reward=mean_reward,
                std_reward=std_reward,
                median_reward=median_reward,
                min_reward=min_reward,
                max_reward=max_reward,
                iqm_reward=iqm_reward,
                success_rate=success_rate,
                cvar_reward=cvar_reward,
                stability_score=stability_score,
                latency_ms=avg_latency,
                status="completed",
                evaluated_at=datetime.utcnow()
            )
            db.add(record)
            db.commit()
            db.close()
            log.info(f"Persisted BenchmarkRecord to database: model={model_id}, env={env_name}")
        except Exception as e:
            log.warning(f"Could not persist BenchmarkRecord to DB: {e}")

        # 2. Store in Redis for high-speed cache
        if USE_REDIS:
            try:
                redis_client.hset(f"benchmark:result:{model_id}:{env_name}", mapping={
                    k: str(v) for k, v in result.items()
                })
                redis_client.lpush("benchmark:recent_results", json.dumps(result))
            except Exception as e:
                log.warning(f"Failed to cache benchmark in Redis: {e}")
        else:
            # Fallback to file
            out = UPLOAD_DIR / f"{model_id}_{env_name}_result.json"
            out.write_text(json.dumps(result))

        log.info(
            f"Benchmark completed for model={model_id} env={env_name}: "
            f"mean={mean_reward}, iqm={iqm_reward}, cvar={cvar_reward}, stability={stability_score}"
        )
        return result

    @staticmethod
    def list_recent_results(limit: int = 10) -> List[Dict[str, Any]]:
        """
        Return recent benchmark results from DB, with Redis/file fallback.
        """
        # Try reading from database first
        try:
            db = SessionLocal()
            records = (
                db.query(BenchmarkRecord)
                .order_by(BenchmarkRecord.evaluated_at.desc())
                .limit(limit)
                .all()
            )
            db.close()
            if records:
                return [
                    {
                        "model_id": r.model_id,
                        "env_name": r.env_name,
                        "mean_reward": r.mean_reward,
                        "std_reward": r.std_reward,
                        "median_reward": r.median_reward,
                        "min_reward": r.min_reward,
                        "max_reward": r.max_reward,
                        "iqm_reward": r.iqm_reward,
                        "success_rate": r.success_rate,
                        "cvar_reward": r.cvar_reward,
                        "stability_score": r.stability_score,
                        "latency_ms": r.latency_ms,
                        "total_episodes": r.total_episodes,
                        "status": r.status,
                        "evaluated_at": r.evaluated_at.isoformat() if r.evaluated_at else None,
                    }
                    for r in records
                ]
        except Exception as e:
            log.warning(f"Database query failed, falling back to cache: {e}")

        # Redis fallback
        if USE_REDIS:
            try:
                items = redis_client.lrange("benchmark:recent_results", 0, limit - 1)
                return [json.loads(i) for i in items]
            except Exception:
                pass

        # File fallback
        results = []
        for p in sorted(UPLOAD_DIR.glob("*_result.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
            try:
                results.append(json.loads(p.read_text()))
            except Exception:
                continue
        return results

    @staticmethod
    def list_history(
        limit: int = 50,
        offset: int = 0,
        env_name: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Paginated historical benchmark queries filtered by env_name or model_id.
        """
        try:
            db = SessionLocal()
            query = db.query(BenchmarkRecord)
            if env_name:
                query = query.filter(BenchmarkRecord.env_name == env_name)
            if model_id:
                query = query.filter(BenchmarkRecord.model_id == model_id)

            total = query.count()
            rows = query.order_by(BenchmarkRecord.evaluated_at.desc()).offset(offset).limit(limit).all()
            db.close()

            results = [
                {
                    "model_id": r.model_id,
                    "env_name": r.env_name,
                    "mean_reward": r.mean_reward,
                    "std_reward": r.std_reward,
                    "median_reward": r.median_reward,
                    "min_reward": r.min_reward,
                    "max_reward": r.max_reward,
                    "iqm_reward": r.iqm_reward,
                    "success_rate": r.success_rate,
                    "cvar_reward": r.cvar_reward,
                    "stability_score": r.stability_score,
                    "latency_ms": r.latency_ms,
                    "total_episodes": r.total_episodes,
                    "status": r.status,
                    "evaluated_at": r.evaluated_at.isoformat() if r.evaluated_at else None,
                }
                for r in rows
            ]
            return {"total": total, "results": results}
        except Exception as exc:
            log.warning(f"History query DB fallback error: {exc}")
            recent = BenchmarkService.list_recent_results(limit=limit)
            return {"total": len(recent), "results": recent}

    @staticmethod
    def get_model_details(model_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve comprehensive metadata and performance overview for a model.
        """
        try:
            db = SessionLocal()
            meta = db.query(ModelMetadata).filter(ModelMetadata.model_id == model_id).first()
            benchmarks = (
                db.query(BenchmarkRecord)
                .filter(BenchmarkRecord.model_id == model_id)
                .order_by(BenchmarkRecord.mean_reward.desc())
                .all()
            )
            db.close()

            if meta:
                best_score = benchmarks[0].mean_reward if benchmarks else None
                return {
                    "model_id": meta.model_id,
                    "filename": meta.filename,
                    "file_path": meta.file_path,
                    "file_size_bytes": meta.file_size_bytes,
                    "uploaded_at": meta.uploaded_at.isoformat() if meta.uploaded_at else None,
                    "benchmarks_count": len(benchmarks),
                    "best_mean_reward": best_score,
                }
        except Exception as exc:
            log.warning(f"Error querying model details from DB: {exc}")

        # Fallback to file metadata
        meta_file = UPLOAD_DIR / f"{model_id}.meta.json"
        if meta_file.exists():
            try:
                data = json.loads(meta_file.read_text())
                return {
                    "model_id": data.get("model_id"),
                    "filename": data.get("filename", "unknown"),
                    "file_path": data.get("path", ""),
                    "file_size_bytes": data.get("file_size"),
                    "uploaded_at": data.get("uploaded_at"),
                    "benchmarks_count": 0,
                    "best_mean_reward": None,
                }
            except Exception:
                pass

        return None

    @staticmethod
    def compare_models(model_ids: list, env_name: str = None) -> Dict[str, Any]:
        """
        Compare a list of model_ids by mean_reward. If env_name provided, compare results for that env.
        """
        def _safe_float(value):
            if isinstance(value, (float, int)):
                return float(value)
            if isinstance(value, str):
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

        # Try database first
        try:
            db = SessionLocal()
            query = db.query(BenchmarkRecord).filter(BenchmarkRecord.model_id.in_(model_ids))
            if env_name:
                query = query.filter(BenchmarkRecord.env_name == env_name)
            db_records = query.all()
            db.close()

            for r in db_records:
                records.append({
                    "model_id": r.model_id,
                    "env_name": r.env_name,
                    "mean_reward": r.mean_reward,
                    "std_reward": r.std_reward,
                    "median_reward": r.median_reward,
                    "min_reward": r.min_reward,
                    "max_reward": r.max_reward,
                    "iqm_reward": r.iqm_reward,
                    "success_rate": r.success_rate,
                    "stability_score": r.stability_score,
                    "latency_ms": r.latency_ms,
                    "total_episodes": r.total_episodes,
                    "status": r.status,
                    "evaluated_at": r.evaluated_at.isoformat() if r.evaluated_at else None,
                })
        except Exception as e:
            log.warning(f"DB compare failed, falling back to cache: {e}")

        # Redis fallback if no records found
        if not records and USE_REDIS:
            for mid in model_ids:
                if env_name:
                    key = f"benchmark:result:{mid}:{env_name}"
                    row = redis_client.hgetall(key)
                    if row:
                        row["mean_reward"] = _safe_float(row.get("mean_reward", 0))
                        row["std_reward"] = _safe_float(row.get("std_reward", 0))
                        row["median_reward"] = _safe_float(row.get("median_reward", 0))
                        row["latency_ms"] = _safe_float(row.get("latency_ms", 0))
                        records.append(row)
                else:
                    pattern = f"benchmark:result:{mid}:*"
                    for k in redis_client.keys(pattern):
                        row = redis_client.hgetall(k)
                        if row:
                            row["mean_reward"] = _safe_float(row.get("mean_reward", 0))
                            row["std_reward"] = _safe_float(row.get("std_reward", 0))
                            row["median_reward"] = _safe_float(row.get("median_reward", 0))
                            row["latency_ms"] = _safe_float(row.get("latency_ms", 0))
                            records.append(row)

        # File fallback
        if not records:
            for mid in model_ids:
                for p in UPLOAD_DIR.glob(f"{mid}_*_result.json"):
                    try:
                        r = json.loads(p.read_text())
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

        df = pd.DataFrame(records)
        df_sorted = df.sort_values(by="mean_reward", ascending=False)

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
