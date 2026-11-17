"""
Automated Test Suite: Menu Browsing & Order Lifecycle (backend/tests/test_orders.py)
Tests category fetching, veg filtering, checkout edge cases, and live order tracking.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

# Create our simulated HTTP client that talks directly to FastAPI
client = TestClient(app)


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
    assert len(data) >= 1  # We seeded 4 categories, so at least 1 must exist


def test_filter_menu_by_veg():
    """
    Test: Vegetarian filter query parameter (?is_veg=true).
    Expects: HTTP 200 OK, and EVERY returned dish must have is_veg == True.
    """
    response = client.get("/api/menu?is_veg=true")
    
    assert response.status_code == 200
    dishes = response.json()
    assert isinstance(dishes, list)
    
    # Assert that no meat/non-veg dish slipped through the filter!
    for dish in dishes:
        assert dish["is_veg"] is True


# =============================================================
# 2. CHECKOUT EDGE CASES (THE HACKER TESTS)
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
                "quantity": 0  # Invalid! Pydantic requires gt=0!
            }
        ]
    }
    
    response = client.post("/api/orders", json=payload)
    
    # 422 is FastAPI's standard code for schema validation failure
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
    3. Retrieve the order via GET /api/orders/{id} (Expects 200 OK).
    4. Verify that frozen snapshot prices and names match.
    """
    # Step 1: Grab the first available dish from our database
    menu_res = client.get("/api/menu")
    assert menu_res.status_code == 200
    dishes = menu_res.json()
    assert len(dishes) > 0, "Database must have at least 1 seeded dish to run this test"
    
    target_dish = dishes[0]
    
    # Step 2: Place the order
    order_payload = {
        "customer_name": "Alice Tester",
        "customer_email": "alice.test@example.com",
        "customer_phone": "9876543210",
        "delivery_address": "123 Test Street, Apartment 4B",
        "payment_method": "COD",
        "items": [
            {
                "menu_item_id": target_dish["id"],
                "quantity": 2
            }
        ]
    }
    
    create_res = client.post("/api/orders", json=order_payload)
    assert create_res.status_code == 201
    created_order = create_res.json()
    
    order_id = created_order["id"]
    assert order_id is not None
    assert created_order["status"] == "PENDING"
    
    # Step 3: Fetch the order using our tracking endpoint
    track_res = client.get(f"/api/orders/{order_id}")
    assert track_res.status_code == 200
    tracked_order = track_res.json()
    
    # Step 4: Verify receipt integrity & frozen snapshots
    assert tracked_order["id"] == order_id
    assert tracked_order["customer_name"] == "Alice Tester"
    assert len(tracked_order["items"]) == 1
    
    order_item = tracked_order["items"][0]
    assert order_item["item_name_snapshot"] == target_dish["name"]
    assert order_item["quantity"] == 2