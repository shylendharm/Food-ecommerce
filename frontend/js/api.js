/* =============================================================
   FILE: frontend/js/api.js
   API CLIENT MODULE
   Centralizes all HTTP network communication with our FastAPI backend.
   Automatically manages JWT authentication and token persistence.
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