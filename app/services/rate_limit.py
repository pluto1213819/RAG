import time
import redis
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.db import REDIS_URL


class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window_seconds
        try:
            self.r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
            self.r.ping()
            self.enabled = True
        except Exception:
            self.enabled = False

    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)
        key = f"rl:{request.client.host}:{int(time.time() // self.window)}"
        count = self.r.incr(key)
        if count == 1:
            self.r.expire(key, self.window)
        if count > self.max_requests:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        return await call_next(request)
