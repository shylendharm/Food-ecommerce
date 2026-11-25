"""Integration tests for payment creation, webhooks, and HMAC verification."""

import json
import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.payment_gateway import simulate_gateway_webhook

client = TestClient(app)


# HELPER FIXTURES: AUTHENTICATED TEST CUSTOMERS & ORDERS

def create_test_customer_auth() -> tuple[dict, dict]:
    """
    Creates an isolated test customer in MySQL.
    Returns: (user_data, auth_headers_dict)
    """
    unique_suffix = uuid.uuid4().hex[:8]
    email = f"pay_tester_{unique_suffix}@example.com"
    password = "StrongPassword123!"

    register_payload = {
        "name": f"Pay Tester {unique_suffix}",
        "email": email,
        "password": password,
        "phone": "9876543210",
        "default_address": "404 Wall Street, Financial District, Bengaluru"
    }

    reg_res = client.post("/api/auth/register", json=register_payload)
    assert reg_res.status_code == 201, f"Failed to register test user: {reg_res.text}"
    user_data = reg_res.json()

    login_res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login_res.status_code == 200, f"Failed to authenticate test user: {login_res.text}"
    token = login_res.json()["access_token"]

    return user_data, {"Authorization": f"Bearer {token}"}


def create_test_order(auth_headers: dict = None) -> tuple[dict, dict]:
    """
    Creates an authenticated order in MySQL.
    Returns: (created_order_dict, auth_headers_used)
    """
    if auth_headers is None:
        user_data, auth_headers = create_test_customer_auth()
    else:
        user_data = {"name": "Existing User", "email": "user@example.com", "phone": "9876543210", "default_address": "Default Address 101"}

    menu_res = client.get("/api/menu")
    assert menu_res.status_code == 200 and len(menu_res.json()) > 0
    dish_id = menu_res.json()[0]["id"]

    order_payload = {
        "customer_name": user_data["name"],
        "customer_email": user_data["email"],
        "customer_phone": user_data["phone"],
        "delivery_address": user_data["default_address"],
        "payment_method": "ONLINE",
        "items": [{"menu_item_id": dish_id, "quantity": 2}]
    }
    res = client.post("/api/orders", json=order_payload, headers=auth_headers)
    assert res.status_code == 201
    return res.json(), auth_headers


# 1. PAYMENT INTENT INITIALIZATION TEST (HAPPY PATH)

