"""Runs only when a real Redis is available (CI provides one as a service container).

    REDIS_TEST_URL=redis://localhost:6379/15 pytest tests/test_gateway_redis_integration.py

Proves the rate limiter's counters actually live in Redis, not in process memory.
"""
import os
import sys
import uuid

import pytest

REDIS_URL = os.environ.get("REDIS_TEST_URL")
pytestmark = pytest.mark.skipif(not REDIS_URL, reason="REDIS_TEST_URL not set (no Redis available)")

sys.path.insert(0, os.path.abspath("api-gateway"))


def test_limiter_uses_redis_storage_and_writes_counters_to_redis():
    import redis
    from app.main import build_limiter, check_redis

    assert check_redis(REDIS_URL) == "healthy"

    limiter = build_limiter(REDIS_URL)
    assert type(limiter._storage).__name__ == "RedisStorage"

    from limits import parse
    item = parse("3/minute")
    key = f"itest-{uuid.uuid4()}"
    assert [limiter.limiter.hit(item, key) for _ in range(4)] == [True, True, True, False]

    # The counter is visible to an independent Redis client, i.e. it is not process-local.
    client = redis.Redis.from_url(REDIS_URL)
    assert any(key.encode() in k for k in client.scan_iter("*"))
