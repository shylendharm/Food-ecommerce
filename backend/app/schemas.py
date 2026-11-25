"""Pydantic validation schemas for API requests and responses."""

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from app.models import UserRole, OrderStatus, PaymentStatus, AuthProvider


# Category schemas
class CategoryBase(BaseModel):
    name: str = Field(..., example="Starters")
    slug: str = Field(..., example="starters")

class CategoryResponse(CategoryBase):
    id: int

    class Config:
        from_attributes = True


# Menu item schemas
class MenuItemBase(BaseModel):
    name: str = Field(..., example="Margherita Pizza")
    description: Optional[str] = Field(None, example="Fresh mozzarella, basil, and tomato sauce")
    price: Decimal = Field(..., ge=0, example=299.00)
    is_veg: bool = True
    image_url: Optional[str] = Field(None, example="https://images.unsplash.com/photo-1513104890138-7c749659a591")
    is_available: bool = True
    category_id: int

class MenuItemCreate(MenuItemBase):
    pass

class MenuItemResponse(MenuItemBase):
    id: int

    class Config:
        from_attributes = True


# Order item schemas
class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int = Field(..., gt=0, example=2)

class OrderItemResponse(BaseModel):
    id: int
    menu_item_id: Optional[int]
    item_name_snapshot: str
    price_per_unit: Decimal
    quantity: int

    class Config:
        from_attributes = True


# Order schemas
class OrderCreate(BaseModel):
    customer_name: str = Field(..., min_length=2, example="John Doe")
    customer_email: EmailStr = Field(..., example="john@example.com")
    customer_phone: str = Field(..., min_length=10, max_length=15, example="9876543210")
    delivery_address: str = Field(..., min_length=5, example="Flat 402, Sunshine Apartments, Bengaluru")
    payment_method: str = Field(default="COD", example="COD")
    items: List[OrderItemCreate] = Field(..., min_length=1)

class OrderStatusUpdate(BaseModel):
    status: OrderStatus = Field(..., example="PREPARING")

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


# User and auth schemas
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)
    phone: Optional[str] = None
    default_address: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Payload sent by frontend when customer clicks 'Sign in with Google':
class GoogleAuthRequest(BaseModel):
    credential: str = Field(..., description="Google ID Token JWT returned by Google Identity Services")

# Payload sent by frontend during the mandatory onboarding profile setup:
class UserProfileUpdate(BaseModel):
    name: str = Field(..., min_length=2, example="John Doe")
    phone: str = Field(..., min_length=10, max_length=15, example="9876543210")
    default_address: str = Field(..., min_length=5, example="Flat 402, Sunshine Apartments, Bengaluru")

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None
    default_address: Optional[str] = None
    role: UserRole
    auth_provider: AuthProvider = AuthProvider.LOCAL
    picture_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Payment schemas
class PaymentIntentCreate(BaseModel):
    order_id: int = Field(..., example=1)

class PaymentIntentResponse(BaseModel):
    order_id: int
    transaction_id: str
    amount: Decimal
    currency: str
    key_id: str

class PaymentWebhookPayload(BaseModel):
    event: str = Field(..., example="payment.captured")
    transaction_id: str = Field(..., example="txn_sim_123456")
    order_id: int = Field(..., example=1)
    amount: Decimal = Field(..., example=34.99)
    status: PaymentStatus = Field(..., example="SUCCESS")

class PaymentResponse(BaseModel):
    id: int
    order_id: int
    transaction_id: str
    amount: Decimal
    currency: str
    provider: str
    status: PaymentStatus
    created_at: datetime

    class Config:
        from_attributes = True