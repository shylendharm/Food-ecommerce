/* =============================================================
   MENU & STOREFRONT CONTROLLER (frontend/js/menu.js)
   Fetches dishes from FastAPI, powers real-time in-memory search,
   and implements self-healing resilient food image fallbacks.
   ============================================================= */

// Active filter state
let selectedCategoryId = "";
let isVegOnly = false;
let currentSearchQuery = "";

// In-memory cache of dishes fetched from backend for active filters
let currentDishes = [];

// High-speed CDN category-aware image fallbacks
const CATEGORY_FALLBACK_IMAGES = {
  1: "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600&auto=format&fit=crop&q=80", // Pizzas
  2: "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&auto=format&fit=crop&q=80", // Burgers
  3: "https://images.unsplash.com/photo-1576107232684-1279f3908594?w=600&auto=format&fit=crop&q=80", // Sides
  4: "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=600&auto=format&fit=crop&q=80", // Desserts & Drinks
  default: "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600&auto=format&fit=crop&q=80"
};

/**
 * Self-healing image error handler:
 * Instantly replaces a broken/throttled image with the category fallback.
 */
window.handleDishImageError = function (imgElement, categoryId) {
  imgElement.onerror = null; // Prevents recursive loop if fallback fails
  const fallbackUrl = CATEGORY_FALLBACK_IMAGES[categoryId] || CATEGORY_FALLBACK_IMAGES.default;
  imgElement.src = fallbackUrl;
};

/**
 * Validates and returns a verified image URL string
 */
function getDishImageUrl(dish) {
  if (dish.image_url && dish.image_url.trim().startsWith("http")) {
    return dish.image_url.trim();
  }
  return CATEGORY_FALLBACK_IMAGES[dish.category_id] || CATEGORY_FALLBACK_IMAGES.default;
}


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

    // Default "All Items" tab
    let tabsHTML = `
            <button class="tab-btn active" data-category-id="">All Items</button>
        `;

    // Tab button for each category from MySQL
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
        buttons.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");

        // Update active category and refresh menu
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
 * Fetches dishes matching category and veg filters from the backend
 */
