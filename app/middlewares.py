import time

from fastapi.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware


class SimplePrintLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print("Before request")
        response = await call_next(request)
        print("After request")

        return response


class ProcessTimeLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            start_time = time.perf_counter()
            response = await call_next(request)
            duration = time.perf_counter() - start_time
            response.headers["X-Process-Time"] = str(duration)
            return response
        except Exception as e:
            print("Middleware error:", e)
            raise e


# CORS middleware

origins = [
    "http://localhost:3000",
]