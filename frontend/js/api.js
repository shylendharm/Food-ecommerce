/* =============================================================
   FILE: frontend/js/api.js
   API CLIENT & GLOBAL UI RUNTIME MODULE
   Centralizes all HTTP network communication with our FastAPI backend.
   Automatically manages JWT authentication and token persistence.
   Provides unified design-system modal confirmations and alert dialogs.
   ============================================================= */

// The base address of our live Python/FastAPI server
const API_BASE_URL = "http://127.0.0.1:8000/api";
// LocalStorage Keys used to persist login session across page refreshes
const TOKEN_KEY = "foodexpress_jwt_token";
const USER_KEY = "foodexpress_user_profile";


/**
 * Centralized fetch wrapper:
 * 1. Automatically injects 'Authorization: Bearer <token>' if user is logged in.
 * 2. Parses JSON responses safely.
 * 3. Catches and bubbles up server error messages cleanly (extracts FastAPI 422 arrays).
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;

    // Read stored JWT token from localStorage (if user is logged in)
    const token = getStoredToken();
    const authHeaders = token ? { "Authorization": `Bearer ${token}` } : {};

    try {
        const response = await fetch(url, {
            headers: {
                "Content-Type": "application/json",
                ...authHeaders,         // Injects Bearer token automatically
                ...options.headers,     // Allows caller to override headers if needed
            },
            ...options,
        });

        // Handle HTTP error statuses (400, 401, 403, 404, 422, 500)
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));

            // If the server tells us our token has expired or is invalid
            if (response.status === 401 && token) {
                console.warn("[Auth] Session expired. Clearing stored credentials.");
                logoutUser();
            }

            // Extract human-readable error message (handles both plain string detail and FastAPI 422 error arrays)
            let errorMessage = `Server error: ${response.status} ${response.statusText}`;

            if (errorData.detail) {
                if (Array.isArray(errorData.detail)) {
                    // FastAPI Pydantic 422 returns an array: [{loc: [...], msg: "...", type: "..."}]
                    errorMessage = errorData.detail.map(e => e.msg || JSON.stringify(e)).join(", ");
                } else if (typeof errorData.detail === "object") {
                    errorMessage = JSON.stringify(errorData.detail);
                } else {
                    errorMessage = String(errorData.detail);
                }
            }

            throw new Error(errorMessage);
        }

        // Return parsed JSON
        return await response.json();
    } catch (error) {
        console.error(`[API] Network request failed for [${endpoint}]:`, error.message);
        throw error;
    }
}


/* =============================================================
   1. AUTHENTICATION & SESSION MANAGEMENT
   ============================================================= */

// Saves token and user info to browser's permanent localStorage
function saveAuthSession(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
}

// Retrieves the stored JWT token string (or null)
function getStoredToken() {
    return localStorage.getItem(TOKEN_KEY);
}

// Retrieves the stored user object (or null)
function getStoredUser() {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
}

// Clears session on logout
function logoutUser() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    window.location.reload(); // Refresh the page to reset navbar and UI
}

// Checks if someone is currently logged in
function isAuthenticated() {
    return !!getStoredToken();
}

// Checks if the logged-in user is an administrator
function isAdmin() {
    const user = getStoredUser();
    return user && user.role === "ADMIN";
}

/**
 * Logs in a user with email and password
 * Calls: POST /api/auth/login
 */
async function loginUser(email, password) {
    const data = await apiRequest("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
    });

    // Save token and user details to localStorage
    saveAuthSession(data.access_token, data.user);
    return data;
}

/**
 * Logs in or registers a user via Google OAuth2 Single Sign-On (SSO)
 * Calls: POST /api/auth/google
 */
async function loginWithGoogle(credential) {
    const data = await apiRequest("/auth/google", {
        method: "POST",
        body: JSON.stringify({ credential }),
    });

    // Save token and user details to localStorage
    saveAuthSession(data.access_token, data.user);
    return data;
}

/**
 * Registers a new customer account
 * Calls: POST /api/auth/register
 */
async function registerUser(name, email, password, phone = null) {
    return await apiRequest("/auth/register", {
        method: "POST",
        body: JSON.stringify({ name, email, password, phone }),
    });
}

/**
 * Fetches latest profile data for the logged-in user
 * Calls: GET /api/auth/me
 */
async function getMyProfile() {
    return await apiRequest("/auth/me");
}

/**
 * Updates profile details (Full Name, Phone Number, Default Address)
 * Calls: PUT /api/auth/profile
 */
async function updateUserProfile(profileData) {
    const updatedUser = await apiRequest("/auth/profile", {
        method: "PUT",
        body: JSON.stringify(profileData),
    });

    // Synchronize fresh user state into local storage
    const currentToken = getStoredToken();
    if (currentToken && updatedUser) {
        saveAuthSession(currentToken, updatedUser);
    }

    return updatedUser;
}


