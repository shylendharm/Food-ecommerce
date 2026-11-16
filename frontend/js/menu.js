/* =============================================================
   MENU & STOREFRONT CONTROLLER (frontend/js/menu.js)
   Fetches dishes from FastAPI, renders category tabs, and filters food.
   ============================================================= */

// Active filter state
let selectedCategoryId = "";
let isVegOnly = false;

// In-memory cache of currently displayed dishes
let currentDishes = [];


/* =============================================================
   1. LOAD & RENDER CATEGORIES
   ============================================================= */

/**
 * Fetches all categories from the backend and builds the tab buttons
 */
async function loadCategories() {
    const tabsContainer = document.getElementById("category-tabs");
    if (!tabsContainer) return;

    try {
        const categories = await getCategories();

        // Start with the default "All Items" tab
        let tabsHTML = `
      <button class="tab-btn active" data-category-id="">All Items</button>
    `;

        // Add a tab button for each category from MySQL (Pizzas, Burgers, etc.)
        categories.forEach(cat => {
            tabsHTML += `
        <button class="tab-btn" data-category-id="${cat.id}">${cat.name}</button>
      `;
        });

        tabsContainer.innerHTML = tabsHTML;

        // Attach click events to all category tabs
        const buttons = tabsContainer.querySelectorAll(".tab-btn");
        buttons.forEach(btn => {
            btn.addEventListener("click", () => {
                // Remove 'active' class from all tabs, add it to the clicked one
                buttons.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");

                // Update the active category and refresh the menu dishes
                selectedCategoryId = btn.getAttribute("data-category-id");
                loadMenu();
            });
        });

    } catch (error) {
        console.error("Failed to load categories:", error);
    }
}


/* =============================================================
   2. LOAD & RENDER MENU ITEMS
   ============================================================= */

/**
 * Fetches dishes matching the current filters and paints the food cards
 */
async function loadMenu() {
    const grid = document.getElementById("menu-grid");
    const countLabel = document.getElementById("items-count-label");
    const titleLabel = document.getElementById("current-category-title");

    if (!grid) return;

    // Show loading spinner/message while waiting for backend
    grid.innerHTML = `
    <div class="loading-state">
      <p>Fetching fresh dishes from kitchen...</p>
    </div>
  `;

    try {
        // 1. Call our FastAPI backend via api.js
        const dishes = await getMenuItems(selectedCategoryId, isVegOnly);
        currentDishes = dishes; // Save in memory

        // 2. Update item count label
        if (countLabel) {
            countLabel.textContent = `${dishes.length} ${dishes.length === 1 ? 'item' : 'items'} found`;
        }

        // 3. Update section title
        if (titleLabel) {
            const activeBtn = document.querySelector(".tab-btn.active");
            titleLabel.textContent = activeBtn ? activeBtn.textContent : "Our Menu";
        }

        // 4. If no dishes match the filter (e.g. no veg burgers found)
        if (dishes.length === 0) {
            grid.innerHTML = `
        <div class="loading-state">
          <p>No dishes found matching your selection.</p>
          <small>Try turning off the Veg Only filter or pick another category.</small>
        </div>
      `;
            return;
        }

        // 5. Paint the food cards into the grid!
        grid.innerHTML = dishes.map(dish => {
            const priceFormatted = `$${parseFloat(dish.price).toFixed(2)}`;
            const vegClass = dish.is_veg ? "veg" : "non-veg";
            const vegText = dish.is_veg ? "🌿 Veg" : "🍗 Non-Veg";

            return `
        <div class="food-card">
          <div class="card-img-wrapper">
            <img class="card-img" src="${dish.image_url}" alt="${dish.name}" loading="lazy">
            <span class="veg-badge ${vegClass}">${vegText}</span>
          </div>

          <div class="card-body">
            <h3 class="dish-name">${dish.name}</h3>
            <p class="dish-desc">${dish.description || 'Made fresh to order with authentic ingredients.'}</p>

            <div class="card-footer">
              <span class="dish-price">${priceFormatted}</span>
              <button class="add-btn" onclick="handleAddToCart(${dish.id})">Add to Cart</button>
            </div>
          </div>
        </div>
      `;
        }).join("");

    } catch (error) {
        grid.innerHTML = `
      <div class="loading-state">
        <p style="color: #E23744;">⚠️ Unable to connect to the backend server.</p>
        <small>Make sure Uvicorn is running on http://localhost:8000</small>
      </div>
    `;
        console.error("Failed to load menu items:", error);
    }
}


/* =============================================================
   3. BRIDGE TO CART.JS
   ============================================================= */

/**
 * Called when a customer clicks the "Add to Cart" button on any card
 */
function handleAddToCart(dishId) {
    // Find the complete dish object from our memory
    const dish = currentDishes.find(d => d.id === dishId);
    if (dish) {
        // Call the addToCart function we wrote in cart.js!
        addToCart(dish);
    }
}


/* =============================================================
   4. PAGE INITIALIZATION & FILTER EVENT LISTENERS
   ============================================================= */
document.addEventListener("DOMContentLoaded", () => {
    // 1. Initial load of categories and dishes
    loadCategories();
    loadMenu();

    // 2. Wire up the "Veg Only" toggle switch
    const vegCheckbox = document.getElementById("veg-only-checkbox");
    if (vegCheckbox) {
        vegCheckbox.addEventListener("change", (e) => {
            isVegOnly = e.target.checked; // true when checked, false when unchecked
            loadMenu();                   // Re-fetch dishes with the new filter!
        });
    }
});