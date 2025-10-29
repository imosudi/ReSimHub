from fastapi import FastAPI
from backend.fastapi_app.routers import experiments, environments

app = FastAPI(title="ReSimHub FastAPI Service")

app.include_router(experiments.router)
app.include_router(environments.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "fastapi"}
