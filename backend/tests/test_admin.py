"""Integration tests for admin dashboard and kitchen operations."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Helper function: Obtains JWT Bearer header for regular customer via Google SSO
def get_customer_auth_header() -> dict:
    response = client.post("/api/auth/google", json={
        "credential": "mock_google_token_customer@gmail.com"
    })
    assert response.status_code == 200, f"Customer Google login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# Helper function: Obtains JWT Bearer header for master admin via Google SSO
def get_admin_auth_header() -> dict:
    response = client.post("/api/auth/google", json={
        "credential": "mock_google_token_shylendharm369@gmail.com"
    })
    assert response.status_code == 200, f"Admin Google login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# 1. UNAUTHENTICATED TESTS (Should be 401 Unauthorized)

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

    # 4. Stranger calls Executive Metrics
    res4 = client.get("/api/admin/metrics")
    assert res4.status_code == 401

    # 5. Stranger calls Admin Menu Inventory
    res5 = client.get("/api/admin/menu")
    assert res5.status_code == 401


# 2. CUSTOMER RBAC TESTS (Should be 403 Forbidden on Admin routes)

def test_customer_can_access_profile_and_my_orders():
    """
    Verifies that a logged-in customer CAN view their own profile
    and order history.
    """
    customer_headers = get_customer_auth_header()

    # 1. Customer checks profile
    res_me = client.get("/api/auth/me", headers=customer_headers)
    assert res_me.status_code == 200
    assert res_me.json()["email"] == "customer@gmail.com"
    assert res_me.json()["role"] == "CUSTOMER"

    # 2. Customer checks their order history
    res_orders = client.get("/api/orders/my-orders", headers=customer_headers)
    assert res_orders.status_code == 200
    assert isinstance(res_orders.json(), list)


def test_customer_is_forbidden_from_admin_portal():
    """
    RBAC Security Test: A customer trying to access the Kitchen Dashboard
    or Executive Analytics must be stopped at the door with 403 Forbidden!
    """
    customer_headers = get_customer_auth_header()

    # 1. Customer tries to list all restaurant orders
    res_orders = client.get("/api/admin/orders", headers=customer_headers)
    assert res_orders.status_code == 403
    assert "forbidden" in res_orders.json()["detail"].lower()

    # 2. Customer tries to spy on Executive Metrics
    res_metrics = client.get("/api/admin/metrics", headers=customer_headers)
    assert res_metrics.status_code == 403

    # 3. Customer tries to inspect the Admin Menu inventory endpoint
    res_menu = client.get("/api/admin/menu", headers=customer_headers)
    assert res_menu.status_code == 403

    # 4. Customer tries to create a dish
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


# 3. GENUINE ADMIN TESTS (shylendharm369@gmail.com)

def test_admin_metrics_telemetry():
    """
    Verifies that the master admin can fetch real-time restaurant metrics
    and that all mathematical invariants hold.
    """
    admin_headers = get_admin_auth_header()

    res = client.get("/api/admin/metrics", headers=admin_headers)
    assert res.status_code == 200

    metrics = res.json()
    # Contract validation: All required KPI keys must exist
    required_keys = [
        "total_revenue", "total_orders", "pending_orders", 
        "preparing_orders", "delivering_orders", "completed_orders", 
        "active_kitchen_orders", "total_dishes", "out_of_stock_dishes"
    ]
    for key in required_keys:
        assert key in metrics, f"Missing KPI metric key: {key}"

    # Mathematical integrity assertions
    assert isinstance(metrics["total_revenue"], (int, float))
    assert metrics["active_kitchen_orders"] == metrics["pending_orders"] + metrics["preparing_orders"]
    assert metrics["total_dishes"] >= 80  # All 80 seeded gourmet dishes accounted for
    assert metrics["out_of_stock_dishes"] >= 0


def test_admin_menu_returns_all_including_out_of_stock():
    """
    Verifies that GET /api/admin/menu returns all 80 dishes
    and continues to show items even after they are marked Out of Stock.
    """
    admin_headers = get_admin_auth_header()

    # 1. Fetch entire menu catalog via admin endpoint
    res = client.get("/api/admin/menu", headers=admin_headers)
    assert res.status_code == 200
    all_dishes = res.json()
    assert isinstance(all_dishes, list)
    assert len(all_dishes) >= 80

    # 2. Pick a dish and toggle its stock to Out of Stock
    target_dish = all_dishes[0]
    dish_id = target_dish["id"]

    toggle_res = client.patch(f"/api/admin/menu/{dish_id}/toggle-stock", headers=admin_headers)
    assert toggle_res.status_code == 200
    new_stock_state = toggle_res.json()["is_available"]

    # 3. Verify /api/admin/menu still lists the dish with its updated stock state
    refreshed_menu = client.get("/api/admin/menu", headers=admin_headers).json()
    matched = next((d for d in refreshed_menu if d["id"] == dish_id), None)
    assert matched is not None
    assert matched["is_available"] == new_stock_state

    # 4. Clean up: Toggle it back to original state
    client.patch(f"/api/admin/menu/{dish_id}/toggle-stock", headers=admin_headers)


def test_admin_can_view_orders_and_update_status():
    """
    Verifies that the master admin can view incoming orders
    and advance their status along the kitchen lifecycle.
    """
    admin_headers = get_admin_auth_header()

    # 1. Dynamically get an existing menu item ID from the fresh 80 dishes
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


def test_admin_can_cancel_order():
    """
    Verifies that the master admin can cancel an order, that the status transitions
    to CANCELLED in MySQL, and that it remains visible in the orders ledger.
    """
    admin_headers = get_admin_auth_header()

    # 1. Dynamically get an existing menu item ID
    menu_res = client.get("/api/menu")
    assert menu_res.status_code == 200 and len(menu_res.json()) > 0
    valid_dish_id = menu_res.json()[0]["id"]

    # 2. Place an order to cancel
    order_payload = {
        "customer_name": "Cancel Test Customer",
        "customer_email": "cancel_test@example.com",
        "customer_phone": "9876543210",
        "delivery_address": "Test Cancel Suite 99",
        "payment_method": "COD",
        "items": [{"menu_item_id": valid_dish_id, "quantity": 1}]
    }
    place_res = client.post("/api/orders", json=order_payload)
    assert place_res.status_code == 201
    order_id = place_res.json()["id"]

    # 3. Admin cancels the order via PATCH /api/admin/orders/{id}/status
    cancel_res = client.patch(
        f"/api/admin/orders/{order_id}/status",
        json={"status": "CANCELLED"},
        headers=admin_headers
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

    # 4. Verify orders list reflects CANCELLED status
    list_res = client.get("/api/admin/orders", headers=admin_headers)
    assert list_res.status_code == 200
    matched_order = next((o for o in list_res.json() if o["id"] == order_id), None)
    assert matched_order is not None
    assert matched_order["status"] == "CANCELLED"


def test_admin_can_add_dish_and_toggle_stock():
    """
    Verifies that the master admin can publish a new dish and toggle its in-stock status.
    """
    admin_headers = get_admin_auth_header()

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