/* =============================================================
   2. MENU & CATEGORIES API FUNCTIONS
   ============================================================= */

async function getCategories() {
    return await apiRequest("/categories");
}

async function getMenuItems(categoryId = null, isVeg = null) {
    const queryParams = new URLSearchParams();

    if (categoryId !== null && categoryId !== "") {
        queryParams.append("category_id", categoryId);
    }

    if (isVeg !== null && isVeg !== false) {
        queryParams.append("is_veg", "true");
    }

    const queryString = queryParams.toString();
    const endpoint = queryString ? `/menu?${queryString}` : "/menu";

    return await apiRequest(endpoint);
}

async function getMenuItemById(itemId) {
    return await apiRequest(`/menu/${itemId}`);
}


/* =============================================================
   3. ORDERS & CHECKOUT API FUNCTIONS
   ============================================================= */

async function submitOrder(orderData) {
    return await apiRequest("/orders", {
        method: "POST",
        body: JSON.stringify(orderData),
    });
}

async function getOrderById(orderId) {
    return await apiRequest(`/orders/${orderId}`);
}

/**
 * Fetches order history for the currently logged-in customer
 * Calls: GET /api/orders/my-orders
 */
async function getMyOrders() {
    return await apiRequest("/orders/my-orders");
}

/**
 * Cancels a customer's pending order
 * Calls: PATCH /api/orders/{order_id}/cancel
 */
async function cancelOrder(orderId) {
    return await apiRequest(`/orders/${orderId}/cancel`, {
        method: "PATCH",
    });
}


/* =============================================================
   4. RESTAURANT ADMIN & KITCHEN API FUNCTIONS
   ============================================================= */

/**
 * Fetches all orders across all customers (with optional status filter)
 * Calls: GET /api/admin/orders?status_filter=PENDING
 */
async function getAdminOrders(statusFilter = null) {
    const endpoint = statusFilter ? `/admin/orders?status_filter=${statusFilter}` : "/admin/orders";
    return await apiRequest(endpoint);
}

/**
 * Updates an order status (e.g., PENDING -> PREPARING, or CANCELLED)
 * Calls: PATCH /api/admin/orders/{id}/status
 */
