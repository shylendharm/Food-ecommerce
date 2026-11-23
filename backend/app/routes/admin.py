"""
Admin - Kitchen Operations & Inventory Management Router
Location: backend/app/routes/admin.py

Provides:
1. Real-time KPI metrics calculation (/metrics).
2. Full kitchen order management with WebSocket event broadcasts (/orders).
3. Complete 80-dish inventory management with Redis cache invalidation (/menu).
"""

from decimal import Decimal
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

# Import our Redis cache invalidator
from app.cache import invalidate_cache

# Import our Real-Time WebSocket broadcaster and Logistics engine
from app.websocket_manager import ws_manager
from app.logistics import compute_order_logistics

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin - Kitchen & Inventory Management"]
)


# =============================================================
# 1. REAL-TIME EXECUTIVE METRICS (KPIs)
# =============================================================

@router.get("/metrics", summary="Get executive real-time restaurant metrics (Admin only)")
def get_admin_metrics(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Computes real-time operational and financial health metrics:
    1. Total revenue earned from completed orders ($).
    2. Active tickets currently being cooked in the kitchen.
    3. Orders currently on the road with delivery riders.
    4. Out-of-stock dish counts across the 80-item menu.
    """
    # 1. Revenue from delivered orders
    delivered_orders = db.query(Order).filter(Order.status == OrderStatus.DELIVERED).all()
    total_revenue = sum([o.total_amount for o in delivered_orders], Decimal("0.00"))

    # 2. Stage counts
    total_orders = db.query(Order).count()
    pending_orders = db.query(Order).filter(Order.status == OrderStatus.PENDING).count()
    preparing_orders = db.query(Order).filter(Order.status == OrderStatus.PREPARING).count()
    delivering_orders = db.query(Order).filter(Order.status == OrderStatus.OUT_FOR_DELIVERY).count()
    completed_orders = len(delivered_orders)

    # 3. Inventory health
    total_dishes = db.query(MenuItem).count()
    out_of_stock_dishes = db.query(MenuItem).filter(MenuItem.is_available == False).count()

    return {
        "total_revenue": float(total_revenue),
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "preparing_orders": preparing_orders,
        "delivering_orders": delivering_orders,
        "completed_orders": completed_orders,
        "active_kitchen_orders": pending_orders + preparing_orders,
        "total_dishes": total_dishes,
        "out_of_stock_dishes": out_of_stock_dishes
    }


# =============================================================
# 2. KITCHEN ORDER MANAGEMENT (WITH LIVE WEBSOCKET BROADCAST)
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


@router.patch("/orders/{order_id}/status", response_model=OrderResponse, summary="Update status & broadcast live event (Admin only)")
async def update_order_status(
    order_id: int,
    status_payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Advances an order to the next stage:
    PENDING -> PREPARING -> OUT_FOR_DELIVERY -> DELIVERED
    1. Updates status in MySQL.
    2. Recalculates dynamic delivery ETA.
    3. Broadcasts real-time event to customer over WebSockets in 0ms!
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order #{order_id} does not exist."
        )

    # 1. Update MySQL state
    order.status = status_payload.status
    db.commit()
    db.refresh(order)

    # 2. Recompute real-time logistics and ETA for the new stage
    logistics = compute_order_logistics(order.status.value, order.delivery_address)

    # 3. 📡 BROADCAST TO CUSTOMER IN REAL-TIME:
    event_payload = {
        "event": "STATUS_UPDATE",
        "order_id": order.id,
        "status": order.status.value,
        "logistics": logistics
    }
    await ws_manager.broadcast_order_update(order.id, event_payload)

    return order


# =============================================================
# 3. COMPLETE 80-DISH INVENTORY MANAGEMENT (ADMIN FULL ACCESS)
# =============================================================

@router.get("/menu", response_model=List[MenuItemResponse], summary="List all dishes including out-of-stock (Admin only)")
def list_admin_menu(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Returns the complete inventory of all dishes (both in-stock and sold-out).
    Used by the Admin Inventory Management table.
    """
    return db.query(MenuItem).order_by(MenuItem.category_id.asc(), MenuItem.name.asc()).all()


@router.post("/menu", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED, summary="Add a new dish to the menu (Admin only)")
def create_menu_item(
    item_payload: MenuItemCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Allows the restaurant manager to create and publish a new dish.
    Validates parent category exists, saves to MySQL, and purges Redis cache.
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

    # 🧹 Purge Redis cache so customers instantly see the new dish
    invalidate_cache("menu:*")

    return new_dish


@router.patch("/menu/{item_id}/toggle-stock", response_model=MenuItemResponse, summary="Toggle dish availability in/out of stock (Admin only)")
def toggle_dish_stock(
    item_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    One-click toggle: If a dish was Available (True), marks it Out of Stock (False), and vice-versa.
    Saves to MySQL and purges Redis cache.
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

    # 🧹 Purge Redis cache
    invalidate_cache("menu:*")

    return dish