/* =============================================================
   FILE: frontend/js/cart.js
   SHOPPING CART STATE & DRAWER CONTROLLER
   Manages cart items in localStorage, calculations, drawer animations,
   and clean checkout navigation routing.
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
        return saved ? JSON.parse(saved) : [];
    } catch (e) {
        console.error("[Cart] Failed to parse cart from localStorage:", e);
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
   2. CORE CART ACTIONS (Add, Increase, Decrease, Remove, Clear)
   ============================================================= */

/**
 * Adds a dish to the shopping cart
 * If already in cart, increases its quantity by 1
 */
function addToCart(dish) {
    const existingItem = cart.find(item => item.id === dish.id);

    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({
            id: dish.id,
            name: dish.name,
            price: parseFloat(dish.price),
            image_url: dish.image_url,
            is_veg: dish.is_veg,
            quantity: 1
        });
    }

    saveCartToStorage();
    updateCartUI();
    openCartDrawer();
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
    cart = cart.filter(item => item.id !== dishId);
    saveCartToStorage();
    updateCartUI();
}

/**
 * Clears all items from the cart
 */
function clearCart() {
    cart = [];
    saveCartToStorage();
    updateCartUI();
}


/* =============================================================
   3. UI RENDERING & PRICE CALCULATIONS
   ============================================================= */

/**
 * Re-calculates totals and updates badge counter, drawer list, and subtotal
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

    // If the cart is empty, show the clean empty state
    if (cart.length === 0) {
        container.innerHTML = `
            <div class="empty-cart-state">
                <p>Your cart is empty.</p>
                <small>Add some tasty dishes from the menu to get started.</small>
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
   5. CHECKOUT ROUTING (Zero Modal Popups)
   ============================================================= */

/**
 * Handles the "Proceed to Checkout" action:
 * 1. Blocks action if cart is empty.
 * 2. If unauthenticated, sets return redirect and navigates cleanly to login.html.
 * 3. If authenticated, allows default navigation to checkout.html.
 */
function handleProceedToCheckout(e) {
    if (!cart || cart.length === 0) {
        e.preventDefault();
        alert("Your cart is empty. Please add items from the menu first.");
        return;
    }

    if (typeof isAuthenticated === "function" && !isAuthenticated()) {
        e.preventDefault();
        sessionStorage.setItem("post_login_redirect", "checkout.html");
        window.location.href = "login.html";
        return;
    }
}


/* =============================================================
   6. EVENT LISTENERS INITIALIZATION
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

    // 4. Clicking the dark backdrop outside the cart closes it
    const backdrop = document.getElementById("cart-backdrop");
    if (backdrop) {
        backdrop.addEventListener("click", closeCartDrawer);
    }

    // 5. Intercept Proceed to Checkout
    const checkoutBtn = document.getElementById("proceed-checkout-btn");
    if (checkoutBtn) {
        checkoutBtn.addEventListener("click", handleProceedToCheckout);
    }
});