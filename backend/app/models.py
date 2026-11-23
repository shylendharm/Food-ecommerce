"""
Database Models (SQLAlchemy ORM)
Location: backend/app/models.py

Defines the MySQL table schemas for:
- Users (Customers & Administrators with Google OAuth2 SSO support)
- Categories (Pizzas, Burgers, Sides, Desserts)
- Menu Items (80 gourmet dishes with Veg/Non-Veg flags and stock availability)
- Orders (Kitchen lifecycle including CANCELLED with delivery addresses)
- Order Items (Frozen historical snapshots of purchased dishes)
- Payments (Financial settlements, HMAC cryptographic signatures & audit logs)
"""

import enum
from sqlalchemy import Column, Integer, String, Boolean, Numeric, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


# =============================================================
# ENUMERATIONS (Strict Type Safety for Database Columns)
# =============================================================

class UserRole(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    ADMIN = "ADMIN"


class AuthProvider(str, enum.Enum):
    LOCAL = "LOCAL"      # Standard email + password registration
    GOOGLE = "GOOGLE"    # Google OAuth2 Single Sign-On (SSO)


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    PREPARING = "PREPARING"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"  # Order voided/cancelled by restaurant or customer


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


# -------------------------------------------------------------
# 1. Users Model (Customers & Restaurant Staff)
# -------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(191), unique=True, index=True, nullable=False)
    
    # Nullable for Google SSO accounts since Google manages credentials
    password_hash = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    
    # Google OAuth2 Integration Fields
    auth_provider = Column(Enum(AuthProvider), default=AuthProvider.LOCAL, nullable=False)
    google_id = Column(String(191), unique=True, index=True, nullable=True)
    picture_url = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    orders = relationship("Order", back_populates="customer")


# -------------------------------------------------------------
# 2. Categories Model (Pizzas, Burgers, Sides, Desserts)
# -------------------------------------------------------------
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)

    # Relationships (No created_at - matches MySQL table)
    menu_items = relationship("MenuItem", back_populates="category", cascade="all, delete-orphan")


# -------------------------------------------------------------
# 3. Menu Items Model (Dishes, Pricing, Stock Status)
# -------------------------------------------------------------
class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(150), index=True, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    image_url = Column(String(500), nullable=True)
    is_veg = Column(Boolean, default=True, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)

    # Relationships (No created_at - matches MySQL table)
    category = relationship("Category", back_populates="menu_items")
    order_items = relationship("OrderItem", back_populates="menu_item")


# -------------------------------------------------------------
# 4. Orders Model (Kitchen Lifecycle & Delivery Tracking)
# -------------------------------------------------------------
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Guest & Delivery Contact Info
    customer_name = Column(String(100), nullable=False)
    customer_email = Column(String(191), nullable=False)
    customer_phone = Column(String(20), nullable=False)
    delivery_address = Column(Text, nullable=False)
    
    total_amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(50), default="COD", nullable=False)  # "COD" or "ONLINE"
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    customer = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")


# -------------------------------------------------------------
# 5. Order Items Model (Frozen Snapshots of Purchased Dishes)
# -------------------------------------------------------------
class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id", ondelete="SET NULL"), nullable=True)
    
    # Historical Snapshot Fields
    item_name_snapshot = Column(String(150), nullable=False)
    price_per_unit = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem", back_populates="order_items")


# -------------------------------------------------------------
# 6. Payments Model (Financial Settlements & HMAC Signatures)
# -------------------------------------------------------------
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    transaction_id = Column(String(100), unique=True, index=True, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    provider = Column(String(50), default="SANDBOX_GATEWAY", nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    signature = Column(String(255), nullable=True)  # Cryptographic HMAC SHA-256 audit signature
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    order = relationship("Order", back_populates="payments")