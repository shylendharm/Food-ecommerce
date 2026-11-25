// Shopping cart state, local persistence, and drawer UI

/**
 * Computes an isolated storage key scoped to the authenticated customer.
 * - Authenticated Customer (ID: 12): "foodexpress_cart_user_12"
 * - Guest visitor: "foodexpress_cart_guest"
 * Completely isolates cart contents between accounts on the same computer.
 */
function getCartStorageKey() {
    if (typeof getStoredUser === "function") {
        const user = getStoredUser();
        if (user && user.id) {
            return `foodexpress_cart_user_${user.id}`;
        }
    }
    return "foodexpress_cart_guest";
}

// Load user-scoped cart items on script execution
let cart = loadCartFromStorage();


// Cart persistence and storage sync

/**
 * Reads the saved cart from localStorage scoped to the active user.
 * Auto-sanitizes any malformed or legacy NaN entries.
 */
function loadCartFromStorage() {
    try {
        const key = getCartStorageKey();
        const saved = localStorage.getItem(key);
        let items = [];

        if (saved) {
            items = JSON.parse(saved);
        } else if (key !== "foodexpress_cart_guest") {
            const guestCart = localStorage.getItem("foodexpress_cart_guest");
            if (guestCart) {
                localStorage.removeItem("foodexpress_cart_guest");
                localStorage.setItem(key, guestCart);
                items = JSON.parse(guestCart);
            }
        }

        // Clean up legacy global key if present from older versions
        localStorage.removeItem("foodexpress_cart");

        if (!Array.isArray(items)) return [];

        // Self-Healing Filter: Remove corrupt, NaN, or improperly typed items
        return items.filter(item => {
            if (!item || typeof item !== "object") return false;

            // Normalize ID if stored as an object
            if (typeof item.id === "object" && item.id !== null && item.id.id) {
                item.id = item.id.id;
            }

            item.id = parseInt(item.id, 10);
            item.price = parseFloat(item.price);
            item.quantity = parseInt(item.quantity, 10);

            return !isNaN(item.id) && !isNaN(item.price) && !isNaN(item.quantity) && item.quantity > 0;
        });
    } catch (e) {
        console.error("[Cart] Failed to parse cart from localStorage:", e);
        return [];
    }
}

/**
 * Saves the current cart array to user-partitioned localStorage
 */
function saveCartToStorage() {
    const key = getCartStorageKey();
    localStorage.setItem(key, JSON.stringify(cart));
}


// Cart mutations (add, update, remove)

/**
 * Adds a dish to the active user's cart.
 * Supports both polymorphic calls:
 * - addToCart(dishObject)
 * - addToCart(dishId, name, price, imageUrl)
 */
function addToCart(dishOrId, name, price, imageUrl) {
    let dishId, dishName, dishPrice, dishImage, isVeg;

    // Polymorphic Parameter Extraction
    if (typeof dishOrId === "object" && dishOrId !== null) {
        dishId = parseInt(dishOrId.id, 10);
        dishName = dishOrId.name || "Delicious Dish";
        dishPrice = parseFloat(dishOrId.price);
        dishImage = dishOrId.image_url || dishOrId.imageUrl || "assets/hero-bg.jpg";
        isVeg = Boolean(dishOrId.is_veg);
    } else {
        dishId = parseInt(dishOrId, 10);
        dishName = name || "Delicious Dish";
        dishPrice = parseFloat(price);
        dishImage = imageUrl || "assets/hero-bg.jpg";
        isVeg = false;
    }

    // Fallback if price is missing or invalid
    if (isNaN(dishPrice)) {
        console.error("[Cart] Invalid price received for dish:", dishOrId, price);
        dishPrice = 0;
    }

    const existing = cart.find(item => item.id === dishId);

    if (existing) {
        existing.quantity += 1;
    } else {
        cart.push({
            id: dishId,
            name: dishName,
            price: dishPrice,
            image_url: dishImage,
            imageUrl: dishImage,
            is_veg: isVeg,
            quantity: 1
        });
    }

    saveCartToStorage();
    updateCartUI();
    animateNavbarCartBadge();
}

/**
 * Changes item quantity (+1 or -1)
 */
function updateQuantity(dishId, change) {
    const targetId = parseInt(dishId, 10);
    const item = cart.find(item => item.id === targetId);
    if (!item) return;

    item.quantity += change;

    // If quantity drops to 0 or below, remove the dish from the cart
    if (item.quantity <= 0) {
        removeFromCart(targetId);
        return;
    }

    saveCartToStorage();
    updateCartUI();
    animateNavbarCartBadge();
}

/**
 * Completely removes a dish from the cart
 */
