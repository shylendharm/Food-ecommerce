"""Redis cache client and rate limiting utilities."""

import os
import json
from decimal import Decimal
from typing import Optional, Any
import redis
from dotenv import load_dotenv

load_dotenv()

# Redis connection
REDIS_URL = os.getenv("REDIS_URL")
DEFAULT_CACHE_TTL = 3600  # Default Time-To-Live: 1 hour (3600 seconds)

try:
    if REDIS_URL:
        redis_client = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2
        )
    else:
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


# JSON serialization helper
def json_serial_helper(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} is not JSON serializable")


# Cache helpers

def get_cache(key: str) -> Optional[Any]:
    """Get cached data from Redis."""
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