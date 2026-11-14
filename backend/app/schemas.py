from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from app.models import UserRole, OrderStatus

# =============================================================
# 1. CATEGORY SCHEMAS
# =============================================================
class CategoryBase(BaseModel):
    name: str = Field(..., example="Starters")
    slug: str = Field(..., example="starters")

class CategoryResponse(CategoryBase):
    id: int

    class Config:
        from_attributes = True  # Allows Pydantic to read SQLAlchemy model objects!


# =============================================================
# 2. MENU ITEM SCHEMAS
# =============================================================
class MenuItemBase(BaseModel):
    name: str = Field(..., example="Margherita Pizza")
    description: Optional[str] = Field(None, example="Fresh mozzarella, basil, and tomato sauce")
    price: Decimal = Field(..., ge=0, example=299.00)
    is_veg: bool = True
    image_url: Optional[str] = Field(None, example="https://images.unsplash.com/photo-1513104890138-7c749659a591")
    is_available: bool = True
    category_id: int

class MenuItemResponse(MenuItemBase):
    id: int

    class Config:
        from_attributes = True


# =============================================================
# 3. ORDER ITEM SCHEMAS (Items inside an order)
# =============================================================
# What the customer sends when adding an item to their order:
class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int = Field(..., gt=0, example=2)  # gt=0 means quantity must be greater than 0!

# What the server returns to show what was ordered:
class OrderItemResponse(BaseModel):
    id: int
    menu_item_id: Optional[int]
    item_name_snapshot: str
    price_per_unit: Decimal
    quantity: int

    class Config:
        from_attributes = True


# =============================================================
# 4. ORDER SCHEMAS
# =============================================================
# What the customer submits from the checkout form:
class OrderCreate(BaseModel):
    customer_name: str = Field(..., min_length=2, example="John Doe")
    customer_email: EmailStr = Field(..., example="john@example.com")
    customer_phone: str = Field(..., min_length=10, max_length=15, example="9876543210")
    delivery_address: str = Field(..., min_length=5, example="Flat 402, Sunshine Apartments, Bengaluru")
    payment_method: str = Field(default="COD", example="COD")
    items: List[OrderItemCreate] = Field(..., min_items=1)  # Order must have at least 1 item!

# What the server returns after an order is placed:
class OrderResponse(BaseModel):
    id: int
    user_id: Optional[int]
    customer_name: str
    customer_email: str
    customer_phone: str
    delivery_address: str
    total_amount: Decimal
    payment_method: str
    status: OrderStatus
    created_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True


# =============================================================
# 5. USER & AUTH SCHEMAS
# =============================================================
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)  # Plain text from signup form (will be hashed)
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Notice: UserResponse NEVER includes password or password_hash!
class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: Optional[str]
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True