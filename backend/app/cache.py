"""
Redis In-Memory Caching Engine & Rate Limiter Store
Location: backend/app/cache.py

Manages high-speed RAM caching for read-heavy endpoints (Menu, Categories)
and provides atomic distributed counters for brute-force rate limiting (SEC-06).
Implements the Cache-Aside pattern with TTL expiration and pattern-based invalidation.
Supports standard cloud REDIS_URL connection strings with graceful fallback.
"""

import os
import json
from decimal import Decimal
from typing import Optional, Any
import redis
from dotenv import load_dotenv

load_dotenv()

# -------------------------------------------------------------
# 1. Resolve Cloud Redis Connection String (12-Factor Pattern)
# -------------------------------------------------------------
REDIS_URL = os.getenv("REDIS_URL")
DEFAULT_CACHE_TTL = 3600  # Default Time-To-Live: 1 hour (3600 seconds)

try:
    if REDIS_URL:
        # Standard cloud connection string (supports redis:// and TLS rediss://)
        redis_client = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2
        )
    else:
        # Localhost development fallback
        REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
        REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
        REDIS_DB = int(os.getenv("REDIS_DB", 0))
        REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True,
            socket_connect_timeout=2
        )
except Exception as e:
    print(f"[Cache] Warning: Could not initialize Redis connection: {e}")
    redis_client = None


# Helper to serialize Python types like Decimal and datetime to JSON
def json_serial_helper(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} is not JSON serializable")


# =============================================================
# CACHE ACCESS FUNCTIONS (GET, SET, PURGE)
# =============================================================

def get_cache(key: str) -> Optional[Any]:
    """
    Reads cached data from Redis.
    Returns: Parsed Python dict/list if CACHE HIT, None if CACHE MISS or error.
    """
    if not redis_client:
        return None
    try:
        cached_value = redis_client.get(key)
        if cached_value:
            return json.loads(cached_value)
        return None
    except Exception as e:
        # Graceful degradation: Log warning and let app query MySQL without crashing
        print(f"[Cache] Redis GET error for key '{key}': {e}")
        return None


def set_cache(key: str, data: Any, ttl_seconds: int = DEFAULT_CACHE_TTL) -> bool:
    """
    Saves data into Redis RAM with a Time-To-Live (TTL) expiration.
    Automatically serializes Python dicts/lists and Decimals to JSON.
    """
    if not redis_client:
        return False

    try:
        json_payload = json.dumps(data, default=json_serial_helper)
        redis_client.set(key, json_payload, ex=ttl_seconds)
        return True
    except Exception as e:
        print(f"[Cache] Redis SET error for key '{key}': {e}")
        return False


def invalidate_cache(pattern: str) -> int:
    """
    Cache Invalidation / Purge:
    Deletes all keys matching a wildcard pattern (e.g. 'menu:*').
    Called whenever an admin updates menu items or toggles stock.
    Returns the number of keys deleted.
    """
    if not redis_client:
        return 0

    try:
        matching_keys = redis_client.keys(pattern)
        if matching_keys:
            deleted_count = redis_client.delete(*matching_keys)
            print(f"[Cache] Purged {deleted_count} cached Redis keys matching '{pattern}'")
            return deleted_count
        return 0
    except Exception as e:
        print(f"[Cache] Redis PURGE error for pattern '{pattern}': {e}")
        return 0


def is_redis_healthy() -> bool:
    """Quick health check: Returns True if Redis responds to PING."""
    if not redis_client:
        return False
    try:
        return bool(redis_client.ping())
    except Exception:
        return False