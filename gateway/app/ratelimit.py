import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int


class SlidingWindowRateLimiter:
    def __init__(self, limit_per_minute: int) -> None:
        self.limit_per_minute = max(limit_per_minute, 1)
        self.window_seconds = 60.0
        self._entries: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check(self, key: str) -> RateLimitResult:
        now = time.time()
        async with self._lock:
            q = self._entries[key]
            cutoff = now - self.window_seconds
            while q and q[0] < cutoff:
                q.popleft()
            if len(q) >= self.limit_per_minute:
                return RateLimitResult(allowed=False, remaining=0)
            q.append(now)
            return RateLimitResult(allowed=True, remaining=self.limit_per_minute - len(q))
