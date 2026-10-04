

# backend/fastapi_app/main.py
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, HTTPException
from backend.fastapi_app.core.config import AppConfig
from backend.fastapi_app.core.db import init_db

from middlewares.log_middleware import LogMiddleware
from shared.utils.exceptions import http_exception_handler, unhandled_exception_handler
from shared.utils.logger import get_logger
from backend.fastapi_app.routers import (
    experiments,
    environments,
    status,
    train,
    orchestrator,
    analytics,
    benchmark,
    metrics,
    dashboard,
    checkpoints,
)
from backend.fastapi_app.services.progress_broadcast import get_broadcast_service
from backend.fastapi_app.core.logging_config import logger  # structured logger



log = get_logger("Main")
app_config = AppConfig()

app = FastAPI(title="ReSimHub  Backend Service", version=app_config.version)

# Include routers
app.include_router(experiments.router)
app.include_router(environments.router)
app.include_router(orchestrator.router)
app.include_router(train.router)
app.include_router(status.router)
app.include_router(analytics.router)
app.include_router(benchmark.router)
app.include_router(metrics.router)
app.include_router(dashboard.router)
app.include_router(checkpoints.router)

app.add_middleware(LogMiddleware)

# Exception Handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


# -------------------------------------------------------
# 🧩 Lifecycle Events
# -------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    """Initialise database, progress broadcaster, and log startup state."""
    try:
        init_db()
        logger.info("Database initialised successfully.")
    except Exception as e:
        logger.error("Database initialisation failed", error=str(e))

    try:
        broadcaster = get_broadcast_service()
        await broadcaster.connect()
        logger.info("Progress broadcaster initialised.")
    except Exception as e:
        logger.warning("Progress broadcaster init warning", error=str(e))

    logger.info("ReSimHub Application startup complete.")


@app.on_event("shutdown")
async def on_shutdown():
    """Graceful shutdown with structured log."""
    try:
        broadcaster = get_broadcast_service()
        await broadcaster.disconnect()
    except Exception:
        pass
    logger.info("ReSimHub Application shutting down.")

# -------------------------------------------------------
# 🩺 Health Check Endpoint
# -------------------------------------------------------
@app.get("/health", tags=["System"])
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "backend fastapi service", "version": app.version}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.fastapi_app.main:app", host="0.0.0.0", port=8000, reload=True)


