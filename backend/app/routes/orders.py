from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Import database session provider, ORM models, and security guards
from app.database import get_db
from app.models import MenuItem, Order, OrderItem, User
from app.schemas import OrderCreate, OrderResponse
from app.security import get_current_user, get_optional_current_user

router = APIRouter(
    prefix="/api/orders",
    tags=["Orders & Checkout"]
)


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED, summary="Place a new food order")
def place_order(
    order_payload: OrderCreate,
    db: Session = Depends(get_db),
    optional_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Places a new order through an atomic database transaction:
    1. Validates that all requested menu items exist and are available.
    2. Retrieves official prices directly from the database (prevents price tampering).
    3. Calculates total amount server-side.
    4. Freezes dish names and prices into immutable order_items snapshots.
    5. Links user_id if the customer is logged in, or leaves it null for guests.
    6. Commits the master order and child items atomically.
    """
    total_amount = Decimal("0.00")
    order_items_to_save = []

    # Step 1: Validate items and fetch authoritative prices from DB
    for item_data in order_payload.items:
        dish = db.query(MenuItem).filter(MenuItem.id == item_data.menu_item_id).first()

        if not dish:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with ID {item_data.menu_item_id} does not exist."
            )

        if not dish.is_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dish '{dish.name}' is currently marked out of stock."
            )

        item_total = dish.price * item_data.quantity
        total_amount += item_total

        order_item_record = OrderItem(
            menu_item_id=dish.id,
            item_name_snapshot=dish.name,
            quantity=item_data.quantity,
            price_per_unit=dish.price
        )
        order_items_to_save.append(order_item_record)

    # Step 2: Determine user linkage (Logged in vs Guest)
    user_id = optional_user.id if optional_user else None

    # Step 3: Assemble the master Order
    new_order = Order(
        user_id=user_id,
        customer_name=order_payload.customer_name,
        customer_email=order_payload.customer_email,
        customer_phone=order_payload.customer_phone,
        delivery_address=order_payload.delivery_address,
        payment_method=order_payload.payment_method,
        total_amount=total_amount,
        status="PENDING",
        items=order_items_to_save
    )

    # Step 4: Atomic Transaction Block
    try:
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        return new_order
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to place order due to a database error. Please try again."
        )


@router.get("/my-orders", response_model=List[OrderResponse], summary="Get order history for the logged-in customer")
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves all past orders belonging to the authenticated customer.
    Protected endpoint: Requires customer login!
    """
    orders = db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()
    return orders


@router.get("/{order_id}", response_model=OrderResponse, summary="Track order status and view receipt")
def get_order_by_id(order_id: int, db: Session = Depends(get_db)):
    """
    Retrieves complete details of an order (status, items snapshot, total, delivery info).
    Used by the frontend order-tracking page.
    """
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order #{order_id} was not found."
        )

    return order