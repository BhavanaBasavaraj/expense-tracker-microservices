"""Shared test environment.

These env vars must be set before any service module is imported, because each
service reads its settings once at import time.
"""
import os

# Shared secret the gateway attaches and downstream services require.
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-key")
# slowapi/limits in-process storage so unit tests do not need a Redis server.
# The real-Redis path is covered by tests/test_gateway_redis_integration.py.
os.environ.setdefault("REDIS_URL", "memory://")
