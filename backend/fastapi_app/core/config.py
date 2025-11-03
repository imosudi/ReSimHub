"""
ReSimHub Unified Configuration Loader (Pydantic v2+)
# backend/fastapi_app/core/config.py
----------------------------------------------------
Supports:
  - Hierarchical YAML (envs/.config.yaml)
  - .env environment overrides
  - Automatic type validation
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, Field
from pathlib import Path
import yaml


# ==========================================================
# Submodels for each configuration section
# ==========================================================

class AppConfig(BaseModel):
    name: str = "ReSimHub"
    version: str = "0.7.0"
    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000


class DatabaseConfig(BaseModel):
    driver: str = "sqlite"
    url: str = "sqlite:///./resimhub.db"
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False


class LoggingConfig(BaseModel):
    level: str = "INFO"
    structured: bool = True
    json_format: bool = True
    log_file: str = "logs/resimhub.log"
    rotation: str = "daily"
    retention: str = "7d"
    stdout: bool = True
    processors: list[str] = [
        "add_log_level",
        "add_timestamp",
        "format_exc_info",
        "json_renderer",
    ]


class PrometheusConfig(BaseModel):
    port: int = 8000
    endpoint: str = "/metrics"


class ObservabilityConfig(BaseModel):
    enable_prometheus: bool = True
    prometheus: PrometheusConfig = PrometheusConfig()
    enable_structlog: bool = True
    enable_tracing: bool = False


class MonitoringConfig(BaseModel):
    metrics_labels: list[str] = []
    alert_thresholds: dict[str, int | float] = {}


class CacheConfig(BaseModel):
    backend: str = "redis"
    #url: str = "redis://localhost:6379/0"
    url: str = "redis://localhost:6379/"
    timeout_seconds: int = 2


class SecurityConfig(BaseModel):
    secret_key: str = "change_me_in_production"
    access_token_expire_minutes: int = 60


class SystemConfig(BaseModel):
    max_workers: int = 4
    enable_experiment_tracking: bool = True


# ==========================================================
# Main Settings (merges all submodels)
# ==========================================================

class Settings(BaseSettings):
    app: AppConfig = AppConfig()
    database: DatabaseConfig = DatabaseConfig()
    logging: LoggingConfig = LoggingConfig()
    observability: ObservabilityConfig = ObservabilityConfig()
    monitoring: MonitoringConfig = MonitoringConfig()
    cache: CacheConfig = CacheConfig()
    security: SecurityConfig = SecurityConfig()
    system: SystemConfig = SystemConfig()

    model_config = SettingsConfigDict(
        env_file="envs/.env",
        extra="ignore",
    )


# ==========================================================
# Load YAML & merge environment overrides
# ==========================================================

def load_settings() -> Settings:
    config_path = Path("envs/.config.yaml")
    settings = Settings()

    if config_path.exists():
        with open(config_path, "r") as f:
            yaml_data = yaml.safe_load(f) or {}

        # Merge YAML into Pydantic models
        for section, data in yaml_data.items():
            if hasattr(settings, section) and isinstance(data, dict):
                submodel = getattr(settings, section)
                for key, value in data.items():
                    if hasattr(submodel, key):
                        setattr(submodel, key, value)

    return settings


settings = load_settings()


if __name__ == "__main__":
    print("✅ Configuration loaded successfully:")
    print(f"App: {settings.app.name} ({settings.app.environment})")
    print(f"Database: {settings.database.url}")
    print(f"Cache: {settings.cache.url}")
