from typing import Any, Optional
from datetime import datetime, timedelta
import threading

class TTLCache:
    """Thread-safe cache with TTL"""
    def __init__(self, ttl_seconds: int = 3600):
        self._cache = {}
        self._ttl = ttl_seconds
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Get value if exists and not expired"""
        with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if datetime.now() < expiry:
                    return value
                del self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Set value with expiration"""
        with self._lock:
            expiry = datetime.now() + timedelta(seconds=self._ttl)
            self._cache[key] = (value, expiry)

    def clear(self) -> None:
        """Clear expired entries"""
        with self._lock:
            now = datetime.now()
            self._cache = {
                k: (v, e) for k, (v, e) in self._cache.items()
                if e > now
            }