function removeFromCart(dishId) {
    const targetId = parseInt(dishId, 10);
    cart = cart.filter(item => item.id !== targetId);
    saveCartToStorage();
    updateCartUI();
    animateNavbarCartBadge();
}

/**
 * Clears all items from the active user's cart
 */
function clearCart() {
    cart = [];
    saveCartToStorage();
    updateCartUI();
}


// Render cart items and totals

/**
 * Re-calculates totals and updates badge counter, drawer list, and subtotal
 */
function updateCartUI() {
    // 1. Calculate total number of items for the badge counter
    const totalItemCount = cart.reduce((sum, item) => sum + (parseInt(item.quantity, 10) || 0), 0);
    const badgeElement = document.getElementById("cart-count-badge");
    if (badgeElement) {
        badgeElement.textContent = totalItemCount;
    }

    // 2. Calculate financial subtotal
    const subtotal = cart.reduce((sum, item) => {
        const itemPrice = parseFloat(item.price) || 0;
        const itemQty = parseInt(item.quantity, 10) || 0;
        return sum + (itemPrice * itemQty);
    }, 0);

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

    // Render active cart items matching style.css classes
    container.innerHTML = cart.map(item => `
        <div class="cart-item-row" data-dish-id="${item.id}">
            <div class="item-info">
                <h4>${escapeCartText(item.name)}</h4>
                <span>$${(parseFloat(item.price) || 0).toFixed(2)} each</span>
            </div>
            <div class="qty-controls">
                <button type="button" class="qty-btn" onclick="updateQuantity(${item.id}, -1)" aria-label="Decrease quantity">−</button>
                <span class="qty-number">${item.quantity}</span>
                <button type="button" class="qty-btn" onclick="updateQuantity(${item.id}, 1)" aria-label="Increase quantity">+</button>
            </div>
        </div>
    `).join("");
}

/**
 * Escapes HTML characters in item names to prevent injection inside drawer
 */
function escapeCartText(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/**
 * Subtle pulse micro-animation on the navbar cart pill when an item is added
 */
function animateNavbarCartBadge() {
    const badge = document.getElementById("cart-count-badge");
    const cartBtn = document.getElementById("cart-toggle-btn");
    if (!badge && !cartBtn) return;

    const target = badge || cartBtn;
    target.style.transition = "transform 0.15s cubic-bezier(0.175, 0.885, 0.32, 1.275)";
    target.style.transform = "scale(1.25)";
    setTimeout(() => {
        target.style.transform = "scale(1)";
    }, 160);
}


// Cart drawer open/close

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


// Checkout navigation

/**
 * Handles the "Proceed to Checkout" action:
 * 1. Blocks action if cart is empty, presenting a styled modal.
 * 2. If unauthenticated, sets return redirect and navigates cleanly to login.html.
 * 3. If authenticated, allows default navigation to checkout.html.
 */
function handleProceedToCheckout(e) {
    if (!cart || cart.length === 0) {
        e.preventDefault();
        if (typeof showAppAlert === "function") {
            showAppAlert({
                title: "Your Cart is Empty",
                message: "Please select your favorite dishes from the menu before proceeding to checkout.",
                type: "info",
                tag: "Shopping Basket",
                confirmText: "Browse Menu"
            });
        }
        return;
    }

    if (typeof isAuthenticated === "function" && !isAuthenticated()) {
        e.preventDefault();
        sessionStorage.setItem("post_login_redirect", "checkout.html");
        window.location.href = "login.html";
        return;
    }
}


// Initialize cart event listeners

document.addEventListener("DOMContentLoaded", () => {
    // 1. Initial render of cart from user-scoped storage
    updateCartUI();

    // 2. Open cart button in navbar (The only trigger for the drawer)
    const openBtn = document.getElementById("cart-toggle-btn");
    if (openBtn) {
        openBtn.addEventListener("click", openCartDrawer);
    }

    // 3. Close drawer on close button click ('close-cart-btn')
    const closeBtn = document.getElementById("close-cart-btn") || document.getElementById("cart-close-btn");
    if (closeBtn) {
        closeBtn.addEventListener("click", closeCartDrawer);
    }

    // 4. Close drawer when clicking the blurred backdrop
    const backdrop = document.getElementById("cart-backdrop");
    if (backdrop) {
        backdrop.addEventListener("click", closeCartDrawer);
    }

    // 5. Intercept "Proceed to Checkout" button click ('proceed-checkout-btn')
    const checkoutBtn = document.getElementById("proceed-checkout-btn") || document.getElementById("checkout-btn");
    if (checkoutBtn) {
        checkoutBtn.addEventListener("click", handleProceedToCheckout);
    }
});