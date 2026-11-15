"""
Database Seeding Script
Populates MySQL with initial categories, dishes, and test accounts.
Run from the terminal:
    cd backend
    python seed.py
"""

from decimal import Decimal
from app.database import SessionLocal
from app.models import Category, MenuItem, User, UserRole
from app.security import hash_password


def seed_database():
    # 1. Create a direct database connection session
    db = SessionLocal()

    try:
        # 2. Idempotency Check: Don't insert duplicate data if already seeded
        if db.query(Category).first():
            print("⚠️  Database already contains data. Seeding skipped to avoid duplicates!")
            return

        print("🌱 Seeding database with fresh categories, dishes, and test users...")

        # 3. Create Categories
        pizzas = Category(name="Pizzas", slug="pizzas")
        burgers = Category(name="Burgers", slug="burgers")
        sides_drinks = Category(name="Sides & Drinks", slug="sides-drinks")
        desserts = Category(name="Desserts", slug="desserts")

        db.add_all([pizzas, burgers, sides_drinks, desserts])
        
        # db.flush() writes to MySQL immediately so MySQL generates the category IDs (1, 2, 3, 4)
        # without ending our transaction yet!
        db.flush()

        # 4. Create Menu Items (linked to category IDs above)
        menu_items = [
            # --- Pizzas ---
            MenuItem(
                category_id=pizzas.id,
                name="Margherita Supreme",
                description="Classic sourdough crust topped with San Marzano tomato sauce, fresh mozzarella, and sweet basil.",
                price=Decimal("12.99"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=600&auto=format&fit=crop",
                is_available=True
            ),
            MenuItem(
                category_id=pizzas.id,
                name="Pepperoni Feast",
                description="Loaded with crispy spiced pepperoni, aged mozzarella, and rich marinara sauce.",
                price=Decimal("15.49"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1628840042765-356cda07504e?w=600&auto=format&fit=crop",
                is_available=True
            ),
            MenuItem(
                category_id=pizzas.id,
                name="Spicy Paneer Tikka Pizza",
                description="Tandoori-spiced paneer cubes, crunchy bell peppers, red onions, and mozzarella on a crispy crust.",
                price=Decimal("14.25"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=600&auto=format&fit=crop",
                is_available=True
            ),

            # --- Burgers ---
            MenuItem(
                category_id=burgers.id,
                name="Classic Smash Cheeseburger",
                description="Double crispy smashed beef patties, melted American cheddar, pickles, and signature house sauce on a toasted brioche bun.",
                price=Decimal("10.99"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&auto=format&fit=crop",
                is_available=True
            ),
            MenuItem(
                category_id=burgers.id,
                name="Crispy Veggie Crunch Burger",
                description="Golden potato and herb patty with fresh iceberg lettuce, sliced tomatoes, and creamy vegan garlic mayo.",
                price=Decimal("8.99"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1550547660-d9450f859349?w=600&auto=format&fit=crop",
                is_available=True
            ),

            # --- Sides & Drinks ---
            MenuItem(
                category_id=sides_drinks.id,
                name="Seasoned Truffle Fries",
                description="Hand-cut golden potatoes tossed in fragrant white truffle oil, sea salt, and fresh parsley.",
                price=Decimal("5.50"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1576107232684-1279f3908594?w=600&auto=format&fit=crop",
                is_available=True
            ),
            MenuItem(
                category_id=sides_drinks.id,
                name="Cold Brew Iced Coffee",
                description="Slow-steeped organic dark roast served chilled over ice with a touch of creamy oat milk.",
                price=Decimal("4.25"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1517701604599-bb29b565090c?w=600&auto=format&fit=crop",
                is_available=True
            ),

            # --- Desserts ---
            MenuItem(
                category_id=desserts.id,
                name="Warm Molten Lava Cake",
                description="Rich dark Belgian chocolate cake with a warm, gooey liquid chocolate center, dusted with powdered sugar.",
                price=Decimal("6.99"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=600&auto=format&fit=crop",
                is_available=True
            ),
        ]

        db.add_all(menu_items)

        # 5. Create Test Users (Passwords are properly salted & hashed with bcrypt!)
        admin_user = User(
            name="Restaurant Manager",
            email="admin@restaurant.com",
            phone="9876543210",
            password_hash=hash_password("admin123"),
            role=UserRole.ADMIN
        )

        customer_user = User(
            name="Alice Customer",
            email="alice@example.com",
            phone="9876543211",
            password_hash=hash_password("customer123"),
            role=UserRole.CUSTOMER
        )

        db.add_all([admin_user, customer_user])

        # 6. Commit the entire batch to MySQL
        db.commit()
        print("✅ Success! Database seeded with 4 categories, 8 dishes, and 2 test users.")

    except Exception as e:
        db.rollback()
        print(f"❌ Failed to seed database: {e}")
    finally:
        # Always close the session to return connection back to the pool
        db.close()


if __name__ == "__main__":
    seed_database()