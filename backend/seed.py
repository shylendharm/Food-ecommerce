"""Database reset and seed script for FoodExpress menu items and categories."""

from decimal import Decimal
from sqlalchemy import text
from app.database import SessionLocal
from app.models import Category, MenuItem
from app.cache import redis_client


def reset_and_seed():
    db = SessionLocal()

    try:
        print("Resetting database tables...")
        # Temporarily disable foreign key constraints to allow clean truncates
        db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        db.execute(text("TRUNCATE TABLE payments;"))
        db.execute(text("TRUNCATE TABLE order_items;"))
        db.execute(text("TRUNCATE TABLE orders;"))
        db.execute(text("TRUNCATE TABLE menu_items;"))
        db.execute(text("TRUNCATE TABLE categories;"))
        db.execute(text("TRUNCATE TABLE users;"))
        db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        db.commit()
        print("Tables reset.")

        # Flush Redis Cache
        print("Flushing Redis cache...")
        try:
            if redis_client:
                redis_client.flushdb()
                print("Redis cache cleared.")
        except Exception as redis_err:
            print(f"   Could not flush Redis: {redis_err}")

        # Create categories
        print("Seeding categories...")
        cat_pizzas = Category(name="Pizzas", slug="pizzas")
        cat_burgers = Category(name="Burgers & Sandwiches", slug="burgers")
        cat_sides = Category(name="Sides & Appetizers", slug="sides-appetizers")
        cat_desserts = Category(name="Desserts & Beverages", slug="desserts-beverages")

        db.add_all([cat_pizzas, cat_burgers, cat_sides, cat_desserts])
        db.flush() # Flushes to MySQL to generate category IDs

        print("Seeding menu items...")

        dishes = [
            # Pizzas
            # --- Veg Pizzas ---
            MenuItem(
                category_id=cat_pizzas.id,
                name="Margherita Supreme",
                description="San Marzano tomato sauce, fresh buffalo mozzarella, aromatic basil, and extra virgin olive oil.",
                price=Decimal("12.99"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1604382355076-af4b0eb60143?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_pizzas.id,
                name="Spicy Paneer Tikka Pizza",
                description="Char-grilled spiced paneer cubes, crunchy bell peppers, pickled red onions, and mozzarella.",
                price=Decimal("14.49"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_pizzas.id,
                name="Quattro Formaggi",
                description="Four artisanal cheeses: fresh mozzarella, aged parmesan, gorgonzola dolce, and creamy ricotta.",
                price=Decimal("15.99"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_pizzas.id,
                name="Wild Truffle & Mushroom Pizza",
                description="Roasted portobello and button mushrooms, white truffle cream drizzle, and fresh thyme.",
                price=Decimal("16.99"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_pizzas.id,
                name="Mediterranean Garden Veggie",
                description="Sun-dried tomatoes, kalamata olives, artichoke hearts, crumbled feta cheese, and spinach.",
                price=Decimal("13.99"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1593560708920-61dd98c46a4e?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_pizzas.id,
                name="Sweet Corn & Jalapeño Crunch",
                description="Charred golden sweet corn, spicy jalapeño coins, roasted red peppers, and cheddar.",
                price=Decimal("12.49"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1571407970349-bc81e7e96d47?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_pizzas.id,
                name="Rustic Pesto & Burrata Pizza",
                description="Genovese basil pesto base, cherry tomatoes, creamy burrata ball, and balsamic reduction.",
                price=Decimal("16.49"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1588315029754-2dd089d39a1a?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_pizzas.id,
                name="Spicy Mexican Fiesta Pizza",
                description="Black beans, fire-roasted salsa, jalapeños, sweet corn, cilantro, and chipotle crema.",
                price=Decimal("13.79"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1594007654729-407eedc4be65?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_pizzas.id,
                name="Caramelized Onion & Spinach White Pie",
                description="Garlic ricotta sauce, slow-caramelized sweet yellow onions, and wilted baby spinach.",
                price=Decimal("13.25"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1571997478779-2adcbbe9ab2f?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_pizzas.id,
                name="Smoky BBQ Jackfruit Pizza",
                description="Tender pulled jackfruit smothered in Texas hickory BBQ sauce, red onion, and cilantro.",
                price=Decimal("14.99"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1534308983496-4fabb1a015ee?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),

            # --- Non-Veg Pizzas ---
            MenuItem(
                category_id=cat_pizzas.id,
                name="Artisanal Pepperoni Feast",
                description="Triple layers of crispy cupped pepperoni, aged mozzarella, and zesty marinara sauce.",
                price=Decimal("15.99"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1628840042765-356cda07504e?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_pizzas.id,
                name="BBQ Smoked Chicken Pizza",
                description="Smoked pulled chicken breast, tangy BBQ sauce, red onions, bacon bits, and cilantro.",
                price=Decimal("15.49"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_pizzas.id,
                name="The Carnivore Meat Lover's",
                description="Italian fennel sausage, crispy bacon, pepperoni, seasoned ground beef, and mozzarella.",
                price=Decimal("17.49"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1541745537411-b8046dc6d66c?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_pizzas.id,
                name="Fiery Buffalo Chicken Pizza",
                description="Crispy tossed buffalo chicken, blue cheese crumbles, spicy cayenne ranch, and scallions.",
                price=Decimal("15.25"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1579751626657-72bc17010498?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_pizzas.id,
                name="Chicken Tikka Butter Masala Pizza",
                description="Tandoori chicken chunks bathed in rich makhani gravy with capsicum and mozzarella.",
                price=Decimal("16.29"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1585238342024-78d387f4a707?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_pizzas.id,
                name="Prosciutto & Baby Arugula Pizza",
                description="Dry-cured Italian prosciutto di Parma, wild baby arugula, shaved parmesan, and olive oil.",
                price=Decimal("17.99"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1528137871618-79d2761e3fd5?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_pizzas.id,
                name="Garlic Prawn & Herb Pizza",
                description="Sautéed butter garlic ocean shrimp, fresh oregano, chili flakes, and melted fontina cheese.",
                price=Decimal("18.49"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1564936281291-294551497d81?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_pizzas.id,
                name="Spicy Calabrian Sausage Pizza",
                description="Crumbled spicy Italian sausage, Calabrian chili paste, broccolini, and shaved pecorino.",
                price=Decimal("16.49"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_pizzas.id,
                name="Chicken Bacon Ranch Pizza",
                description="Herb grilled chicken, hardwood-smoked bacon crumbles, buttermilk ranch sauce, and mozzarella.",
                price=Decimal("15.75"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1506354666786-959d6d497f1a?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_pizzas.id,
                name="Hawaiian Sweet Ham & Pineapple",
                description="Honey-glazed ham slices, caramelized grilled pineapple chunks, and savory bacon bits.",
                price=Decimal("14.99"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),

            # Burgers & Sandwiches
            # --- Veg Burgers ---
            MenuItem(
                category_id=cat_burgers.id,
                name="Crispy Veggie Crunch Burger",
                description="Golden potato, pea, and corn patty with crisp lettuce, sliced tomatoes, and vegan garlic aioli.",
                price=Decimal("8.99"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1550547660-d9450f859349?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_burgers.id,
                name="Spicy Paneer Smash Burger",
                description="Crispy paneer steak spiced with peri-peri rub, pickled cucumbers, and spicy tandoori mayo.",
                price=Decimal("9.99"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1520072959219-c595dc870360?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_burgers.id,
                name="Black Bean & Quinoa Fiesta Burger",
                description="Hearty black bean and toasted quinoa patty topped with smashed avocado and jalapeño salsa.",
                price=Decimal("10.49"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1585238341710-4a87a746937e?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_burgers.id,
                name="Portobello Mushroom Melt",
                description="Balsamic marinated grilled portobello cap, melted swiss cheese, and caramelized onion jam.",
                price=Decimal("11.25"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1525059696034-4967a8e1dca2?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_burgers.id,
                name="Falafel Tahini Pita Pocket",
                description="Crispy golden chickpea falafels, Israeli salad, pickled turnips, and creamy sesame tahini.",
                price=Decimal("8.75"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_burgers.id,
                name="Gourmet Truffle Halloumi Burger",
                description="Pan-seared Cypriot halloumi cheese, wild rocket leaves, and black truffle mayonnaise.",
                price=Decimal("11.99"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_burgers.id,
                name="Bombay Masala Toast Sandwich",
                description="Spiced mashed potato filling, fresh cucumber, beet slices, and spicy green mint chutney.",
                price=Decimal("7.49"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_burgers.id,
                name="Four-Cheese Garlic Grilled Sandwich",
                description="Aged cheddar, gouda, mozzarella, and gruyère on sourdough bread toasted with garlic herb butter.",
                price=Decimal("8.99"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1528736235302-52922df5c122?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_burgers.id,
                name="Caprese Pesto Panini",
                description="Fresh buffalo mozzarella, ripe beefsteak tomatoes, sweet basil leaves, and basil pesto on ciabatta.",
                price=Decimal("9.49"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1509722747041-616f39b57569?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_burgers.id,
                name="Beetroot & Walnut Super Burger",
                description="Roasted beetroot and walnut patty, creamy goat cheese spread, and baby spinach on multigrain bun.",
                price=Decimal("10.75"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1550547660-d9450f859349?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),

            # --- Non-Veg Burgers ---
            MenuItem(
                category_id=cat_burgers.id,
                name="Classic Smashed Double Cheeseburger",
                description="Two crispy smashed beef patties, melted American cheddar, crinkle pickles, and secret shack sauce.",
                price=Decimal("11.99"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_burgers.id,
                name="Nashville Hot Crispy Chicken Burger",
                description="Buttermilk fried chicken breast drenched in cayenne hot oil, topped with sweet slaw and pickles.",
                price=Decimal("11.49"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1625813506062-0aeb1d7a094b?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_burgers.id,
                name="Smoky Bacon & BBQ Rodeo Burger",
                description="Angus beef patty, crispy applewood smoked bacon, beer-battered onion rings, and smoky BBQ sauce.",
                price=Decimal("13.49"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1553979459-d2229ba7433b?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_burgers.id,
                name="Truffle & Aged Cheddar Burger",
                description="Prime chuck beef patty, black truffle butter, 12-month aged white cheddar, and garlic aioli.",
                price=Decimal("14.99"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1586190848861-99aa4a171e90?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_burgers.id,
                name="Spicy Peri-Peri Grilled Chicken Burger",
                description="Flame-grilled chicken thigh marinated in bird's eye chilies, citrus, lettuce, and herb mayo.",
                price=Decimal("10.99"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_burgers.id,
                name="Slow-Smoked Pulled Pork Sandwich",
                description="14-hour hickory smoked pulled pork shoulder, Carolina mustard BBQ sauce, and apple cider coleslaw.",
                price=Decimal("12.49"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1603064752734-4c48eff53d05?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_burgers.id,
                name="Philly Cheesesteak Hoagie",
                description="Thinly shaved ribeye steak, sautéed peppers and onions, smothered in melted provolone cheese.",
                price=Decimal("12.99"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1549611016-3a70d82b5040?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_burgers.id,
                name="Texas Brisket Smash Melt",
                description="Chopped smoked beef brisket, pepper jack cheese, pickled jalapeños, toasted on Texas toast.",
                price=Decimal("13.99"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1521305916504-4a1121188589?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_burgers.id,
                name="Crispy Fish Fillet & Tartar Sandwich",
                description="Golden panko-crusted cod fillet, homemade caper tartar sauce, shredded lettuce on potato bun.",
                price=Decimal("10.75"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1550547660-d9450f859349?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_burgers.id,
                name="Classic Club Sandwich",
                description="Triple-decker toasted bread layered with smoked turkey, crispy bacon, cheddar, lettuce, and tomato.",
                price=Decimal("11.50"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),

            # Sides & Appetizers
            # --- Veg Sides ---
            MenuItem(
                category_id=cat_sides.id,
                name="Parmesan Truffle Fries",
                description="Crispy golden potato fries tossed in Italian white truffle oil, grated parmesan, and fresh parsley.",
                price=Decimal("5.99"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1576107232684-1279f3908594?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_sides.id,
                name="Crispy Mozzarella Sticks",
                description="Breaded melted mozzarella sticks served with a side of warm marinara dipping sauce.",
                price=Decimal("6.49"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1531749668029-2db88e4276c7?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_sides.id,
                name="Beer-Battered Onion Rings",
                description="Jumbo sweet yellow onion rings dipped in craft IPA batter, fried golden with chipotle dip.",
                price=Decimal("5.25"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1639024471287-032f667712d5?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_sides.id,
                name="Garlic Herb Sourdough Pull-Apart",
                description="Warm sourdough bread stuffed with roasted garlic butter, parsley, and stretchy mozzarella.",
                price=Decimal("6.75"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1573140247632-f8fd74997d5c?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_sides.id,
                name="Spicy Peri-Peri Waffle Fries",
                description="Cross-cut waffle potatoes seasoned with fiery African peri-peri spices, served with sour cream.",
                price=Decimal("5.49"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1541592106381-b31e9677c0e5?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_sides.id,
                name="Cheesy Jalapeño Poppers",
                description="Fresh jalapeño peppers stuffed with cream cheese and cheddar, breaded and fried to perfection.",
                price=Decimal("6.29"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1541745537411-b8046dc6d66c?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_sides.id,
                name="Sweet Potato Fries with Honey Mustard",
                description="Crispy caramelized sweet potato batons served with house Dijon honey mustard.",
                price=Decimal("5.75"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1585109649139-366815a0d713?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_sides.id,
                name="Fiesta Loaded Nachos",
                description="Stoneground corn tortilla chips baked with queso, black beans, jalapeños, pico de gallo, and guacamole.",
                price=Decimal("8.49"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1513456852971-30c0b8199d4d?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_sides.id,
                name="Tandoori Paneer Bites",
                description="Bite-sized roasted cottage cheese cubes marinated in yogurt, ginger, and fenugreek spices.",
                price=Decimal("7.25"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_sides.id,
                name="Crispy Mac & Cheese Balls",
                description="Deep-fried panko-crusted three-cheese macaroni balls served with warm marinara dip.",
                price=Decimal("6.99"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1543339308-43e59d6b73a6?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_sides.id,
                name="Mediterranean Hummus & Warm Pita",
                description="Silky smooth chickpea hummus with extra virgin olive oil, paprika, and warm toasted pita triangles.",
                price=Decimal("6.49"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_sides.id,
                name="Creamy Spinach & Artichoke Dip",
                description="Bubbling warm skillet of melted parmesan, cream cheese, baby spinach, served with corn chips.",
                price=Decimal("7.99"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1576107232684-1279f3908594?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),

            # --- Non-Veg Sides ---
            MenuItem(
                category_id=cat_sides.id,
                name="Buffalo Hot Wings (6 Pcs)",
                description="Crispy bone-in chicken wings tossed in tangy cayenne red pepper sauce, celery, and blue cheese dip.",
                price=Decimal("8.99"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1567620832903-9fc6debc209f?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_sides.id,
                name="Honey Garlic Glazed Wings (6 Pcs)",
                description="Crispy wings tossed in sticky roasted honey garlic glaze with toasted sesame seeds and scallions.",
                price=Decimal("8.99"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1527477378696-6d60c29fb916?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_sides.id,
                name="Crispy Buttermilk Chicken Tenders",
                description="Four large hand-breaded chicken breast tenderloins served with smoky honey mustard.",
                price=Decimal("7.99"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1562967914-608f82629710?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_sides.id,
                name="Chili Garlic Calamari",
                description="Flash-fried tender squid rings tossed with fresh red chilies, sea salt, and lemon garlic aioli.",
                price=Decimal("9.49"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_sides.id,
                name="Bacon & Cheddar Loaded Potato Skins",
                description="Crispy baked potato shells filled with sharp cheddar, smoked bacon bits, and sour cream.",
                price=Decimal("7.49"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1541592106381-b31e9677c0e5?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_sides.id,
                name="Crispy Coconut Butterfly Shrimp",
                description="Six jumbo ocean shrimp crusted with shredded sweet coconut, served with sweet chili dipping sauce.",
                price=Decimal("9.99"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1565680018434-b513d5e5fd47?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_sides.id,
                name="Smoky BBQ Pork Rib Tips",
                description="Slow-braised tender pork rib tips glazed with Kansas City brown sugar BBQ glaze.",
                price=Decimal("8.75"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1544025162-d76694265947?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_sides.id,
                name="Popcorn Chicken Crunch Bites",
                description="Bite-sized crispy spiced chicken nuggets served with spicy cajun dipping sauce.",
                price=Decimal("6.99"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1569058242252-623df46b5025?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),

            # Desserts & Beverages
            # --- Desserts & Drinks (Veg) ---
            MenuItem(
                category_id=cat_desserts.id,
                name="Warm Molten Chocolate Lava Cake",
                description="Rich Belgian dark chocolate cake with a warm flowing liquid fudge core, dusted with confectioners sugar.",
                price=Decimal("6.99"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_desserts.id,
                name="New York Classic Baked Cheesecake",
                description="Creamy Philadelphia cream cheese filling on a buttery graham cracker crust with strawberry coulis.",
                price=Decimal("6.49"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1533134242443-d4fd215305ad?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_desserts.id,
                name="Crispy Cinnamon Sugar Churros",
                description="Four crispy Spanish fried dough sticks rolled in cinnamon sugar, served with dulce de leche.",
                price=Decimal("5.75"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1624371414361-e670edf4898d?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_desserts.id,
                name="Classic Italian Tiramisu Cup",
                description="Espresso-soaked ladyfingers layered with whipped mascarpone cream and dusted with bitter cocoa.",
                price=Decimal("6.50"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_desserts.id,
                name="Fudgy Walnut Chocolate Brownie",
                description="Dense double chocolate brownie loaded with roasted walnuts, served warm with vanilla ice cream.",
                price=Decimal("5.25"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1589218436045-ee320057f443?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_desserts.id,
                name="Warm Red Velvet Skillet Cookie",
                description="Freshly baked red velvet cookie loaded with white chocolate chips, topped with cream cheese drizzle.",
                price=Decimal("6.25"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1587314168485-3236d6710814?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_desserts.id,
                name="Salted Caramel Apple Crumble",
                description="Tender caramelized spiced apples topped with golden buttery oat crumble and fleur de sel caramel.",
                price=Decimal("5.99"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1568571780765-9276ac8b75a2?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_desserts.id,
                name="Artisanal Belgian Waffle with Nutella",
                description="Crisp pearl sugar Belgian waffle smothered in warm Nutella and fresh banana slices.",
                price=Decimal("6.75"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1562376552-0d160a2f238d?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_desserts.id,
                name="Cold Brew Iced Coffee",
                description="20-hour slow steeped Colombian dark roast served over clear ice blocks with a dash of oat milk.",
                price=Decimal("4.50"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1517701604599-bb29b565090c?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_desserts.id,
                name="Fresh Strawberry Basil Lemonade",
                description="Crushed ripe strawberries, fresh lemon juice, muddled sweet basil, and effervescent sparkling water.",
                price=Decimal("4.25"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_desserts.id,
                name="Mango Alphonso Frappé",
                description="Blended real Alphonso mango pulp, chilled Greek yogurt, crushed ice, and a dash of cardamom.",
                price=Decimal("4.99"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1546173159-315724a31696?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_desserts.id,
                name="Oreo Overload Thick Milkshake",
                description="Creamy vanilla bean ice cream spun with whole Oreos, chocolate drizzle, and whipped cream.",
                price=Decimal("5.49"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_desserts.id,
                name="Matcha Green Tea Iced Latte",
                description="Ceremonial grade Japanese Uji matcha whisked with iced almond milk and pure agave nectar.",
                price=Decimal("4.75"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1536256263959-770b48d82b0a?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_desserts.id,
                name="Passionfruit Sparkling Iced Tea",
                description="Brewed Ceylon black tea infused with tropical passionfruit pulp, fresh mint leaves, and lime.",
                price=Decimal("3.99"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_desserts.id,
                name="Caramel Macchiato on Ice",
                description="Rich espresso shots poured over iced vanilla-infused milk, finished with butter caramel drizzle.",
                price=Decimal("4.75"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_desserts.id,
                name="Classic Root Beer Float",
                description="Old-fashioned handcrafted sarsaparilla root beer topped with a scoop of Madagascar vanilla gelato.",
                price=Decimal("4.50"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1551024709-8f23befc6f87?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_desserts.id,
                name="Dragonfruit Lychee Cooler",
                description="Chilled vibrant pink dragonfruit juice shaken with sweet lychee chunks and sparkling soda.",
                price=Decimal("4.49"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1534353473418-4cfa6c56fd38?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_desserts.id,
                name="Hot Spiced Masala Chai",
                description="Slow-brewed Assam CTC black tea simmered with fresh ginger, crushed green cardamom, and whole milk.",
                price=Decimal("3.25"),
                is_veg=True,
                image_url="https://images.unsplash.com/photo-1561336313-0bd5e0b27ec8?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),

            # --- Specialty Non-Veg Desserts (Contains Gelatin / Egg Custard) ---
            MenuItem(
                category_id=cat_desserts.id,
                name="Crème Brûlée with Madagascar Vanilla",
                description="Traditional rich egg-yolk custard base topped with a layer of hardened caramelized sugar crust.",
                price=Decimal("6.75"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1470124182917-cc6e71b22ecc?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
            MenuItem(
                category_id=cat_desserts.id,
                name="Silky Mango Panna Cotta",
                description="Chilled Italian sweetened cream set with gelatin, topped with fresh alphonso mango coulis.",
                price=Decimal("6.25"),
                is_veg=False,
                image_url="https://images.unsplash.com/photo-1488477181946-6428a0291777?w=600&auto=format&fit=crop&q=80",
                is_available=True
            ),
        ]

        db.add_all(dishes)
        db.commit()
        print(f"🎉 Success! Database wiped and reseeded with {len(dishes)} dishes across 4 categories!")

    except Exception as err:
        db.rollback()
        print(f"❌ Seeding transaction failed: {err}")
    finally:
        db.close()


if __name__ == "__main__":
    reset_and_seed()