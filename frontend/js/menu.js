// Storefront menu listing, search filters, and categories

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
  imgElement.onerror = null;
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

/**
 * Reads quantity of a given dish currently in the cart
 */
function getCartItemQuantity(dishId) {
  if (typeof cart !== "undefined" && Array.isArray(cart)) {
    const item = cart.find(i => i.id === dishId);
    return item ? item.quantity : 0;
  }
  return 0;
}

/**
 * Deterministic rating generator (e.g. 4.8, 4.9) for authentic menu appearance
 */
function getDishRating(dishId) {
  const ratings = ["4.8", "4.9", "4.7", "4.8", "4.9"];
  return ratings[dishId % ratings.length];
}

/**
 * Dynamic kitchen prep time generator
 */
function getDishPrepTime(dishId) {
  const times = ["20-25 min", "25-30 min", "15-20 min", "20-30 min"];
  return times[dishId % times.length];
}


// Categories

async function loadCategories() {
  const tabsContainer = document.getElementById("category-tabs");
  if (!tabsContainer) return;

  try {
    const categories = await getCategories();

    let tabsHTML = `
      <button class="tab-btn active" data-category-id="">All Items</button>
    `;

    categories.forEach(cat => {
      tabsHTML += `
        <button class="tab-btn" data-category-id="${cat.id}">${cat.name}</button>
      `;
    });

    tabsContainer.innerHTML = tabsHTML;

    const buttons = tabsContainer.querySelectorAll(".tab-btn");
    buttons.forEach(btn => {
      btn.addEventListener("click", () => {
        buttons.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");

        selectedCategoryId = btn.getAttribute("data-category-id");
        loadMenu();
      });
    });

  } catch (error) {
    console.error("Failed to load categories:", error);
  }
}


// Menu items

async function loadMenu() {
  const grid = document.getElementById("menu-grid");
  const titleLabel = document.getElementById("current-category-title");

  if (!grid) return;

  grid.innerHTML = `
    <div class="loading-state">
      <p>Fetching fresh dishes from kitchen...</p>
    </div>
  `;

  try {
    const dishes = await getMenuItems(selectedCategoryId, isVegOnly);
    currentDishes = dishes;

    if (titleLabel) {
      const activeBtn = document.querySelector(".tab-btn.active");
      titleLabel.textContent = activeBtn ? activeBtn.textContent : "Our Menu";
    }

    applyDishSearchAndRender();

  } catch (error) {
    grid.innerHTML = `
      <div class="loading-state">
        <p style="color: #E11D48; font-weight: 700;">Unable to connect to the backend server.</p>
        <small>Make sure Uvicorn is running on http://127.0.0.1:8000</small>
      </div>
    `;
    console.error("Failed to load menu items:", error);
  }
}


// Search and filtering

/**
 * Generates the HTML for a dish card action: either [+ Add] or [ - qty + ]
 */
function renderCardActionButton(dishId, qty) {
  if (qty > 0) {
    return `
      <div class="card-stepper" id="card-stepper-${dishId}">
        <button class="card-stepper-btn" onclick="handleCardQtyChange(event, ${dishId}, -1)" aria-label="Decrease quantity">−</button>
        <span class="card-stepper-qty">${qty}</span>
        <button class="card-stepper-btn" onclick="handleCardQtyChange(event, ${dishId}, 1)" aria-label="Increase quantity">+</button>
      </div>
    `;
  }
  return `<button class="add-btn" onclick="handleAddToCart(event, ${dishId})">+ Add</button>`;
}

/**
 * Filters in-memory dishes array against currentSearchQuery and paints cards
 */
