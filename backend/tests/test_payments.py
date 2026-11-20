"""
Automated Test Suite: Financial Settlements & HMAC Webhook Security
Location: backend/tests/test_payments.py

Verifies:
1. Payment intent initialization and transaction ticket generation.
2. Cryptographic rejection (400 Bad Request) on forged or missing HMAC signatures.
3. Successful settlement and MySQL state transition on genuine HMAC webhook.
4. Idempotent processing of duplicate webhook events.
"""

import json
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.payment_gateway import simulate_gateway_webhook

client = TestClient(app)


# Helper: Creates a fresh test order in MySQL
def create_test_order() -> dict:
    menu_res = client.get("/api/menu")
    assert menu_res.status_code == 200 and len(menu_res.json()) > 0
    dish_id = menu_res.json()[0]["id"]

    order_payload = {
        "customer_name": "Fintech Tester",
        "customer_email": "fintech@example.com",
        "customer_phone": "9876543210",
        "delivery_address": "404 Wall Street, Financial District",
        "payment_method": "ONLINE",
        "items": [{"menu_item_id": dish_id, "quantity": 2}]
    }
    res = client.post("/api/orders", json=order_payload)
    assert res.status_code == 201
    return res.json()


# =============================================================
# 1. PAYMENT INTENT INITIALIZATION TEST
# =============================================================

def test_create_payment_intent():
    """
    Verifies that create-intent generates a valid transaction ticket
    and stores a PENDING payment record in MySQL.
    """
    order = create_test_order()

    res = client.post("/api/payments/create-intent", json={"order_id": order["id"]})
    assert res.status_code == 200
    data = res.json()

    assert data["order_id"] == order["id"]
    assert data["transaction_id"].startswith("txn_sim_")
    assert float(data["amount"]) == float(order["total_amount"])
    assert data["currency"] == "USD"
    assert "key_id" in data


# =============================================================
# 2. HACKER ATTACK TESTS: SIGNATURE FORGERY REJECTION (400)
# =============================================================

def test_forged_webhook_signature_is_rejected():
    """
    Penetration Test: A hacker calls /api/payments/webhook with a fake signature.
    Must be stopped at the door with 400 Bad Request!
    """
    order = create_test_order()

    # Step 1: Initialize payment intent
    intent = client.post("/api/payments/create-intent", json={"order_id": order["id"]}).json()

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


# =============================================================
# 3. GENUINE BANK WEBHOOK TEST (HMAC VERIFIED SUCCESS)
# =============================================================

def test_genuine_bank_webhook_confirms_payment():
    """
    Verifies the end-to-end payment settlement:
    1. Customer creates intent.
    2. Bank signs genuine HMAC-SHA256 signature and fires webhook.
    3. Server verifies signature, updates Payment = SUCCESS, and Order = ONLINE.
    """
    order = create_test_order()

    # Step 1: Create intent
    intent = client.post("/api/payments/create-intent", json={"order_id": order["id"]}).json()
    txn_id = intent["transaction_id"]

    # Step 2: Simulate Gateway generating genuine raw bytes + HMAC signature
    raw_bytes, valid_sig = simulate_gateway_webhook(
        order_id=order["id"],
        transaction_id=txn_id,
        amount=order["total_amount"],
        status="SUCCESS"
    )

    # Step 3: Bank delivers the webhook
    headers = {
        "X-Signature": valid_sig,
        "Content-Type": "application/json"
    }
    webhook_res = client.post("/api/payments/webhook", content=raw_bytes, headers=headers)
    assert webhook_res.status_code == 200
    assert webhook_res.json()["payment_status"] == "SUCCESS"

    # Step 4: Verify payment ledger in MySQL via GET /api/payments/order/{id}
    ledger_res = client.get(f"/api/payments/order/{order['id']}")
    assert ledger_res.status_code == 200
    assert ledger_res.json()["status"] == "SUCCESS"
    assert ledger_res.json()["transaction_id"] == txn_id


# =============================================================
# 4. IDEMPOTENCY TEST: DUPLICATE WEBHOOK RETRIES
# =============================================================

def test_webhook_idempotency_duplicate_handling():
    """
    Idempotency Test: If the Bank's network retries and delivers the same
    webhook twice, the second call must be safely ignored without error!
    """
    order = create_test_order()
    intent = client.post("/api/payments/create-intent", json={"order_id": order["id"]}).json()
    txn_id = intent["transaction_id"]

    raw_bytes, valid_sig = simulate_gateway_webhook(
        order_id=order["id"],
        transaction_id=txn_id,
        amount=order["total_amount"],
        status="SUCCESS"
    )
    headers = {"X-Signature": valid_sig, "Content-Type": "application/json"}

    # Delivery 1: Processed
    res1 = client.post("/api/payments/webhook", content=raw_bytes, headers=headers)
    assert res1.status_code == 200
    assert res1.json()["status"] == "confirmed"

    # Delivery 2: Duplicate ignored cleanly!
    res2 = client.post("/api/payments/webhook", content=raw_bytes, headers=headers)
    assert res2.status_code == 200
    assert res2.json()["status"] == "already_processed"