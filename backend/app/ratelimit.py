"""Minimal in-memory sliding-window rate limiter (dev/staging hardening).

Not a distributed limiter; sufficient for Phase 1A single-pod dev/staging to blunt
brute-force and cron-auth abuse. Never records secrets.
"""
import time
import threading


class RateLimiter:
    def __init__(self):
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def add(self, key: str) -> None:
        with self._lock:
            self._hits.setdefault(key, []).append(time.time())

    def exceeded(self, key: str, limit: int, window_s: int) -> bool:
        now = time.time()
        with self._lock:
            arr = [t for t in self._hits.get(key, []) if now - t < window_s]
            self._hits[key] = arr
            return len(arr) >= limit


limiter = RateLimiter()