def test_create_payment_intent():
    """
    Verifies that create-intent generates a valid transaction ticket
    and stores a PENDING payment record in MySQL when called with ownership token.
    """
    order, headers = create_test_order()

    res = client.post(
        "/api/payments/create-intent",
        json={"order_id": order["id"]},
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()

    assert data["order_id"] == order["id"]
    assert data["transaction_id"].startswith("txn_sim_")
    assert float(data["amount"]) == float(order["total_amount"])
    assert data["currency"] == "USD"
    assert "key_id" in data


# 2. HACKER ATTACK TESTS: SIGNATURE FORGERY REJECTION (400)

def test_forged_webhook_signature_is_rejected():
    """
    Penetration Test: A hacker calls /api/payments/webhook with a fake signature.
    Must be stopped at the door with 400 Bad Request!
    """
    order, headers = create_test_order()

    # Step 1: Initialize payment intent
    intent = client.post(
        "/api/payments/create-intent",
        json={"order_id": order["id"]},
        headers=headers
    ).json()

    # Step 2: Hacker tries to forge a SUCCESS webhook with a fake signature
    fake_body = json.dumps({
        "event": "payment.captured",
        "transaction_id": intent["transaction_id"],
        "order_id": order["id"],
        "amount": 10.0,
        "status": "SUCCESS"
    }).encode("utf-8")

    fake_headers = {
        "X-Signature": "fake_forged_signature_attacker_cannot_guess_this",
        "Content-Type": "application/json"
    }

    res = client.post("/api/payments/webhook", content=fake_body, headers=fake_headers)
    assert res.status_code == 400
    assert "cryptographic verification failed" in res.json()["detail"].lower()


def test_missing_signature_header_is_rejected():
    """
    Penetration Test: Calling webhook with NO X-Signature header must fail.
    """
    res = client.post("/api/payments/webhook", content=b"{}", headers={"Content-Type": "application/json"})
    assert res.status_code == 400


# 3. GENUINE BANK WEBHOOK TEST (HMAC VERIFIED SUCCESS)

def test_genuine_bank_webhook_confirms_payment():
    """
    Verifies the end-to-end payment settlement:
    1. Customer creates intent.
    2. Bank signs genuine HMAC-SHA256 signature and fires webhook.
    3. Server verifies signature, updates Payment = SUCCESS, and Order = ONLINE.
    """
    order, headers = create_test_order()

    # Step 1: Create intent
    intent = client.post(
        "/api/payments/create-intent",
        json={"order_id": order["id"]},
        headers=headers
    ).json()
    txn_id = intent["transaction_id"]

    # Step 2: Simulate Gateway generating genuine raw bytes + HMAC signature
    raw_bytes, valid_sig = simulate_gateway_webhook(
        order_id=order["id"],
        transaction_id=txn_id,
        amount=order["total_amount"],
        status="SUCCESS"
    )

    # Step 3: Bank delivers the webhook
    webhook_headers = {
        "X-Signature": valid_sig,
        "Content-Type": "application/json"
    }
    webhook_res = client.post("/api/payments/webhook", content=raw_bytes, headers=webhook_headers)
    assert webhook_res.status_code == 200
    assert webhook_res.json()["payment_status"] == "SUCCESS"

    # Step 4: Verify payment ledger in MySQL via GET /api/payments/order/{id} (Ownership Protected)
    ledger_res = client.get(f"/api/payments/order/{order['id']}", headers=headers)
    assert ledger_res.status_code == 200
    assert ledger_res.json()["status"] == "SUCCESS"
    assert ledger_res.json()["transaction_id"] == txn_id


# 4. IDEMPOTENCY TEST: DUPLICATE WEBHOOK RETRIES

def test_webhook_idempotency_duplicate_handling():
    """
    Idempotency Test: If the Bank's network retries and delivers the same
    webhook twice, the second call must be safely ignored without error!
    """
    order, headers = create_test_order()
    intent = client.post(
        "/api/payments/create-intent",
        json={"order_id": order["id"]},
        headers=headers
    ).json()
    txn_id = intent["transaction_id"]

    raw_bytes, valid_sig = simulate_gateway_webhook(
        order_id=order["id"],
        transaction_id=txn_id,
        amount=order["total_amount"],
        status="SUCCESS"
    )
    webhook_headers = {"X-Signature": valid_sig, "Content-Type": "application/json"}

    # Delivery 1: Processed
    res1 = client.post("/api/payments/webhook", content=raw_bytes, headers=webhook_headers)
    assert res1.status_code == 200
    assert res1.json()["status"] == "confirmed"

    # Delivery 2: Duplicate ignored cleanly!
    res2 = client.post("/api/payments/webhook", content=raw_bytes, headers=webhook_headers)
    assert res2.status_code == 200
    assert res2.json()["status"] == "already_processed"


# 5. AUTOMATED SECURITY PENETRATION & IDOR SUITE (SEC-02)

def test_create_payment_intent_unauthenticated_fails_401():
    """
    Security Test (SEC-02): Attempting to initiate payment intent without a token.
    Expects: HTTP 401 Unauthorized.
    """
    order, headers = create_test_order()

    res = client.post("/api/payments/create-intent", json={"order_id": order["id"]})
    assert res.status_code == 401


def test_create_payment_intent_other_user_forbidden_403():
    """
    Security Penetration Test (SEC-02 IDOR): Customer B attempts to initiate payment
    for an order placed by Customer A.
    Expects: HTTP 403 Forbidden with permission denial message.
    """
    order_a, headers_a = create_test_order()
    user_b, headers_b = create_test_customer_auth()

    attack_res = client.post(
        "/api/payments/create-intent",
        json={"order_id": order_a["id"]},
        headers=headers_b
    )
    assert attack_res.status_code == 403
    assert "permission" in attack_res.json()["detail"].lower() or "forbidden" in attack_res.json()["detail"].lower()


def test_get_payment_ledger_unauthenticated_fails_401():
    """
    Security Test (SEC-02): Attempting to inspect financial records without a token.
    Expects: HTTP 401 Unauthorized.
    """
    order, headers = create_test_order()

    res = client.get(f"/api/payments/order/{order['id']}")
    assert res.status_code == 401


def test_get_payment_ledger_other_user_forbidden_403():
    """
    Security Penetration Test (SEC-02 IDOR): Customer B attempts to view Customer A's
    private transaction details and financial ledger record.
    Expects: HTTP 403 Forbidden with permission denial message.
    """
    order_a, headers_a = create_test_order()
    user_b, headers_b = create_test_customer_auth()

    # Create intent as owner
    client.post("/api/payments/create-intent", json={"order_id": order_a["id"]}, headers=headers_a)

    # Customer B attempts to peek at Customer A's payment receipt
    attack_res = client.get(f"/api/payments/order/{order_a['id']}", headers=headers_b)
    assert attack_res.status_code == 403
    assert "permission" in attack_res.json()["detail"].lower() or "forbidden" in attack_res.json()["detail"].lower()