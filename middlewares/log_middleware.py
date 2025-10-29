# middlewares/log_middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from shared.utils.logger import get_logger
import time

log = get_logger("Middleware")

class LogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = round((time.time() - start_time) * 1000, 2)
        
        log.info(
            f"{request.method} {request.url.path} "
            f"→ {response.status_code} ({process_time}ms)"
        )
        return response
