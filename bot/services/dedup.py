"""TTL-based in-memory deduplication cache."""

from time import monotonic


class TTLCache:
    """Thread-safe TTL cache for message deduplication."""

    def __init__(self, ttl_seconds: float = 10.0):
        """
        Initialize TTL cache.

        Args:
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self._ttl = ttl_seconds
        self._cache: dict[str, float] = {}

    def add_if_new(self, key: str) -> bool:
        """
        Add key to cache if not already present (within TTL).

        Args:
            key: Unique key to check/add

        Returns:
            True if key was new (not seen within TTL), False if duplicate
        """
        now = monotonic()
        self._cleanup(now)

        if key in self._cache:
            return False

        self._cache[key] = now
        return True

    def _cleanup(self, now: float) -> None:
        """Remove expired entries from cache."""
        expired = [k for k, ts in self._cache.items() if now - ts > self._ttl]
        for k in expired:
            del self._cache[k]

    def clear(self) -> None:
        """Clear all entries from cache."""
        self._cache.clear()

    def __len__(self) -> int:
        """Return number of entries in cache."""
        return len(self._cache)