async function loadMenu() {
  const grid = document.getElementById("menu-grid");
  const titleLabel = document.getElementById("current-category-title");

  if (!grid) return;

  // Show loading spinner while waiting for FastAPI/Redis
  grid.innerHTML = `
        <div class="loading-state">
            <p>Fetching fresh dishes from kitchen...</p>
        </div>
    `;

  try {
    // Fetch dishes from our cached backend endpoint
    const dishes = await getMenuItems(selectedCategoryId, isVegOnly);
    currentDishes = dishes; // Save in-memory for instant keystroke search

    // Update section title based on active category
    if (titleLabel) {
      const activeBtn = document.querySelector(".tab-btn.active");
      titleLabel.textContent = activeBtn ? activeBtn.textContent : "Our Menu";
    }

    // Apply any active search filter to the newly loaded dishes
    applyDishSearchAndRender();

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
   3. REAL-TIME SEARCH FILTER ENGINE & RESILIENT DOM RENDERER
   ============================================================= */

/**
 * Filters in-memory dishes array against currentSearchQuery and paints cards
 */
function applyDishSearchAndRender() {
  const grid = document.getElementById("menu-grid");
  const countLabel = document.getElementById("items-count-label");
  if (!grid) return;

  const query = currentSearchQuery.trim().toLowerCase();

  // In-memory filter across dish name and description
  const filteredDishes = currentDishes.filter(dish => {
    if (!query) return true;
    const nameMatch = dish.name.toLowerCase().includes(query);
    const descMatch = (dish.description || "").toLowerCase().includes(query);
    return nameMatch || descMatch;
  });

  // Update items count label
  if (countLabel) {
    if (query) {
      countLabel.textContent = `${filteredDishes.length} ${filteredDishes.length === 1 ? 'dish' : 'dishes'} found for "${query}"`;
    } else {
      countLabel.textContent = `${filteredDishes.length} ${filteredDishes.length === 1 ? 'item' : 'items'} found`;
    }
  }

  // 1. Empty state if search yields no results
  if (filteredDishes.length === 0) {
    if (query) {
      grid.innerHTML = `
                <div class="loading-state">
                    <span style="font-size: 2.2rem; display: block; margin-bottom: 8px;">🔍</span>
                    <p>No dishes match "<strong>${escapeHtml(query)}</strong>"</p>
                    <small>Try searching with another keyword or clear the search box.</small>
                </div>
            `;
    } else {
      grid.innerHTML = `
                <div class="loading-state">
                    <p>No dishes found matching your selection.</p>
                    <small>Try turning off the Veg Only filter or pick another category.</small>
                </div>
            `;
    }
    return;
  }

  // 2. Render food cards with lazy-loading and self-healing image handlers
  grid.innerHTML = filteredDishes.map(dish => {
    const priceFormatted = `$${parseFloat(dish.price).toFixed(2)}`;
    const vegClass = dish.is_veg ? "veg" : "non-veg";
    const vegText = dish.is_veg ? "🌿 Veg" : "🍗 Non-Veg";
    const imageUrl = getDishImageUrl(dish);

    return `
            <div class="food-card">
                <div class="card-img-wrapper">
                    <img 
                        class="card-img" 
                        src="${imageUrl}" 
                        alt="${escapeHtml(dish.name)}" 
                        loading="lazy"
                        onerror="handleDishImageError(this, ${dish.category_id})"
                    />
                    <span class="veg-badge ${vegClass}">${vegText}</span>
                </div>

                <div class="card-body">
                    <h3 class="dish-name">${escapeHtml(dish.name)}</h3>
                    <p class="dish-desc">${escapeHtml(dish.description || 'Made fresh to order with authentic ingredients.')}</p>

                    <div class="card-footer">
                        <span class="dish-price">${priceFormatted}</span>
                        <button class="add-btn" onclick="handleAddToCart(${dish.id})">Add to Cart</button>
                    </div>
                </div>
            </div>
        `;
  }).join("");
}

// XSS Sanitizer for safe string reflection
function escapeHtml(string) {
  if (!string) return "";
  const div = document.createElement("div");
  div.innerText = string;
  return div.innerHTML;
}


/* =============================================================
   4. BRIDGE TO CART.JS
   ============================================================= */

function handleAddToCart(dishId) {
  const dish = currentDishes.find(d => d.id === dishId);
  if (dish) {
    addToCart(dish);
  }
}


/* =============================================================
   5. PAGE INITIALIZATION & EVENT LISTENERS
   ============================================================= */
document.addEventListener("DOMContentLoaded", () => {
  // 1. Initial load of categories and dishes
  loadCategories();
  loadMenu();

  // 2. Wire up the "Veg Only" toggle switch
  const vegCheckbox = document.getElementById("veg-only-checkbox");
  if (vegCheckbox) {
    vegCheckbox.addEventListener("change", (e) => {
      isVegOnly = e.target.checked;
      loadMenu();
    });
  }

  // 3. Real-Time Dish Search Input Listener (0ms latency keystroke filtering)
  const searchInput = document.getElementById("dish-search-input");
  const clearBtn = document.getElementById("clear-search-btn");

  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      currentSearchQuery = e.target.value;

      if (clearBtn) {
        if (currentSearchQuery.length > 0) {
          clearBtn.classList.remove("hidden");
        } else {
          clearBtn.classList.add("hidden");
        }
      }

      applyDishSearchAndRender();
    });

    searchInput.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        searchInput.value = "";
        currentSearchQuery = "";
        clearBtn?.classList.add("hidden");
        applyDishSearchAndRender();
      }
    });
  }

  // 4. Clear Search Button Click Listener (×)
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      if (searchInput) {
        searchInput.value = "";
        searchInput.focus();
      }
      currentSearchQuery = "";
      clearBtn.classList.add("hidden");
      applyDishSearchAndRender();
    });
  }
});