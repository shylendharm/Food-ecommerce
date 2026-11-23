"""
Database Schema Migration: Add CANCELLED to orders.status ENUM
Location: backend/migrate_orders.py

Alters the MySQL `orders` table to allow CANCELLED in the status column:
ALTER TABLE orders MODIFY COLUMN status 
ENUM('PENDING', 'PREPARING', 'OUT_FOR_DELIVERY', 'DELIVERED', 'CANCELLED')
NOT NULL DEFAULT 'PENDING';
"""

from sqlalchemy import text
from app.database import engine

def migrate():
    print("🔧 Updating MySQL orders table schema...")
    with engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE orders MODIFY COLUMN status "
            "ENUM('PENDING', 'PREPARING', 'OUT_FOR_DELIVERY', 'DELIVERED', 'CANCELLED') "
            "NOT NULL DEFAULT 'PENDING';"
        ))
        conn.commit()
    print("✅ Successfully updated orders.status enum in MySQL to support CANCELLED!")

if __name__ == "__main__":
    migrate()