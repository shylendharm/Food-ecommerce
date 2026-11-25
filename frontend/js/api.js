/* =============================================================
   FILE: frontend/js/api.js
   API CLIENT & GLOBAL UI RUNTIME MODULE
   Centralizes all HTTP network communication with our FastAPI backend.
   Automatically manages JWT authentication and token persistence.
   Provides unified design-system modal confirmations and alert dialogs.
   Environment-Adaptive: Automatically resolves local dev vs cloud production.
   ============================================================= */

/**
 * Resolves the backend API base URL dynamically:
 * 1. Honors explicit global override: window.FOODEXPRESS_API_URL (cloud static hosting).
 * 2. Defaults to local FastAPI server on localhost/127.0.0.1.
 * 3. Fallbacks to current domain origin with /api prefix for unified cloud deployments.
 */
function resolveApiBaseUrl() {
    if (typeof window !== "undefined" && window.FOODEXPRESS_API_URL) {
        return window.FOODEXPRESS_API_URL;
    }
    const isLocalDevelopment = typeof window !== "undefined" && (
        window.location.hostname === "localhost" ||
        window.location.hostname === "127.0.0.1" ||
        window.location.protocol === "file:" ||
        window.location.hostname === ""
    );
    return isLocalDevelopment ? "http://127.0.0.1:8000/api" : `${window.location.origin}/api`;
}

// Active API Base URL and LocalStorage Session Keys
const API_BASE_URL = resolveApiBaseUrl();
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
                ...authHeaders,
                ...options.headers,
            },
            ...options,
        });

        // Handle HTTP error statuses (400, 401, 403, 404, 422, 500)
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));

            // If the server indicates the token expired or is invalid
            if (response.status === 401 && token) {
                console.warn("[Auth] Session expired. Clearing stored credentials.");
                logoutUser();
            }

            let errorMessage = `Server error: ${response.status} ${response.statusText}`;

            if (errorData.detail) {
                if (Array.isArray(errorData.detail)) {
                    errorMessage = errorData.detail.map(e => e.msg || JSON.stringify(e)).join(", ");
                } else if (typeof errorData.detail === "object") {
                    errorMessage = JSON.stringify(errorData.detail);
                } else {
                    errorMessage = String(errorData.detail);
                }
            }

            throw new Error(errorMessage);
        }

        return await response.json();
    } catch (error) {
        console.error(`[API] Network request failed for [${endpoint}]:`, error.message);
        throw error;
    }
}


/* =============================================================
   1. AUTHENTICATION & SESSION MANAGEMENT
   ============================================================= */

function saveAuthSession(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function getStoredToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function getStoredUser() {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
}

function logoutUser() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    window.location.reload();
}

function isAuthenticated() {
    return !!getStoredToken();
}

function isAdmin() {
    const user = getStoredUser();
    return user && user.role === "ADMIN";
}

async function loginUser(email, password) {
    const data = await apiRequest("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
    });

    saveAuthSession(data.access_token, data.user);
    return data;
}

async function loginWithGoogle(credential) {
    const data = await apiRequest("/auth/google", {
        method: "POST",
        body: JSON.stringify({ credential }),
    });

    saveAuthSession(data.access_token, data.user);
    return data;
}

async function registerUser(name, email, password, phone = null) {
    return await apiRequest("/auth/register", {
        method: "POST",
        body: JSON.stringify({ name, email, password, phone }),
    });
}

async function getMyProfile() {
    return await apiRequest("/auth/me");
}

async function updateUserProfile(profileData) {
    const updatedUser = await apiRequest("/auth/profile", {
        method: "PUT",
        body: JSON.stringify(profileData),
    });

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

async function getMyOrders() {
    return await apiRequest("/orders/my-orders");
}

async function cancelOrder(orderId) {
    return await apiRequest(`/orders/${orderId}/cancel`, {
        method: "PATCH",
    });
}


/* =============================================================
   4. RESTAURANT ADMIN & KITCHEN API FUNCTIONS
   ============================================================= */

async function getAdminOrders(statusFilter = null) {
    const endpoint = statusFilter ? `/admin/orders?status_filter=${statusFilter}` : "/admin/orders";
    return await apiRequest(endpoint);
}

async function updateOrderStatus(orderId, newStatus) {
    return await apiRequest(`/admin/orders/${orderId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: newStatus }),
    });
}

async function toggleDishStock(itemId) {
    return await apiRequest(`/admin/menu/${itemId}/toggle-stock`, {
        method: "PATCH",
    });
}

async function createMenuItem(dishData) {
    return await apiRequest("/admin/menu", {
        method: "POST",
        body: JSON.stringify(dishData),
    });
}


/* =============================================================
   5. PAYMENTS & FINANCIAL SETTLEMENTS API FUNCTIONS
   ============================================================= */

async function createPaymentIntent(orderId) {
    return await apiRequest("/payments/create-intent", {
        method: "POST",
        body: JSON.stringify({ order_id: Number(orderId) }),
    });
}

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

async function getPaymentDetails(orderId) {
    return await apiRequest(`/payments/order/${orderId}`);
}


/* =============================================================
   6. UNIFIED APP MODAL DIALOG ENGINE (Confirmations & Alerts)
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
window.FOODEXPRESS_API_BASE_URL = API_BASE_URL;