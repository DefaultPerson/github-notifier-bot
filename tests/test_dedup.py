"""Tests for TTL-based deduplication cache."""

import time

from bot.services.dedup import TTLCache


class TestTTLCache:
    """Tests for TTLCache class."""

    def test_add_new_key(self):
        """Test that new key returns True."""
        cache = TTLCache(ttl_seconds=10.0)

        assert cache.add_if_new("key1") is True
        assert len(cache) == 1

    def test_duplicate_key(self):
        """Test that duplicate key returns False."""
        cache = TTLCache(ttl_seconds=10.0)

        assert cache.add_if_new("key1") is True
        assert cache.add_if_new("key1") is False
        assert len(cache) == 1

    def test_different_keys(self):
        """Test that different keys are both accepted."""
        cache = TTLCache(ttl_seconds=10.0)

        assert cache.add_if_new("key1") is True
        assert cache.add_if_new("key2") is True
        assert len(cache) == 2

    def test_expiry(self):
        """Test that expired keys are removed."""
        cache = TTLCache(ttl_seconds=0.1)  # 100ms TTL

        assert cache.add_if_new("key1") is True
        assert cache.add_if_new("key1") is False  # Still fresh

        time.sleep(0.15)  # Wait for expiry

        assert cache.add_if_new("key1") is True  # Should be new again

    def test_clear(self):
        """Test that clear removes all entries."""
        cache = TTLCache(ttl_seconds=10.0)

        cache.add_if_new("key1")
        cache.add_if_new("key2")
        assert len(cache) == 2

        cache.clear()
        assert len(cache) == 0

        # Should be able to add again
        assert cache.add_if_new("key1") is True

    def test_cleanup_on_add(self):
        """Test that expired entries are cleaned up on add."""
        cache = TTLCache(ttl_seconds=0.05)  # 50ms TTL

        cache.add_if_new("key1")
        cache.add_if_new("key2")
        assert len(cache) == 2

        time.sleep(0.1)  # Wait for expiry

        # Adding new key should trigger cleanup
        cache.add_if_new("key3")
        assert len(cache) == 1  # Only key3 remains
