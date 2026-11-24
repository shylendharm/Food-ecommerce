"""
Automated Test Suite: Real-Time Logistics & WebSocket Event Streaming (Security Hardened)
Location: backend/tests/test_logistics.py

Verifies:
1. Haversine distance formula accuracy and spherical symmetry.
2. Address coordinate geocoding determinism and bounds.
3. Status-based dynamic ETA calculations across all lifecycle stages.
4. REST logistics endpoint (/api/orders/{id}/logistics) auth guard (SEC-07: 401 unauthenticated, 200 authenticated).
5. Bidirectional WebSocket handshake with ?token= validation (SEC-07: 1008 rejection without token).
6. Real-time broadcast delivery to connected authenticated WebSocket clients.
7. Rejection of WebSocket connections for non-existent orders.
8. Connection pool lifecycle and memory leak prevention (room cleanup).
"""

import asyncio
import uuid
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app
from app.logistics import (
    calculate_haversine_distance,
    get_coordinates_for_address,
    compute_order_logistics
)
from app.websocket_manager import ws_manager

client = TestClient(app)


# =============================================================
# HELPER FIXTURES: AUTHENTICATED TEST CUSTOMER & ORDERS
# =============================================================

def create_test_customer_auth() -> tuple[dict, str, dict]:
    """
    Creates an isolated test customer in MySQL.
    Returns: (user_data, raw_jwt_token, auth_headers_dict)
    """
    unique_suffix = uuid.uuid4().hex[:8]
    email = f"logistics_test_{unique_suffix}@example.com"
    password = "StrongPassword123!"

    register_payload = {
        "name": f"Courier Tester {unique_suffix}",
        "email": email,
        "password": password,
        "phone": "9876543210",
        "default_address": "Indiranagar 100 Feet Road, Bengaluru"
    }

    reg_res = client.post("/api/auth/register", json=register_payload)
    assert reg_res.status_code == 201, f"Failed to register test user: {reg_res.text}"
    user_data = reg_res.json()

    login_res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login_res.status_code == 200, f"Failed to authenticate test user: {login_res.text}"
    token = login_res.json()["access_token"]

    return user_data, token, {"Authorization": f"Bearer {token}"}


def create_test_order() -> tuple[dict, str, dict]:
    """
    Creates an authenticated order in MySQL.
    Returns: (created_order_dict, raw_jwt_token, auth_headers)
    """
    user_data, token, headers = create_test_customer_auth()

    menu_res = client.get("/api/menu")
    assert menu_res.status_code == 200 and len(menu_res.json()) > 0
    dish_id = menu_res.json()[0]["id"]

    order_payload = {
        "customer_name": user_data["name"],
        "customer_email": user_data["email"],
        "customer_phone": user_data["phone"],
        "delivery_address": user_data["default_address"],
        "payment_method": "COD",
        "items": [{"menu_item_id": dish_id, "quantity": 1}]
    }
    res = client.post("/api/orders", json=order_payload, headers=headers)
    assert res.status_code == 201
    return res.json(), token, headers


# =============================================================
# 1. HAVERSINE MATHEMATICAL ACCURACY TESTS
# =============================================================

def test_haversine_formula_math():
    """
    Verifies that the Haversine trigonometric formula:
    - Calculates 0 km for identical coordinates.
    - Accurately calculates great-circle distance between two known geographic points.
    - Exhibits mathematical symmetry: dist(A, B) == dist(B, A).
    """
    restaurant_lat, restaurant_lon = 12.9716, 77.5946

    # 1. Distance from a point to itself must be exactly 0
    assert calculate_haversine_distance(restaurant_lat, restaurant_lon, restaurant_lat, restaurant_lon) == 0.0

    # 2. Known distance: Bangalore Center to Whitefield (~16.8 km)
    whitefield_lat, whitefield_lon = 12.9698, 77.7499
    dist = calculate_haversine_distance(restaurant_lat, restaurant_lon, whitefield_lat, whitefield_lon)
    assert 15.0 < dist < 19.0

    # 3. Symmetry check: Distance A -> B must equal Distance B -> A
    dist_reverse = calculate_haversine_distance(whitefield_lat, whitefield_lon, restaurant_lat, restaurant_lon)
    assert dist == dist_reverse


def test_address_geocoding_determinism_and_bounds():
    """
    Verifies that get_coordinates_for_address:
    - Produces deterministic (repeatable) coordinates for identical addresses.
    - Produces distinct coordinates for different addresses.
    - Yields realistic coordinates within valid latitude (-90 to 90) and longitude (-180 to 180) bounds.
    """
    addr_1 = "100 MG Road, Bangalore"
    addr_2 = "404 Indiranagar 100ft Road, Bangalore"

    lat1, lon1 = get_coordinates_for_address(addr_1)
    lat1_repeat, lon1_repeat = get_coordinates_for_address(addr_1)

    # Determinism: Hashes must match 100% of the time
    assert lat1 == lat1_repeat
    assert lon1 == lon1_repeat

    # Distinctness: Different addresses must produce different locations
    lat2, lon2 = get_coordinates_for_address(addr_2)
    assert (lat1, lon1) != (lat2, lon2)

    # Valid world coordinates
    assert -90.0 <= lat1 <= 90.0
    assert -180.0 <= lon1 <= 180.0


# =============================================================
# 2. DYNAMIC ETA LIFECYCLE TESTS
# =============================================================