function applyDishSearchAndRender() {
  const grid = document.getElementById("menu-grid");
  const countLabel = document.getElementById("items-count-label");
  if (!grid) return;

  const query = currentSearchQuery.trim().toLowerCase();

  const filteredDishes = currentDishes.filter(dish => {
    if (!query) return true;
    const nameMatch = dish.name.toLowerCase().includes(query);
    const descMatch = (dish.description || "").toLowerCase().includes(query);
    return nameMatch || descMatch;
  });

  if (countLabel) {
    if (query) {
      countLabel.textContent = `${filteredDishes.length} ${filteredDishes.length === 1 ? 'dish' : 'dishes'} found for "${query}"`;
    } else {
      countLabel.textContent = `${filteredDishes.length} ${filteredDishes.length === 1 ? 'item' : 'items'} available`;
    }
  }

  if (filteredDishes.length === 0) {
    if (query) {
      grid.innerHTML = `
        <div class="loading-state">
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

  // Render Modern Minimalist Food Cards
  grid.innerHTML = filteredDishes.map(dish => {
    const priceFormatted = `$${parseFloat(dish.price).toFixed(2)}`;
    const vegClass = dish.is_veg ? "veg" : "non-veg";
    const vegLabel = dish.is_veg ? "Veg" : "Non-Veg";
    const imageUrl = getDishImageUrl(dish);
    const qty = getCartItemQuantity(dish.id);
    const rating = getDishRating(dish.id);
    const prepTime = getDishPrepTime(dish.id);

    return `
      <div class="food-card" data-dish-id="${dish.id}">
        <div class="card-img-wrapper">
          <img 
            class="card-img" 
            src="${imageUrl}" 
            alt="${escapeHtml(dish.name)}" 
            loading="lazy"
            onerror="handleDishImageError(this, ${dish.category_id})"
          />
          <div class="diet-indicator ${vegClass}">
            <span class="diet-dot"></span>
            <span>${vegLabel}</span>
          </div>
        </div>

        <div class="card-body">
          <div class="card-meta-row">
            <span class="card-rating"><span>★</span> ${rating}</span>
            <span>•</span>
            <span>${prepTime}</span>
          </div>

          <h3 class="dish-name">${escapeHtml(dish.name)}</h3>
          <p class="dish-desc">${escapeHtml(dish.description || 'Made fresh to order with authentic ingredients.')}</p>

          <div class="card-footer">
            <span class="dish-price">${priceFormatted}</span>
            <div id="card-action-${dish.id}">
              ${renderCardActionButton(dish.id, qty)}
            </div>
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


// Quantity steppers

function handleAddToCart(e, dishId) {
  if (e) e.stopPropagation();
  const dish = currentDishes.find(d => d.id === dishId);
  if (dish) {
    addToCart(dish);
    syncMenuCardSteppers();
  }
}

function handleCardQtyChange(e, dishId, change) {
  if (e) e.stopPropagation();
  updateQuantity(dishId, change);
  syncMenuCardSteppers();
}

/**
 * Synchronizes visible card action containers with the current cart state
 * without rebuilding cards or triggering image re-renders!
 */
window.syncMenuCardSteppers = function () {
  currentDishes.forEach(dish => {
    const actionContainer = document.getElementById(`card-action-${dish.id}`);
    if (actionContainer) {
      const qty = getCartItemQuantity(dish.id);
      actionContainer.innerHTML = renderCardActionButton(dish.id, qty);
    }
  });
};

// Two-way synchronization: If cart drawer modifies items, immediately update card steppers!
if (typeof window.updateCartUI === "function") {
  const originalUpdateCartUI = window.updateCartUI;
  window.updateCartUI = function () {
    originalUpdateCartUI();
    if (typeof window.syncMenuCardSteppers === "function") {
      window.syncMenuCardSteppers();
    }
  };
}


// Page initialization
document.addEventListener("DOMContentLoaded", () => {
  loadCategories();
  loadMenu();

  const vegCheckbox = document.getElementById("veg-only-checkbox");
  if (vegCheckbox) {
    vegCheckbox.addEventListener("change", (e) => {
      isVegOnly = e.target.checked;
      loadMenu();
    });
  }

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