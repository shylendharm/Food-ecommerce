/* =============================================================
   SHOPPING CART STATE & DRAWER CONTROLLER (frontend/js/cart.js)
   Manages cart items in localStorage, calculations, and the sliding drawer.
   ============================================================= */

// Key name used to store cart data inside the browser's localStorage
const CART_STORAGE_KEY = "foodexpress_cart";

// Load existing cart items from the browser's disk, or start with an empty array []
let cart = loadCartFromStorage();


/* =============================================================
   1. LOCAL STORAGE SYNC FUNCTIONS
   ============================================================= */

/**
 * Reads the saved cart from localStorage on page load
 */
function loadCartFromStorage() {
    try {
        const saved = localStorage.getItem(CART_STORAGE_KEY);
        // If saved cart exists, parse it back to a JavaScript array; otherwise return []
        return saved ? JSON.parse(saved) : [];
    } catch (e) {
        console.error("Failed to parse cart from localStorage:", e);
        return [];
    }
}

/**
 * Saves the current cart array to localStorage so it survives page reloads
 */
function saveCartToStorage() {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));
}


/* =============================================================
   2. CORE CART ACTIONS (Add, Increase, Decrease, Remove)
   ============================================================= */

/**
 * Adds a dish to the shopping cart
 * If already in cart, increases its quantity by 1
 */
function addToCart(dish) {
    // Check if this dish is already in the cart
    const existingItem = cart.find(item => item.id === dish.id);

    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        // Add brand new item snapshot to cart
        cart.push({
            id: dish.id,
            name: dish.name,
            price: parseFloat(dish.price), // Convert string/decimal to a number
            image_url: dish.image_url,
            is_veg: dish.is_veg,
            quantity: 1
        });
    }

    saveCartToStorage();
    updateCartUI();
    openCartDrawer(); // Automatically slide the cart open so the user sees it!
}

/**
 * Changes item quantity (+1 or -1)
 */
function updateQuantity(dishId, change) {
    const item = cart.find(item => item.id === dishId);
    if (!item) return;

    item.quantity += change;

    // If quantity drops to 0 or below, remove the dish from the cart
    if (item.quantity <= 0) {
        removeFromCart(dishId);
        return;
    }

    saveCartToStorage();
    updateCartUI();
}

/**
 * Completely removes a dish from the cart
 */
function removeFromCart(dishId) {
    // filter() keeps every item EXCEPT the one matching this ID
    cart = cart.filter(item => item.id !== dishId);
    saveCartToStorage();
    updateCartUI();
}


/* =============================================================
   3. UI RENDERING & PRICE CALCULATIONS
   ============================================================= */

/**
 * Re-calculates totals and updates the screen (badge counter, drawer list, total price)
 */
function updateCartUI() {
    // 1. Calculate total number of items for the badge counter
    const totalItemCount = cart.reduce((sum, item) => sum + item.quantity, 0);
    const badgeElement = document.getElementById("cart-count-badge");
    if (badgeElement) {
        badgeElement.textContent = totalItemCount;
    }

    // 2. Calculate financial subtotal
    const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const formattedSubtotal = `$${subtotal.toFixed(2)}`;

    // Update total prices displayed in the cart drawer
    const subtotalEl = document.getElementById("cart-subtotal");
    const totalEl = document.getElementById("cart-total");
    const btnTotalEl = document.getElementById("btn-total-amount");

    if (subtotalEl) subtotalEl.textContent = formattedSubtotal;
    if (totalEl) totalEl.textContent = formattedSubtotal;
    if (btnTotalEl) btnTotalEl.textContent = formattedSubtotal;

    // 3. Render the list of food items inside the drawer
    const container = document.getElementById("cart-items-container");
    if (!container) return;

    // If the cart is empty, show the friendly empty state
    if (cart.length === 0) {
        container.innerHTML = `
      <div class="empty-cart-state">
        <span class="empty-icon">🍽️</span>
        <p>Your cart is empty.</p>
        <small>Add some tasty dishes from the menu!</small>
      </div>
    `;
        return;
    }

    // Build the HTML rows for each food item
    container.innerHTML = cart.map(item => `
    <div class="cart-item-row">
      <div class="item-info">
        <h4>${item.name}</h4>
        <span>$${item.price.toFixed(2)} each</span>
      </div>
      <div class="qty-controls">
        <button class="qty-btn" onclick="updateQuantity(${item.id}, -1)" aria-label="Decrease quantity">−</button>
        <span class="qty-number">${item.quantity}</span>
        <button class="qty-btn" onclick="updateQuantity(${item.id}, 1)" aria-label="Increase quantity">+</button>
      </div>
    </div>
  `).join("");
}


/* =============================================================
   4. DRAWER SLIDE ANIMATIONS (Open / Close)
   ============================================================= */

function openCartDrawer() {
    const drawer = document.getElementById("cart-drawer");
    const backdrop = document.getElementById("cart-backdrop");

    if (drawer && backdrop) {
        // Swapping CSS classes triggers our smooth 0.35s CSS transition!
        drawer.classList.remove("closed");
        drawer.classList.add("open");
        backdrop.classList.remove("hidden");
    }
}

function closeCartDrawer() {
    const drawer = document.getElementById("cart-drawer");
    const backdrop = document.getElementById("cart-backdrop");

    if (drawer && backdrop) {
        drawer.classList.remove("open");
        drawer.classList.add("closed");
        backdrop.classList.add("hidden");
    }
}


/* =============================================================
   5. WIRE UP BUTTON EVENT LISTENERS ON PAGE LOAD
   ============================================================= */
document.addEventListener("DOMContentLoaded", () => {
    // 1. Initial render of cart from localStorage
    updateCartUI();

    // 2. Open cart button in navbar
    const openBtn = document.getElementById("cart-toggle-btn");
    if (openBtn) {
        openBtn.addEventListener("click", openCartDrawer);
    }

    // 3. Close cart button (the 'X')
    const closeBtn = document.getElementById("close-cart-btn");
    if (closeBtn) {
        closeBtn.addEventListener("click", closeCartDrawer);
    }

    // 4. Clicking the dark backdrop outside the cart closes it too
    const backdrop = document.getElementById("cart-backdrop");
    if (backdrop) {
        backdrop.addEventListener("click", closeCartDrawer);
    }
});
