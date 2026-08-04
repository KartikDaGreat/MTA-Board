import time


class TTLCache:
    """Caches the result of fetch_fn() for ttl_seconds, so callers polling
    frequently for page cycling don't each trigger a new network fetch."""

    def __init__(self, fetch_fn, ttl_seconds):
        self.fetch_fn = fetch_fn
        self.ttl_seconds = ttl_seconds
        self._value = None
        self._fetched_at = 0

    def get(self):
        now = time.monotonic()
        if self._value is None or (now - self._fetched_at) > self.ttl_seconds:
            self._value = self.fetch_fn()
            self._fetched_at = now
        return self._value
