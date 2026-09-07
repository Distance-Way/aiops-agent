import secrets
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from app.config import settings


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class SlidingWindowRateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            events = self._events[key]
            while events and events[0] <= now - self.window_seconds:
                events.popleft()
            if len(events) >= self.limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="请求过于频繁，请稍后再试",
                )
            events.append(now)


rate_limiter = SlidingWindowRateLimiter(
    settings.rate_limit, settings.rate_window_seconds
)


async def require_api_key(
    request: Request,
    api_key: str | None = Security(api_key_header),
) -> None:
    if not api_key or not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或缺失 API Key",
        )
    client = request.client.host if request.client else "unknown"
    rate_limiter.check(f"{client}:{api_key}")
