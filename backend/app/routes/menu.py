from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

# Import database session provider and ORM models
from app.database import get_db
from app.models import Category, MenuItem
from app.schemas import CategoryResponse, MenuItemResponse

# Import our Redis caching engine
from app.cache import get_cache, set_cache

# APIRouter acts as a modular mini-FastAPI application for menu-related endpoints
router = APIRouter(
    prefix="/api",
    tags=["Menu & Categories"]
)


# =============================================================
# 1. CATEGORIES ENDPOINT (CACHED)
# =============================================================

@router.get("/categories", response_model=List[CategoryResponse], summary="Fetch all menu categories (Cached)")
def get_categories(db: Session = Depends(get_db)):
    """
    Returns the list of all food categories.
    Implements Cache-Aside:
    1. Checks Redis for 'categories:all'.
    2. If found, returns in ~2ms.
    3. If not found, queries MySQL, saves to Redis, and returns.
    """
    cache_key = "categories:all"

    # Step 1: Check Redis Cache (In-Memory RAM)
    cached_categories = get_cache(cache_key)
    if cached_categories is not None:
        return cached_categories

    # Step 2: Cache Miss -> Query MySQL (Disk)
    categories = db.query(Category).order_by(Category.name.asc()).all()

    # Step 3: Serialize to JSON-safe dictionaries and save to Redis (1-hour TTL)
    serialized_categories = [
        CategoryResponse.model_validate(c).model_dump(mode="json")
        for c in categories
    ]
    set_cache(cache_key, serialized_categories, ttl_seconds=3600)

    return serialized_categories


# =============================================================
# 2. MENU ITEMS ENDPOINT (CACHED WITH FILTER KEYS)
# =============================================================

@router.get("/menu", response_model=List[MenuItemResponse], summary="Browse dishes with optional filters (Cached)")
def get_menu_items(
    category_id: Optional[int] = Query(None, description="Filter items by category ID"),
    is_veg: Optional[bool] = Query(None, description="Filter for vegetarian items only (true/false)"),
    db: Session = Depends(get_db)
):
    """
    Returns available dishes based on category and vegetarian filters.
    Generates dynamic Redis keys (e.g. 'menu:cat_5:veg_true').
    """
    # Step 1: Construct a unique cache key based on query parameters
    cat_part = str(category_id) if category_id is not None else "all"
    veg_part = str(is_veg).lower() if is_veg is not None else "all"
    cache_key = f"menu:cat_{cat_part}:veg_{veg_part}"

    # Step 2: Check Redis Cache
    cached_menu = get_cache(cache_key)
    if cached_menu is not None:
        return cached_menu

    # Step 3: Cache Miss -> Query MySQL
    query = db.query(MenuItem).filter(MenuItem.is_available == True)

    if category_id is not None:
        query = query.filter(MenuItem.category_id == category_id)

    if is_veg is not None:
        query = query.filter(MenuItem.is_veg == is_veg)

    items = query.order_by(MenuItem.name.asc()).all()

    # Step 4: Serialize to JSON-safe dicts and save to Redis RAM
    serialized_items = [
        MenuItemResponse.model_validate(item).model_dump(mode="json")
        for item in items
    ]
    set_cache(cache_key, serialized_items, ttl_seconds=3600)

    return serialized_items


# =============================================================
# 3. SINGLE DISH DETAIL ENDPOINT (CACHED)
# =============================================================

@router.get("/menu/{item_id}", response_model=MenuItemResponse, summary="Get details for a single dish (Cached)")
def get_menu_item(item_id: int, db: Session = Depends(get_db)):
    """
    Fetches a specific dish by ID. Cached under 'menu:item_{item_id}'.
    """
    cache_key = f"menu:item_{item_id}"

    # Step 1: Check Redis
    cached_dish = get_cache(cache_key)
    if cached_dish is not None:
        return cached_dish

    # Step 2: Cache Miss -> Query MySQL
    item = db.query(MenuItem).filter(
        MenuItem.id == item_id,
        MenuItem.is_available == True
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dish with ID {item_id} not found or is currently unavailable."
        )

    # Step 3: Serialize and save to Redis
    serialized_dish = MenuItemResponse.model_validate(item).model_dump(mode="json")
    set_cache(cache_key, serialized_dish, ttl_seconds=3600)

    return serialized_dish