"""
User Table Cleanup Script
Location: backend/clean_users.py

Purges all automated test accounts, leaving ONLY your master
admin account (shylendharm369@gmail.com) in the database.
"""

from sqlalchemy import text
from app.database import SessionLocal


def clean_test_users():
    db = SessionLocal()
    try:
        print("🧹 Cleaning up automated test users from MySQL...")
        
        # Delete all test accounts, preserving ONLY shylendharm369@gmail.com
        db.execute(text("DELETE FROM users WHERE email != 'shylendharm369@gmail.com';"))
        db.commit()

        # Count remaining users
        remaining = db.execute(text("SELECT id, name, email, role FROM users;")).fetchall()
        print(f"✅ Done! Remaining users in database ({len(remaining)}):")
        for u in remaining:
            print(f"   👤 ID: {u[0]} | Name: {u[1]} | Email: {u[2]} | Role: {u[3]}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error during cleanup: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    clean_test_users()