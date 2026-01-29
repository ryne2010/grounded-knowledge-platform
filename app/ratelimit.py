from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass
class SlidingWindowRateLimiter:
    """Small in-process rate limiter.

    Note: this is per-instance. In Cloud Run (or any scaled deployment), each
    instance enforces its own window.
    """

    window_s: int = 60
    max_requests: int = 30

    def __post_init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.time()
        q = self._hits[key]
        while q and now - q[0] > self.window_s:
            q.popleft()
        if len(q) >= self.max_requests:
            return False
        q.append(now)
        return True
