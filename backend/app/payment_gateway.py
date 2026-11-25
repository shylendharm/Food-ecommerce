"""Mock payment gateway client and signature validation."""

import os
import hmac
import hashlib
import json
import uuid
from decimal import Decimal
from typing import Dict, Any, Tuple
from dotenv import load_dotenv

load_dotenv()

# Secret Key shared between our backend and the Payment Gateway
# In production, this lives in .env as an unguessable 64-character random string!
PAYMENT_WEBHOOK_SECRET = os.getenv("PAYMENT_WEBHOOK_SECRET", "super-secret-sandbox-webhook-key-998877")
SANDBOX_PUBLIC_KEY = os.getenv("SANDBOX_PUBLIC_KEY", "rzp_test_sandbox_key_12345")


# Initialize payment order

def create_payment_order(order_id: int, amount: Decimal, currency: str = "USD") -> Dict[str, Any]:
    """
    Initializes a payment intent with the gateway.
    Generates a unique transaction identifier and returns session metadata.
    """
    transaction_id = f"txn_sim_{uuid.uuid4().hex[:12]}"

    return {
        "order_id": order_id,
        "transaction_id": transaction_id,
        "amount": amount,
        "currency": currency,
        "key_id": SANDBOX_PUBLIC_KEY
    }


# Webhook signature verification

def generate_webhook_signature(payload_bytes: bytes, secret: str = PAYMENT_WEBHOOK_SECRET) -> str:
    """
    Calculates a cryptographic HMAC-SHA256 digital signature.
    Signature = HMAC-SHA256(Raw Request Body Bytes, Secret Key)
    Returns: 64-character hexadecimal digest string.
    """
    return hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()


def verify_webhook_signature(
    payload_bytes: bytes,
    provided_signature: str,
    secret: str = PAYMENT_WEBHOOK_SECRET
) -> bool:
    """
    Cryptographically verifies the authenticity of an incoming webhook.
    Uses hmac.compare_digest for constant-time comparison (prevents timing attacks).
    """
    if not provided_signature:
        return False

    # Recalculate the expected signature using our private secret key
    expected_signature = generate_webhook_signature(payload_bytes, secret)

    # CRITICAL SECURITY STEP:
    # Use hmac.compare_digest instead of standard '==' comparison!
    # Standard '==' exits on the first mismatched letter, allowing hackers
    # to guess signatures byte-by-byte using microsecond response timing.
    # compare_digest runs in constant time regardless of mismatches!
    return hmac.compare_digest(expected_signature, provided_signature)


# Sandbox webhook helper

def simulate_gateway_webhook(
    order_id: int,
    transaction_id: str,
    amount: Decimal,
    status: str = "SUCCESS"
) -> Tuple[bytes, str]:
    """
    Helper for testing and sandbox UI:
    Packages a valid gateway webhook JSON payload and signs it with the authentic HMAC signature.
    Returns: (raw_json_bytes, valid_hmac_signature)
    """
    payload_dict = {
        "event": "payment.captured" if status == "SUCCESS" else "payment.failed",
        "transaction_id": transaction_id,
        "order_id": order_id,
        "amount": float(amount),
        "status": status
    }

    # Convert to exact raw bytes
    raw_bytes = json.dumps(payload_dict, separators=(',', ':')).encode("utf-8")

    # Generate the genuine cryptographic signature
    valid_signature = generate_webhook_signature(raw_bytes)

    return raw_bytes, valid_signature