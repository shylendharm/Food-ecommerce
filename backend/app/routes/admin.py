from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Import database provider, ORM models, Pydantic schemas, and security guard
from app.database import get_db
from app.models import Order, MenuItem, Category, OrderStatus, User
from app.schemas import (
    OrderResponse,
    OrderStatusUpdate,
    MenuItemCreate,
    MenuItemResponse
)
from app.security import get_current_admin

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin - Kitchen & Inventory Management"]
)


# =============================================================
# 1. KITCHEN ORDER MANAGEMENT ENDPOINTS
# =============================================================

@router.get("/orders", response_model=List[OrderResponse], summary="List all restaurant orders (Admin only)")
def list_all_orders(
    status_filter: Optional[OrderStatus] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Retrieves all orders placed across all customers.
    Can be filtered by status (e.g. ?status_filter=PENDING to see incoming tickets).
    Protected: Only accessible by users with role=ADMIN.
    """
    query = db.query(Order)
    if status_filter:
        query = query.filter(Order.status == status_filter)

    return query.order_by(Order.created_at.desc()).all()


@router.patch("/orders/{order_id}/status", response_model=OrderResponse, summary="Update an order's preparation/delivery status (Admin only)")
def update_order_status(
    order_id: int,
    status_payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Advances an order to the next stage:
    PENDING -> PREPARING -> OUT_FOR_DELIVERY -> DELIVERED
    Protected: Only accessible by restaurant staff/admin.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order #{order_id} does not exist."
        )

    order.status = status_payload.status
    db.commit()
    db.refresh(order)
    return order


# =============================================================
# 2. MENU INVENTORY MANAGEMENT ENDPOINTS
# =============================================================

@router.post("/menu", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED, summary="Add a new dish to the menu (Admin only)")
def create_menu_item(
    item_payload: MenuItemCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Allows the restaurant manager to create and publish a new dish.
    Validates that the parent category exists.
    Protected: Only accessible by restaurant staff/admin.
    """
    category = db.query(Category).filter(Category.id == item_payload.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {item_payload.category_id} does not exist."
        )

    new_dish = MenuItem(
        name=item_payload.name,
        description=item_payload.description,
        price=item_payload.price,
        is_veg=item_payload.is_veg,
        image_url=item_payload.image_url,
        is_available=item_payload.is_available,
        category_id=item_payload.category_id
    )

    db.add(new_dish)
    db.commit()
    db.refresh(new_dish)
    return new_dish


@router.patch("/menu/{item_id}/toggle-stock", response_model=MenuItemResponse, summary="Toggle dish availability in/out of stock (Admin only)")
def toggle_dish_stock(
    item_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    One-click toggle: If a dish was Available (True), marks it Out of Stock (False), and vice-versa.
    Protected: Only accessible by restaurant staff/admin.
    """
    dish = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dish #{item_id} does not exist."
        )

    dish.is_available = not dish.is_available
    db.commit()
    db.refresh(dish)
    return dish