from src.utils.cache import TTLCache


def test_ttl_cache_expires_entries():
    now = [100.0]
    cache = TTLCache[str, dict](ttl_seconds=10, max_entries=2, clock=lambda: now[0])
    cache.set("AAPL", {"value": 1})

    assert cache.get("AAPL") == {"value": 1}
    now[0] = 111.0
    assert cache.get("AAPL") is None


def test_ttl_cache_evicts_least_recently_used_entry():
    cache = TTLCache[str, int](ttl_seconds=10, max_entries=2)
    cache.set("AAPL", 1)
    cache.set("MSFT", 2)
    assert cache.get("AAPL") == 1
    cache.set("NVDA", 3)

    assert cache.get("MSFT") is None
    assert cache.get("AAPL") == 1
    assert cache.get("NVDA") == 3
