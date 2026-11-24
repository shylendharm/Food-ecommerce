"""
Automated Test Suite: Menu Browsing, Order Lifecycle, Customer Cancellation & Security Penetration
Location: backend/tests/test_orders.py

Tests:
1. Menu & category catalog queries and vegetarian filters.
2. Order creation edge cases (Pydantic quantity validations, non-existent menu items).
3. Full order creation and snapshot integrity verification.
4. Customer self-serve cancellation (Auth guard, happy path, ownership guard, state machine guard, duplicate guard).
5. Security Penetration Suite (SEC-01 IDOR defense, unauthenticated 401 rejection, cross-user 403 rejection, admin override).
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Order, OrderStatus

# Create our simulated HTTP client that talks directly to FastAPI
client = TestClient(app)


# =============================================================
# HELPER FIXTURES: USER REGISTRATION & AUTH TOKENS
# =============================================================

def create_test_customer_auth() -> tuple[dict, dict]:
    """
    Creates a dedicated test user in MySQL and returns (user_data, auth_headers).
    Guarantees isolated user identity for each test execution.
    """
    unique_suffix = uuid.uuid4().hex[:8]
    email = f"order_test_{unique_suffix}@example.com"
    password = "StrongPassword123!"

    register_payload = {
        "name": f"Tester {unique_suffix}",
        "email": email,
        "password": password,
        "phone": "9876543210",
        "default_address": "100 Innovation Parkway, Bengaluru"
    }

    reg_response = client.post("/api/auth/register", json=register_payload)
    assert reg_response.status_code == 201, f"Failed to register test user: {reg_response.text}"
    user_data = reg_response.json()

    login_response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200, f"Failed to authenticate test user: {login_response.text}"
    token = login_response.json()["access_token"]

    return user_data, {"Authorization": f"Bearer {token}"}


def create_test_admin_auth() -> tuple[dict, dict]:
    """
    Authenticates the master admin account and returns (user_data, auth_headers).
    """
    res = client.post(
        "/api/auth/google",
        json={"credential": "mock_google_token_shylendharm369@gmail.com"}
    )
    assert res.status_code == 200, f"Failed to authenticate master admin: {res.text}"
    token = res.json()["access_token"]
    return res.json()["user"], {"Authorization": f"Bearer {token}"}


def get_first_available_menu_item() -> dict:
    """
    Retrieves the first active dish from the database for checkout payloads.
    """
    menu_res = client.get("/api/menu")
    assert menu_res.status_code == 200
    dishes = menu_res.json()
    assert len(dishes) > 0, "Database must have at least 1 seeded dish to execute order tests."
    return dishes[0]


# =============================================================
# 1. MENU & CATEGORIES TESTS
# =============================================================

def test_get_categories():
    """
    Test: Fetching all categories.
    Expects: HTTP 200 OK and a non-empty list.
    """
    response = client.get("/api/categories")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_filter_menu_by_veg():
    """
    Test: Vegetarian filter query parameter (?is_veg=true).
    Expects: HTTP 200 OK, and every returned dish must have is_veg == True.
    """
    response = client.get("/api/menu?is_veg=true")
    
    assert response.status_code == 200
    dishes = response.json()
    assert isinstance(dishes, list)
    
    for dish in dishes:
        assert dish["is_veg"] is True


# =============================================================
# 2. CHECKOUT EDGE CASES
# =============================================================

def test_order_invalid_quantity_fails():
    """
    Edge Case: User tries to submit an order with quantity 0 or negative.
    Expects: HTTP 422 Unprocessable Entity (Pydantic gt=0 schema validation rule).
    """
    payload = {
        "customer_name": "Bad Actor",
        "customer_email": "bad@example.com",
        "customer_phone": "1234567890",
        "delivery_address": "Nowhere",
        "payment_method": "COD",
        "items": [
            {
                "menu_item_id": 1,
                "quantity": 0
            }
        ]
    }
    
    response = client.post("/api/orders", json=payload)
    assert response.status_code == 422


def test_order_nonexistent_item_fails():
    """
    Edge Case: User tries to order a dish ID that does not exist in MySQL.
    Expects: HTTP 404 Not Found with descriptive detail message.
    """
    fake_item_id = 99999
    payload = {
        "customer_name": "Ghost Customer",
        "customer_email": "ghost@example.com",
        "customer_phone": "1234567890",
        "delivery_address": "Haunted House, Floor 13",
        "payment_method": "COD",
        "items": [
            {
                "menu_item_id": fake_item_id,
                "quantity": 1
            }
        ]
    }
    
    response = client.post("/api/orders", json=payload)
    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"].lower()


# =============================================================
# 3. COMPLETE ORDER & TRACKING LIFECYCLE
# =============================================================

def test_create_and_track_order():
    """
    Happy Path:
    1. Fetch the menu to get a real valid dish ID.
    2. Place an order via POST /api/orders (Expects 201 Created).
    3. Retrieve the order via GET /api/orders/{id} with ownership token (Expects 200 OK).
    4. Verify that frozen snapshot prices and names match.
    """
    user_data, auth_headers = create_test_customer_auth()
    target_dish = get_first_available_menu_item()
    
    order_payload = {
        "customer_name": user_data["name"],
        "customer_email": user_data["email"],
        "customer_phone": user_data["phone"],
        "delivery_address": user_data["default_address"],
        "payment_method": "COD",
        "items": [
            {
                "menu_item_id": target_dish["id"],
                "quantity": 2
            }
        ]
    }
    
    create_res = client.post("/api/orders", json=order_payload, headers=auth_headers)
    assert create_res.status_code == 201
    created_order = create_res.json()
    
    order_id = created_order["id"]
    assert order_id is not None
    assert created_order["status"] == "PENDING"
    
    track_res = client.get(f"/api/orders/{order_id}", headers=auth_headers)
    assert track_res.status_code == 200
    tracked_order = track_res.json()
    
    assert tracked_order["id"] == order_id
    assert tracked_order["customer_name"] == user_data["name"]
    assert len(tracked_order["items"]) == 1
    
    order_item = tracked_order["items"][0]
    assert order_item["item_name_snapshot"] == target_dish["name"]
    assert order_item["quantity"] == 2


# =============================================================
# 4. CUSTOMER ORDER CANCELLATION TESTS
# =============================================================

def test_cancel_order_unauthenticated_fails():
    """
    Security Test: Attempting to cancel an order without Bearer token.
    Expects: HTTP 401 Unauthorized.
    """
    response = client.patch("/api/orders/1/cancel")
    assert response.status_code == 401


def test_customer_cancel_pending_order_success():
    """
    Happy Path: Authenticated customer cancels their own PENDING order.
    Expects: HTTP 200 OK, status updated to CANCELLED in MySQL.
    """
    user_data, auth_headers = create_test_customer_auth()
    target_dish = get_first_available_menu_item()

    # Step 1: Place an authenticated order
    order_payload = {
        "customer_name": user_data["name"],
        "customer_email": user_data["email"],
        "customer_phone": user_data["phone"],
        "delivery_address": user_data["default_address"],
        "payment_method": "COD",
        "items": [{"menu_item_id": target_dish["id"], "quantity": 1}]
    }

    create_res = client.post("/api/orders", json=order_payload, headers=auth_headers)
    assert create_res.status_code == 201
    order_id = create_res.json()["id"]
    assert create_res.json()["status"] == "PENDING"

    # Step 2: Cancel the order via customer self-serve endpoint
    cancel_res = client.patch(f"/api/orders/{order_id}/cancel", headers=auth_headers)
    assert cancel_res.status_code == 200
    cancelled_data = cancel_res.json()
    assert cancelled_data["id"] == order_id
    assert cancelled_data["status"] == "CANCELLED"

    # Step 3: Verify MySQL persistence (Protected retrieval)
    fetch_res = client.get(f"/api/orders/{order_id}", headers=auth_headers)
    assert fetch_res.status_code == 200
    assert fetch_res.json()["status"] == "CANCELLED"


def test_customer_cancel_other_user_order_forbidden():
    """
    Security / IDOR Test: A customer attempts to cancel an order belonging to another customer.
    Expects: HTTP 403 Forbidden with permission denial message.
    """
    owner_user, owner_headers = create_test_customer_auth()
    stranger_user, stranger_headers = create_test_customer_auth()
    target_dish = get_first_available_menu_item()

    # Step 1: Owner places the order
    order_payload = {
        "customer_name": owner_user["name"],
        "customer_email": owner_user["email"],
        "customer_phone": owner_user["phone"],
        "delivery_address": owner_user["default_address"],
        "payment_method": "COD",
        "items": [{"menu_item_id": target_dish["id"], "quantity": 1}]
    }
    create_res = client.post("/api/orders", json=order_payload, headers=owner_headers)
    assert create_res.status_code == 201
    order_id = create_res.json()["id"]

    # Step 2: Stranger attempts to cancel the owner's order
    attack_res = client.patch(f"/api/orders/{order_id}/cancel", headers=stranger_headers)
    assert attack_res.status_code == 403
    assert "permission" in attack_res.json()["detail"].lower()

    # Step 3: Verify the order remains unmolested (PENDING) in MySQL
    fetch_res = client.get(f"/api/orders/{order_id}", headers=owner_headers)
    assert fetch_res.status_code == 200
    assert fetch_res.json()["status"] == "PENDING"


def test_customer_cancel_in_progress_order_fails():
    """
    State Machine Guard: Customer attempts to cancel an order that is already PREPARING.
    Expects: HTTP 400 Bad Request.
    """
    user_data, auth_headers = create_test_customer_auth()
    target_dish = get_first_available_menu_item()

    # Step 1: Place order
    order_payload = {
        "customer_name": user_data["name"],
        "customer_email": user_data["email"],
        "customer_phone": user_data["phone"],
        "delivery_address": user_data["default_address"],
        "payment_method": "COD",
        "items": [{"menu_item_id": target_dish["id"], "quantity": 1}]
    }
    create_res = client.post("/api/orders", json=order_payload, headers=auth_headers)
    assert create_res.status_code == 201
    order_id = create_res.json()["id"]

    # Step 2: Advance order to PREPARING in MySQL
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        order.status = OrderStatus.PREPARING
        db.commit()
    finally:
        db.close()

    # Step 3: Customer attempts to cancel the order
    cancel_res = client.patch(f"/api/orders/{order_id}/cancel", headers=auth_headers)
    assert cancel_res.status_code == 400
    detail_lower = cancel_res.json()["detail"].lower()
    assert "cannot be cancelled" in detail_lower or "preparing" in detail_lower


def test_customer_cancel_already_cancelled_order_fails():
    """
    Idempotency Guard: Attempting to cancel an order that is already CANCELLED.
    Expects: HTTP 400 Bad Request.
    """
    user_data, auth_headers = create_test_customer_auth()
    target_dish = get_first_available_menu_item()

    # Step 1: Place and cancel order
    order_payload = {
        "customer_name": user_data["name"],
        "customer_email": user_data["email"],
        "customer_phone": user_data["phone"],
        "delivery_address": user_data["default_address"],
        "payment_method": "COD",
        "items": [{"menu_item_id": target_dish["id"], "quantity": 1}]
    }
    create_res = client.post("/api/orders", json=order_payload, headers=auth_headers)
    assert create_res.status_code == 201
    order_id = create_res.json()["id"]

    first_cancel = client.patch(f"/api/orders/{order_id}/cancel", headers=auth_headers)
    assert first_cancel.status_code == 200

    # Step 2: Attempt duplicate second cancellation
    second_cancel = client.patch(f"/api/orders/{order_id}/cancel", headers=auth_headers)
    assert second_cancel.status_code == 400
    assert "already been cancelled" in second_cancel.json()["detail"].lower()


# =============================================================
# 5. AUTOMATED SECURITY PENETRATION & IDOR SUITE (SEC-01)
# =============================================================

def test_get_order_unauthenticated_fails_401():
    """
    Penetration Test (SEC-01): An anonymous caller attempts to fetch an order receipt without a JWT.
    Expects: HTTP 401 Unauthorized.
    """
    owner_user, owner_headers = create_test_customer_auth()
    target_dish = get_first_available_menu_item()

    order_payload = {
        "customer_name": owner_user["name"],
        "customer_email": owner_user["email"],
        "customer_phone": owner_user["phone"],
        "delivery_address": owner_user["default_address"],
        "payment_method": "COD",
        "items": [{"menu_item_id": target_dish["id"], "quantity": 1}]
    }
    create_res = client.post("/api/orders", json=order_payload, headers=owner_headers)
    assert create_res.status_code == 201
    order_id = create_res.json()["id"]

    # Attempt to read order receipt with NO Authorization header
    res = client.get(f"/api/orders/{order_id}")
    assert res.status_code == 401
    assert "credentials" in res.json()["detail"].lower() or "not authenticated" in res.json()["detail"].lower()


def test_get_order_idor_attack_forbidden_403():
    """
    Penetration Test (SEC-01 IDOR): Customer B attempts to inspect Customer A's order receipt.
    Expects: HTTP 403 Forbidden with permission denial message.
    """
    user_a, headers_a = create_test_customer_auth()
    user_b, headers_b = create_test_customer_auth()
    target_dish = get_first_available_menu_item()

    # User A places order
    order_payload = {
        "customer_name": user_a["name"],
        "customer_email": user_a["email"],
        "customer_phone": user_a["phone"],
        "delivery_address": user_a["default_address"],
        "payment_method": "COD",
        "items": [{"menu_item_id": target_dish["id"], "quantity": 1}]
    }
    create_res = client.post("/api/orders", json=order_payload, headers=headers_a)
    assert create_res.status_code == 201
    order_a_id = create_res.json()["id"]

    # User B attempts to access User A's order receipt
    attack_res = client.get(f"/api/orders/{order_a_id}", headers=headers_b)
    assert attack_res.status_code == 403
    assert "permission" in attack_res.json()["detail"].lower() or "forbidden" in attack_res.json()["detail"].lower()


def test_get_order_owner_access_success_200():
    """
    Happy Path (SEC-01): Legitimate owner accesses their own order receipt.
    Expects: HTTP 200 OK with full order items and customer data.
    """
    owner_user, owner_headers = create_test_customer_auth()
    target_dish = get_first_available_menu_item()

    order_payload = {
        "customer_name": owner_user["name"],
        "customer_email": owner_user["email"],
        "customer_phone": owner_user["phone"],
        "delivery_address": owner_user["default_address"],
        "payment_method": "COD",
        "items": [{"menu_item_id": target_dish["id"], "quantity": 2}]
    }
    create_res = client.post("/api/orders", json=order_payload, headers=owner_headers)
    assert create_res.status_code == 201
    order_id = create_res.json()["id"]

    res = client.get(f"/api/orders/{order_id}", headers=owner_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == order_id
    assert data["customer_email"] == owner_user["email"]
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2


def test_get_order_admin_override_access_200():
    """
    Authorization Test (RBAC): Restaurant administrator accesses a customer's order for kitchen operations.
    Expects: HTTP 200 OK bypass override.
    """
    customer_user, customer_headers = create_test_customer_auth()
    admin_user, admin_headers = create_test_admin_auth()
    target_dish = get_first_available_menu_item()

    order_payload = {
        "customer_name": customer_user["name"],
        "customer_email": customer_user["email"],
        "customer_phone": customer_user["phone"],
        "delivery_address": customer_user["default_address"],
        "payment_method": "COD",
        "items": [{"menu_item_id": target_dish["id"], "quantity": 1}]
    }
    create_res = client.post("/api/orders", json=order_payload, headers=customer_headers)
    assert create_res.status_code == 201
    order_id = create_res.json()["id"]

    # Admin fetches customer ticket
    admin_res = client.get(f"/api/orders/{order_id}", headers=admin_headers)
    assert admin_res.status_code == 200
    assert admin_res.json()["id"] == order_id