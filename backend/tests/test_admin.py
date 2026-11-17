"""
Automated Test Suite: Admin Portal & Role-Based Access Control (RBAC)
Location: backend/tests/test_admin.py

Verifies:
1. 401 Unauthorized when unauthenticated users access protected endpoints.
2. 403 Forbidden when regular customers attempt admin operations.
3. 200 OK and 201 Created when a genuine administrator performs kitchen and menu actions.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Helper function: Logs in a user and returns their Authorization Bearer header
def get_auth_header(email: str, password: str) -> dict:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, f"Login failed for {email}: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# =============================================================
# 1. UNAUTHENTICATED TESTS (Should be 401 Unauthorized)
# =============================================================

def test_unauthenticated_requests_are_rejected():
    """
    Penetration Test: Calling protected endpoints with NO token
    must be rejected with 401 Unauthorized.
    """
    # 1. Stranger calls Customer Profile
    res1 = client.get("/api/auth/me")
    assert res1.status_code == 401

    # 2. Stranger calls Customer Order History
    res2 = client.get("/api/orders/my-orders")
    assert res2.status_code == 401

    # 3. Stranger calls Admin Orders List
    res3 = client.get("/api/admin/orders")
    assert res3.status_code == 401


# =============================================================
# 2. CUSTOMER RBAC TESTS (Should be 403 Forbidden on Admin routes)
# =============================================================

def test_customer_can_access_profile_and_my_orders():
    """
    Verifies that a logged-in customer (Alice) CAN view her own profile
    and order history.
    """
    customer_headers = get_auth_header("alice@example.com", "customer123")

    # 1. Customer checks profile
    res_me = client.get("/api/auth/me", headers=customer_headers)
    assert res_me.status_code == 200
    assert res_me.json()["email"] == "alice@example.com"
    assert res_me.json()["role"] == "CUSTOMER"

    # 2. Customer checks their order history
    res_orders = client.get("/api/orders/my-orders", headers=customer_headers)
    assert res_orders.status_code == 200
    assert isinstance(res_orders.json(), list)


def test_customer_is_forbidden_from_admin_portal():
    """
    RBAC Security Test: A customer (Alice) trying to access the Kitchen Dashboard
    must be stopped at the door with 403 Forbidden!
    """
    customer_headers = get_auth_header("alice@example.com", "customer123")

    # 1. Alice tries to list all restaurant orders
    res_orders = client.get("/api/admin/orders", headers=customer_headers)
    assert res_orders.status_code == 403
    assert "forbidden" in res_orders.json()["detail"].lower()

    # 2. Alice tries to create a dish
    # Dynamically fetch an existing category ID
    cat_res = client.get("/api/categories")
    valid_cat_id = cat_res.json()[0]["id"]

    new_dish_payload = {
        "name": "Hacker Pizza",
        "description": "Should never be created",
        "price": 99.99,
        "is_veg": True,
        "category_id": valid_cat_id
    }
    res_create = client.post("/api/admin/menu", json=new_dish_payload, headers=customer_headers)
    assert res_create.status_code == 403


# =============================================================
# 3. GENUINE ADMIN TESTS (Should succeed with 200 / 201)
# =============================================================

def test_admin_can_view_orders_and_update_status():
    """
    Verifies that the restaurant manager can view orders and advance their status.
    """
    admin_headers = get_auth_header("admin@restaurant.com", "admin123")

    # 1. Dynamically get an existing menu item ID
    menu_res = client.get("/api/menu")
    assert menu_res.status_code == 200 and len(menu_res.json()) > 0
    valid_dish_id = menu_res.json()[0]["id"]

    # 2. Place an order using the valid dish ID
    order_payload = {
        "customer_name": "Test Customer",
        "customer_email": "test@example.com",
        "customer_phone": "9876543210",
        "delivery_address": "Test Flat 101",
        "payment_method": "COD",
        "items": [{"menu_item_id": valid_dish_id, "quantity": 1}]
    }
    place_res = client.post("/api/orders", json=order_payload)
    assert place_res.status_code == 201
    order_id = place_res.json()["id"]

    # 3. Admin retrieves all orders
    list_res = client.get("/api/admin/orders", headers=admin_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 4. Admin advances the order status to PREPARING
    patch_res = client.patch(
        f"/api/admin/orders/{order_id}/status",
        json={"status": "PREPARING"},
        headers=admin_headers
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "PREPARING"


def test_admin_can_add_dish_and_toggle_stock():
    """
    Verifies that the admin can publish a new dish and toggle its in-stock status.
    """
    admin_headers = get_auth_header("admin@restaurant.com", "admin123")

    # 1. Dynamically get a valid category ID from MySQL
    cat_res = client.get("/api/categories")
    assert cat_res.status_code == 200 and len(cat_res.json()) > 0
    valid_category_id = cat_res.json()[0]["id"]

    # 2. Admin creates a new dish attached to that valid category
    dish_payload = {
        "name": "Chef's Signature Garlic Bread",
        "description": "Toasted sourdough with roasted garlic herb butter",
        "price": 149.00,
        "is_veg": True,
        "is_available": True,
        "category_id": valid_category_id
    }
    create_res = client.post("/api/admin/menu", json=dish_payload, headers=admin_headers)
    assert create_res.status_code == 201
    dish_data = create_res.json()
    dish_id = dish_data["id"]
    assert dish_data["name"] == "Chef's Signature Garlic Bread"
    assert dish_data["is_available"] is True

    # 3. Admin toggles stock (marks it Out of Stock)
    toggle_res = client.patch(f"/api/admin/menu/{dish_id}/toggle-stock", headers=admin_headers)
    assert toggle_res.status_code == 200
    assert toggle_res.json()["is_available"] is False

    # 4. Admin toggles it back to Available
    toggle_back_res = client.patch(f"/api/admin/menu/{dish_id}/toggle-stock", headers=admin_headers)
    assert toggle_back_res.status_code == 200
    assert toggle_back_res.json()["is_available"] is True