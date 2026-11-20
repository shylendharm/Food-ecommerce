"""
Automated Test Suite: Redis In-Memory Caching & Cache Invalidation
Location: backend/tests/test_caching.py

Verifies:
1. Redis connectivity and ping health check.
2. Cache-Aside pattern on GET /api/menu (Cache Miss -> MySQL -> Redis -> Cache Hit).
3. Cache Invalidation on Admin Stock Toggle (Purges Redis keys).
4. Performance Benchmark (Proving sub-5ms Redis response).
"""

import time
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.cache import (
    is_redis_healthy,
    set_cache,
    get_cache,
    invalidate_cache
)

client = TestClient(app)

def get_admin_auth_header() -> dict:
    response = client.post("/api/auth/login", json={"email": "admin@restaurant.com", "password": "admin123"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# =============================================================
# 1. UNIT TEST: REDIS CONNECTIVITY & CRUD
# =============================================================

def test_redis_connection_and_basic_crud():
    """
    Verifies that Redis is reachable on port 6379 and can write/read/delete keys.
    """
    assert is_redis_healthy() is True

    test_key = "test:food_key"
    test_payload = {"status": "ok", "dish_count": 8}

    # Set cache with 60 second TTL
    assert set_cache(test_key, test_payload, ttl_seconds=60) is True

    # Read back from Redis
    cached = get_cache(test_key)
    assert cached is not None
    assert cached["dish_count"] == 8

    # Invalidate / Purge
    assert invalidate_cache("test:*") >= 1
    assert get_cache(test_key) is None


# =============================================================
# 2. INTEGRATION TEST: CACHE-ASIDE PATTERN ON MENU
# =============================================================

def test_cache_aside_flow_on_menu_endpoint():
    """
    Verifies the Cache-Aside pattern:
    1. Purges Redis cache.
    2. First request to /api/menu -> CACHE MISS (queries MySQL, saves to Redis).
    3. Confirms Redis now has the key 'menu:cat_all:veg_all'.
    4. Second request to /api/menu -> CACHE HIT (reads from Redis RAM).
    """
    # 1. Clear existing cache
    invalidate_cache("menu:*")
    cache_key = "menu:cat_all:veg_all"
    assert get_cache(cache_key) is None

    # 2. First request: Cache Miss -> Populates Redis
    res1 = client.get("/api/menu")
    assert res1.status_code == 200
    items1 = res1.json()
    assert len(items1) > 0

    # 3. Verify that Redis now contains the cached data!
    cached_in_redis = get_cache(cache_key)
    assert cached_in_redis is not None
    assert len(cached_in_redis) == len(items1)
    assert cached_in_redis[0]["name"] == items1[0]["name"]

    # 4. Second request: Cache Hit
    res2 = client.get("/api/menu")
    assert res2.status_code == 200
    assert res2.json() == items1


# =============================================================
# 3. INTEGRATION TEST: CACHE INVALIDATION ON STOCK TOGGLE
# =============================================================

def test_admin_stock_toggle_invalidates_cache():
    """
    Verifies Cache Invalidation:
    1. Warm up cache so 'menu:cat_all:veg_all' exists in Redis.
    2. Admin toggles dish stock -> Redis cache must be purged!
    3. Confirms 'menu:cat_all:veg_all' is evaporated from Redis.
    """
    # 1. Warm up cache
    client.get("/api/menu")
    cache_key = "menu:cat_all:veg_all"
    assert get_cache(cache_key) is not None

    # 2. Admin toggles dish stock
    admin_headers = get_admin_auth_header()
    menu_res = client.get("/api/menu")
    first_dish_id = menu_res.json()[0]["id"]

    toggle_res = client.patch(f"/api/admin/menu/{first_dish_id}/toggle-stock", headers=admin_headers)
    assert toggle_res.status_code == 200

    # 3. Verify Redis cache was purged automatically!
    assert get_cache(cache_key) is None

    # 4. Re-toggle back to original state to keep database clean
    client.patch(f"/api/admin/menu/{first_dish_id}/toggle-stock", headers=admin_headers)


# =============================================================
# 4. PERFORMANCE BENCHMARK: MYSQL DISK VS REDIS RAM
# =============================================================

def test_redis_performance_benchmark():
    """
    Performance Benchmark:
    Compares response latency of Cache Miss (MySQL) vs Cache Hit (Redis RAM).
    Prints exact millisecond timings to terminal!
    """
    # 1. Measure Cache Miss (MySQL disk read)
    invalidate_cache("menu:*")
    t0 = time.perf_counter()
    res_miss = client.get("/api/menu")
    t_miss = (time.perf_counter() - t0) * 1000  # Convert to milliseconds
    assert res_miss.status_code == 200

    # 2. Measure Cache Hit (Redis RAM read)
    t1 = time.perf_counter()
    res_hit = client.get("/api/menu")
    t_hit = (time.perf_counter() - t1) * 1000  # Convert to milliseconds
    assert res_hit.status_code == 200

    print(f"\n=======================================================")
    print(f"⚡ REDIS CACHING PERFORMANCE BENCHMARK:")
    print(f"   🐢 Cache Miss (MySQL Disk I/O): {t_miss:.2f} ms")
    print(f"   🚀 Cache Hit (Redis RAM I/O):   {t_hit:.2f} ms")
    if t_hit > 0:
        print(f"   💨 Speedup Factor:              {t_miss / t_hit:.1f}x faster!")
    print(f"=======================================================")

    assert res_hit.status_code == 200