def test_eta_calculation_across_lifecycle_stages():
    """
    Verifies status-based dynamic ETA calculation:
    - PENDING includes cooking + transit + buffer.
    - PREPARING has less cooking time remaining.
    - OUT_FOR_DELIVERY includes ONLY transit time (cooking finished!).
    - DELIVERED returns 0 minutes remaining.
    - ETA strictly decreases monotonically as the order advances.
    """
    addr = "25 Koramangala 4th Block"

    pending_logistics = compute_order_logistics("PENDING", addr)
    preparing_logistics = compute_order_logistics("PREPARING", addr)
    transit_logistics = compute_order_logistics("OUT_FOR_DELIVERY", addr)
    delivered_logistics = compute_order_logistics("DELIVERED", addr)

    # Monotonic decrease: As delivery progresses, ETA drops
    assert pending_logistics["estimated_minutes"] > preparing_logistics["estimated_minutes"]
    assert preparing_logistics["estimated_minutes"] > transit_logistics["estimated_minutes"]
    assert transit_logistics["estimated_minutes"] > delivered_logistics["estimated_minutes"]

    # Terminal state: Completed delivery has 0 minutes remaining
    assert delivered_logistics["estimated_minutes"] == 0


# =============================================================
# 3. REST LOGISTICS ENDPOINT TESTS (SEC-07 DEFENSE)
# =============================================================

def test_rest_logistics_endpoint_unauthenticated_fails_401():
    """
    Security Penetration Test (SEC-07): Querying logistics without a Bearer token.
    Must be rejected with HTTP 401 Unauthorized.
    """
    order, token, headers = create_test_order()

    res = client.get(f"/api/orders/{order['id']}/logistics")
    assert res.status_code == 401


def test_rest_logistics_endpoint_authenticated_success():
    """
    Happy Path: Authenticated customer retrieves real-time logistics.
    Expects: HTTP 200 OK with coordinates, distance, and ETA.
    """
    order, token, headers = create_test_order()

    res = client.get(f"/api/orders/{order['id']}/logistics", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["order_id"] == order["id"]
    assert "logistics" in data

    logistics = data["logistics"]
    assert "distance_km" in logistics
    assert "estimated_minutes" in logistics
    assert "restaurant_coordinates" in logistics
    assert "customer_coordinates" in logistics

    # 404 check for invalid order ID
    res_404 = client.get("/api/orders/999999/logistics", headers=headers)
    assert res_404.status_code == 404


# =============================================================
# 4. WEBSOCKET REAL-TIME STREAMING & AUTH TESTS (SEC-07)
# =============================================================

def test_websocket_unauthenticated_connection_rejected_1008():
    """
    Security Penetration Test (SEC-07): Connecting to WebSocket with NO token.
    Must be rejected immediately with WebSocket code 1008 (Policy Violation).
    """
    order, token, headers = create_test_order()

    try:
        with client.websocket_connect(f"/ws/orders/{order['id']}") as ws:
            pytest.fail("Unauthenticated WebSocket connection should have been rejected with code 1008.")
    except WebSocketDisconnect as exc:
        assert exc.code == 1008


def test_websocket_handshake_and_initial_state():
    """
    Happy Path (SEC-07): Authenticated WebSocket connection with ?token={token}.
    - Connects successfully via full-duplex TCP.
    - Pushes INITIAL_STATE greeting payload with coordinates and ETA upon handshake.
    - Responds to 'ping' with 'PONG'.
    """
    order, token, headers = create_test_order()

    with client.websocket_connect(f"/ws/orders/{order['id']}?token={token}") as ws:
        # 1. First frame sent by server must be the initial greeting state
        greeting = ws.receive_json()
        assert greeting["event"] == "INITIAL_STATE"
        assert greeting["order_id"] == order["id"]
        assert greeting["status"] == "PENDING"
        assert "logistics" in greeting

        # 2. Test bi-directional ping-pong
        ws.send_text("ping")
        pong_res = ws.receive_json()
        assert pong_res["event"] == "PONG"


def test_websocket_live_broadcast():
    """
    Verifies that calling ws_manager.broadcast_order_update delivers
    the live payload to the connected authenticated client over WebSocket.
    """
    order, token, headers = create_test_order()

    with client.websocket_connect(f"/ws/orders/{order['id']}?token={token}") as ws:
        # Drain initial greeting frame
        _ = ws.receive_json()

        # Simulate kitchen event broadcasting to this order channel
        update_payload = {
            "event": "STATUS_UPDATE",
            "order_id": order["id"],
            "status": "PREPARING",
            "message": "Kitchen is now preparing your delicious meal!"
        }
        asyncio.run(ws_manager.broadcast_order_update(order["id"], update_payload))

        # Client must receive the broadcast immediately
        broadcast_msg = ws.receive_json()
        assert broadcast_msg["event"] == "STATUS_UPDATE"
        assert broadcast_msg["status"] == "PREPARING"
        assert broadcast_msg["order_id"] == order["id"]


def test_websocket_nonexistent_order_rejected():
    """
    Verifies that attempting to open an authenticated WebSocket connection for an
    order that does not exist in MySQL is rejected with code 1008 (Policy Violation).
    """
    user_data, token, headers = create_test_customer_auth()

    try:
        with client.websocket_connect(f"/ws/orders/999999?token={token}"):
            pytest.fail("Connection for non-existent order should have been rejected!")
    except WebSocketDisconnect as exc:
        assert exc.code == 1008


def test_websocket_manager_lifecycle_and_cleanup():
    """
    Verifies that disconnecting removes the client from active_connections
    and deletes the channel key when empty, preventing memory leaks.
    """
    order, token, headers = create_test_order()
    order_id = order["id"]

    assert order_id not in ws_manager.active_connections

    with client.websocket_connect(f"/ws/orders/{order_id}?token={token}"):
        # While connected, channel must exist and have 1 listener
        assert order_id in ws_manager.active_connections
        assert len(ws_manager.active_connections[order_id]) == 1

    # After exiting context manager (client disconnects), room must be deleted
    assert order_id not in ws_manager.active_connections