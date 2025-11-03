# backend/fastapi_app/main.py
from fastapi import FastAPI
from middlewares.log_middleware import LogMiddleware
from fastapi.exceptions import RequestValidationError, HTTPException
from shared.utils.exceptions import http_exception_handler, unhandled_exception_handler
from shared.utils.logger import get_logger
from backend.fastapi_app.routers import experiments, environments, status,  train , orchestrator, analytics, benchmark, metrics
from backend.fastapi_app.core.logging_config import logger



log = get_logger("Main")


app = FastAPI(title="ReSimHub  Backend Service", version="0.7.0")

# Include routers
app.include_router(experiments.router)
app.include_router(environments.router)
app.include_router(orchestrator.router)
app.include_router(train.router)
app.include_router(status.router)
app.include_router(analytics.router)
app.include_router(benchmark.router)
app.include_router(metrics.router)

app.add_middleware(LogMiddleware)

# Exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)



@app.on_event("startup")
async def startup_event():
    log.info("ReSimHub Application startup complete.")

@app.on_event("shutdown")
async def shutdown_event():
    log.info("ReSimHub Application shutting down.")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "fastapi"}