async function updateOrderStatus(orderId, newStatus) {
    return await apiRequest(`/admin/orders/${orderId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: newStatus }),
    });
}

/**
 * Toggles a dish's in-stock / out-of-stock availability
 * Calls: PATCH /api/admin/menu/{id}/toggle-stock
 */
async function toggleDishStock(itemId) {
    return await apiRequest(`/admin/menu/${itemId}/toggle-stock`, {
        method: "PATCH",
    });
}

/**
 * Creates a new dish in the menu
 * Calls: POST /api/admin/menu
 */
async function createMenuItem(dishData) {
    return await apiRequest("/admin/menu", {
        method: "POST",
        body: JSON.stringify(dishData),
    });
}


/* =============================================================
   5. PAYMENTS & FINANCIAL SETTLEMENTS API FUNCTIONS
   ============================================================= */

/**
 * Initializes an online payment session with the gateway
 * Calls: POST /api/payments/create-intent
 */
async function createPaymentIntent(orderId) {
    return await apiRequest("/payments/create-intent", {
        method: "POST",
        body: JSON.stringify({ order_id: Number(orderId) }),
    });
}

/**
 * Simulates the Payment Gateway delivering an HMAC-signed webhook
 * Calls: POST /api/payments/webhook
 */
async function triggerPaymentWebhook(webhookData, signature) {
    const url = `${API_BASE_URL}/payments/webhook`;

    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-Signature": signature,
        },
        body: JSON.stringify(webhookData),
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Payment webhook verification failed.");
    }

    return await response.json();
}

/**
 * Retrieves the payment settlement status for an order
 * Calls: GET /api/payments/order/{order_id}
 */
async function getPaymentDetails(orderId) {
    return await apiRequest(`/payments/order/${orderId}`);
}


/* =============================================================
   6. UNIFIED APP MODAL DIALOG ENGINE (Confirmations & Alerts)
   Replaces native browser window.alert and window.confirm with
   a non-blocking, accessible, design-system compliant modal.
   ============================================================= */

function getOrCreateModalContainer() {
    let container = document.getElementById("app-global-modal-root");
    if (!container) {
        container = document.createElement("div");
        container.id = "app-global-modal-root";
        document.body.appendChild(container);
    }
    return container;
}

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/**
 * Asynchronous Confirmation Dialog
 * @param {Object} options
 * @param {string} options.title - Header text (e.g. "Sign Out")
 * @param {string} options.message - Body text explaining action
 * @param {string|null} [options.tag=null] - Optional small pill tag
 * @param {string} [options.confirmText="Confirm"] - Text on confirm button
 * @param {string} [options.cancelText="Cancel"] - Text on cancel button
 * @param {boolean} [options.isDanger=false] - If true, uses red danger styling
 * @returns {Promise<boolean>} Resolves true if confirmed, false if cancelled
 */
function showAppConfirm({
    title = "Confirm Action",
    message = "Are you sure you want to proceed?",
    tag = null,
    confirmText = "Confirm",
    cancelText = "Cancel",
    isDanger = false
} = {}) {
    return new Promise((resolve) => {
        const root = getOrCreateModalContainer();
        const tagClass = isDanger ? "tag-danger" : "tag-info";
        const confirmBtnClass = isDanger ? "btn-modal-confirm danger" : "btn-modal-confirm";
        const tagHtml = tag ? `<span class="app-modal-tag ${tagClass}">${escapeHtml(tag)}</span>` : "";

        root.innerHTML = `
            <div class="app-modal-backdrop" id="app-modal-backdrop">
                <div class="app-modal-card" role="dialog" aria-modal="true" aria-labelledby="modal-title">
                    ${tagHtml}
                    <h3 class="app-modal-title" id="modal-title">${escapeHtml(title)}</h3>
                    <p class="app-modal-message">${escapeHtml(message)}</p>
                    <div class="app-modal-actions">
                        <button type="button" class="btn-modal-cancel" id="btn-modal-cancel">
                            ${escapeHtml(cancelText)}
                        </button>
                        <button type="button" class="${confirmBtnClass}" id="btn-modal-confirm">
                            ${escapeHtml(confirmText)}
                        </button>
                    </div>
                </div>
            </div>
        `;

        const backdrop = document.getElementById("app-modal-backdrop");
        const confirmBtn = document.getElementById("btn-modal-confirm");
        const cancelBtn = document.getElementById("btn-modal-cancel");

        // Trigger entrance transition
        requestAnimationFrame(() => {
            backdrop.classList.add("open");
            confirmBtn?.focus();
        });

        function cleanup(result) {
            backdrop.classList.remove("open");
            setTimeout(() => {
                root.innerHTML = "";
            }, 200);
            document.removeEventListener("keydown", handleKeydown);
            resolve(result);
        }

        function handleKeydown(e) {
            if (e.key === "Escape") {
                cleanup(false);
            }
        }

        confirmBtn?.addEventListener("click", () => cleanup(true));
        cancelBtn?.addEventListener("click", () => cleanup(false));
        backdrop?.addEventListener("click", (e) => {
            if (e.target === backdrop) cleanup(false);
        });
        document.addEventListener("keydown", handleKeydown);
    });
}

/**
 * Asynchronous Alert Dialog
 * @param {Object} options
 * @param {string} options.title - Header text
 * @param {string} options.message - Body text
 * @param {string|null} [options.tag=null] - Optional small pill tag
 * @param {string} [options.confirmText="OK"] - Text on dismiss button
 * @param {"info"|"warning"|"danger"} [options.type="info"]
 * @returns {Promise<void>}
 */
function showAppAlert({
    title = "Notice",
    message = "",
    tag = null,
    confirmText = "OK",
    type = "info"
} = {}) {
    return new Promise((resolve) => {
        const root = getOrCreateModalContainer();
        let tagClass = "tag-info";
        if (type === "danger") tagClass = "tag-danger";
        else if (type === "warning") tagClass = "tag-warning";
        const tagHtml = tag ? `<span class="app-modal-tag ${tagClass}">${escapeHtml(tag)}</span>` : "";

        root.innerHTML = `
            <div class="app-modal-backdrop" id="app-modal-backdrop">
                <div class="app-modal-card" role="dialog" aria-modal="true" aria-labelledby="modal-title">
                    ${tagHtml}
                    <h3 class="app-modal-title" id="modal-title">${escapeHtml(title)}</h3>
                    <p class="app-modal-message">${escapeHtml(message)}</p>
                    <div class="app-modal-actions">
                        <button type="button" class="btn-modal-confirm" id="btn-modal-ok">
                            ${escapeHtml(confirmText)}
                        </button>
                    </div>
                </div>
            </div>
        `;

        const backdrop = document.getElementById("app-modal-backdrop");
        const okBtn = document.getElementById("btn-modal-ok");

        requestAnimationFrame(() => {
            backdrop.classList.add("open");
            okBtn?.focus();
        });

        function cleanup() {
            backdrop.classList.remove("open");
            setTimeout(() => {
                root.innerHTML = "";
            }, 200);
            document.removeEventListener("keydown", handleKeydown);
            resolve();
        }

        function handleKeydown(e) {
            if (e.key === "Escape" || e.key === "Enter") {
                cleanup();
            }
        }

        okBtn?.addEventListener("click", cleanup);
        backdrop?.addEventListener("click", (e) => {
            if (e.target === backdrop) cleanup();
        });
        document.addEventListener("keydown", handleKeydown);
    });
}

// Expose modal helpers globally on window object
window.showAppConfirm = showAppConfirm;
window.showAppAlert = showAppAlert;