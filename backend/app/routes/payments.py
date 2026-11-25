"""Payment processing, verification, and mock gateway integrations."""

import json
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.orm import Session

# Import database session, models, and schemas
from app.database import get_db
from app.models import Order, Payment, PaymentStatus, OrderStatus, User, UserRole
from app.schemas import (
    PaymentIntentCreate,
    PaymentIntentResponse,
    PaymentResponse
)
from app.security import get_current_user

# Import cryptographic gateway engine
from app.payment_gateway import (
    create_payment_order,
    verify_webhook_signature
)

router = APIRouter(
    prefix="/api/payments",
    tags=["Payments & Financial Settlements"]
)


# Create payment intent

@router.post("/create-intent", response_model=PaymentIntentResponse, summary="Initialize online payment session (Ownership Protected)")
def create_payment_intent(
    payload: PaymentIntentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initialize payment intent for an order."""
    # Fetch order
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order #{payload.order_id} does not exist."
        )

    # Verify order ownership
    if order.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have permission to initiate payment for this order."
        )

    # If already delivered or cancelled, don't allow paying
    if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot initiate payment: Order #{order.id} is already {order.status.value}."
        )

    # 2. Call gateway engine to initialize transaction
    intent_data = create_payment_order(
        order_id=order.id,
        amount=order.total_amount,
        currency="USD"
    )

    # 3. Check if a payment record already exists or create a new one
    payment_record = db.query(Payment).filter(Payment.order_id == order.id).first()
    if not payment_record:
        payment_record = Payment(
            order_id=order.id,
            transaction_id=intent_data["transaction_id"],
            amount=order.total_amount,
            currency="USD",
            provider="SANDBOX_GATEWAY",
            status=PaymentStatus.PENDING
        )
        db.add(payment_record)
    else:
        # Update transaction ID if customer is retrying payment
        payment_record.transaction_id = intent_data["transaction_id"]
        payment_record.status = PaymentStatus.PENDING

    db.commit()

    return {
        "order_id": order.id,
        "transaction_id": intent_data["transaction_id"],
        "amount": order.total_amount,
        "currency": "USD",
        "key_id": intent_data["key_id"]
    }


# Payment webhook

@router.post("/webhook", summary="Asynchronous Bank Webhook with HMAC SHA-256 Verification")
async def payment_gateway_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_signature: Optional[str] = Header(None, alias="X-Signature")
):
    """
    Asynchronous Webhook Listener:
    1. Reads raw HTTP byte stream directly from the socket.
    2. Verifies the HMAC-SHA256 signature in X-Signature header.
    3. If forged: Rejects with 400 Bad Request immediately.
    4. If genuine: Atomically updates Payment = SUCCESS and Order payment_method = ONLINE.
    5. Implements idempotency: If webhook arrives twice, safely ignores duplicate.
    """
    # Step 1: Read the exact raw incoming bytes
    payload_bytes = await request.body()

    # Step 2: Cryptographic Signature Verification
    if not x_signature or not verify_webhook_signature(payload_bytes, x_signature):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cryptographic verification failed: Invalid or forged webhook signature."
        )

    # Step 3: Signature is authentic! Parse the JSON payload safely
    try:
        data = json.loads(payload_bytes.decode("utf-8"))
        transaction_id = data.get("transaction_id")
        order_id = data.get("order_id")
        event_status = data.get("status")  # "SUCCESS" or "FAILED"
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed JSON body."
        )

    # Step 4: Look up the transaction in MySQL
    payment = db.query(Payment).filter(Payment.transaction_id == transaction_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' was not found in our ledger."
        )

    # Step 5: IDEMPOTENCY CHECK
    if payment.status == PaymentStatus.SUCCESS:
        return {"status": "already_processed", "message": "Payment already confirmed."}

    # Step 6: Process financial settlement
    order = db.query(Order).filter(Order.id == order_id).first()

    if event_status == "SUCCESS":
        payment.status = PaymentStatus.SUCCESS
        payment.signature = x_signature
        if order:
            order.payment_method = "ONLINE"
    else:
        payment.status = PaymentStatus.FAILED

    db.commit()

    return {
        "status": "confirmed",
        "order_id": order_id,
        "transaction_id": transaction_id,
        "payment_status": payment.status.value
    }


# Payment status

@router.get("/order/{order_id}", response_model=PaymentResponse, summary="Get payment details for an order (Ownership Protected)")
def get_payment_for_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get payment details for an order.
    """
    # Verify order ownership
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order #{order_id} was not found."
        )

    # Verify order ownership
    if order.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have permission to view payment records for this order."
        )

    # 2. Fetch the corresponding payment record
    payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No payment record found for Order #{order_id}."
        )

    return payment