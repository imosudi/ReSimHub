from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="ReSimHub FastAPI Service")

@app.get("/health")
async def health_check():
    return JSONResponse({"status": "ok", "service": "fastapi"})
