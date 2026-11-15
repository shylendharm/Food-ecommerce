from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

# Import our database session provider and ORM models
from app.database import get_db
from app.models import Category, MenuItem
from app.schemas import CategoryResponse, MenuItemResponse

# APIRouter acts as a modular mini-FastAPI application for menu-related endpoints
router = APIRouter(
    prefix="/api",
    tags=["Menu & Categories"]
)


@router.get("/categories", response_model=List[CategoryResponse], summary="Fetch all menu categories")
def get_categories(db: Session = Depends(get_db)):
    """
    Returns the list of all food categories (e.g., Pizzas, Burgers, Drinks)
    ordered alphabetically by name.
    """
    categories = db.query(Category).order_by(Category.name.asc()).all()
    return categories


@router.get("/menu", response_model=List[MenuItemResponse], summary="Browse dishes with optional filters")
def get_menu_items(
    category_id: Optional[int] = Query(None, description="Filter items by category ID"),
    is_veg: Optional[bool] = Query(None, description="Filter for vegetarian items only (true/false)"),
    db: Session = Depends(get_db)
):
    """
    Returns all active menu items.
    Supports query parameters for filtering by category and vegetarian preference:
    - Example: /api/menu?category_id=1
    - Example: /api/menu?is_veg=true
    - Example: /api/menu?category_id=1&is_veg=true
    """
    # Start with a base query: only retrieve items marked as available
    query = db.query(MenuItem).filter(MenuItem.is_available == True)

    # Conditionally apply filters if the client passed them
    if category_id is not None:
        query = query.filter(MenuItem.category_id == category_id)

    if is_veg is not None:
        query = query.filter(MenuItem.is_veg == is_veg)

    items = query.order_by(MenuItem.name.asc()).all()
    return items


@router.get("/menu/{item_id}", response_model=MenuItemResponse, summary="Get details for a single dish")
def get_menu_item(item_id: int, db: Session = Depends(get_db)):
    """
    Fetches a specific dish by its unique ID.
    Returns HTTP 404 if the item doesn't exist or is unavailable.
    """
    item = db.query(MenuItem).filter(
        MenuItem.id == item_id,
        MenuItem.is_available == True
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dish with ID {item_id} not found or is currently unavailable."
        )

    return item