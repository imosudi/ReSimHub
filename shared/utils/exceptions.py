# exceptions.py
from fastapi import Request
from fastapi.responses import JSONResponse
from shared.utils.logger import get_logger
import uuid

error_id = str(uuid.uuid4())

log = get_logger("ExceptionHandler")

async def http_exception_handler(request: Request, exc):
    #log.warning(f"HTTP Exception: {exc.detail}")
    log.warning(f"HTTP Exception on {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

async def unhandled_exception_handler(request: Request, exc):
    #log.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
    error_id = str(uuid.uuid4())
    log.error(f"[{error_id}] Unhandled Exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        #content={"error": "Internal Server Error"},
        content={"error": "Internal Server Error", "error_id": error_id},
    )


