/* =============================================================
   API CLIENT MODULE (frontend/js/api.js)
   Centralizes all HTTP network communication with our FastAPI backend.
   ============================================================= */

// The base address of our live Python/FastAPI server
const API_BASE_URL = "http://localhost:8000/api";

/**
 * Helper function to handle network requests cleanly
 * Sends an HTTP request and parses the incoming JSON response.
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;

    try {
        const response = await fetch(url, {
            headers: {
                "Content-Type": "application/json",
                ...options.headers,
            },
            ...options,
        });

        // If the server answered with an error code (400, 404, 500, etc.)
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorMessage = errorData.detail || `Server error: ${response.status} ${response.statusText}`;
            throw new Error(errorMessage);
        }

        // Parse the JSON data sent back from Python!
        return await response.json();
    } catch (error) {
        console.error(`❌ Network request failed for [${endpoint}]:`, error.message);
        throw error;
    }
}


/* =============================================================
   1. MENU & CATEGORIES API FUNCTIONS
   ============================================================= */

/**
 * Fetches all categories (Pizzas, Burgers, etc.)
 * Calls: GET http://localhost:8000/api/categories
 */
async function getCategories() {
    return await apiRequest("/categories");
}

/**
 * Fetches menu items with optional category and veg filtering
 * Calls: GET http://localhost:8000/api/menu?category_id=1&is_veg=true
 */
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

/**
 * Fetches full details for a single dish by its unique ID
 * Calls: GET http://localhost:8000/api/menu/{id}
 */
async function getMenuItemById(itemId) {
    return await apiRequest(`/menu/${itemId}`);
}


/* =============================================================
   2. ORDERS & CHECKOUT API FUNCTIONS
   ============================================================= */

/**
 * Submits a new customer order to the database
 * Calls: POST http://localhost:8000/api/orders
 * Payload format: { customer_name, customer_email, customer_phone, delivery_address, payment_method, items }
 */
async function submitOrder(orderData) {
    return await apiRequest("/orders", {
        method: "POST",
        body: JSON.stringify(orderData), // Converts Python-style dictionary/JSON
    });
}

/**
 * Fetches an existing order for live tracking & receipts
 * Calls: GET http://localhost:8000/api/orders/{id}
 */
async function getOrderById(orderId) {
    return await apiRequest(`/orders/${orderId}`);
}