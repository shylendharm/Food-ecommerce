/* =============================================================
   RESTAURANT OPERATIONS COMMAND CENTER (frontend/js/admin.js)
   Executive KPIs, Kitchen Display System (KDS) Queue,
   and 80-Dish Instant Inventory Stock Controls.
   ============================================================= */

// Global State
let currentStatusFilter = ""; // "" means all tickets
let allOrdersCache = [];
let allInventoryCache = [];
let pollIntervalId = null;

// Category Metadata & Multi-Tier Fallback Images
const CATEGORY_NAMES = {
    1: "Pizzas",
    2: "Burgers & Sandwiches",
    3: "Sides & Appetizers",
    4: "Desserts & Beverages"
};

const CATEGORY_FALLBACK_IMAGES = {
    1: "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=300&q=80",
    2: "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=300&q=80",
    3: "https://images.unsplash.com/photo-1541592106381-b31e9677c0e5?w=300&q=80",
    4: "https://images.unsplash.com/photo-1551024709-8f23befc6f87?w=300&q=80"
};

/* =============================================================
   1. INITIALIZATION & RBAC SECURITY GUARD
   ============================================================= */

document.addEventListener("DOMContentLoaded", () => {
    // 1. RBAC Guard: Strictly verify ADMIN role
    if (!isAdmin()) {
        const deniedBox = document.getElementById("admin-access-denied");
        const dashboard = document.getElementById("admin-dashboard-content");
        if (deniedBox) deniedBox.classList.remove("hidden");
        if (dashboard) dashboard.classList.add("hidden");
        return;
    }

    // Authenticated Master Administrator: Show console
    const deniedBox = document.getElementById("admin-access-denied");
    const dashboard = document.getElementById("admin-dashboard-content");
    if (deniedBox) deniedBox.classList.add("hidden");
    if (dashboard) dashboard.classList.remove("hidden");

    // 2. Wire up Tab Switchers & Search Controls
    initNavigationTabs();
    initFilterButtons();
    initSearchInputs();

    // 3. Initial Load: Metrics, Tickets, and Polling Loop
    refreshDashboard();
    startOrderPollingLoop();
});

// Clean up polling loop if navigating away
window.addEventListener("beforeunload", () => {
    if (pollIntervalId) clearInterval(pollIntervalId);
});


/* =============================================================
   2. REVENUE & EXECUTIVE METRICS (KPIs)
   ============================================================= */

async function loadExecutiveMetrics() {
    try {
        const metrics = await apiRequest("/admin/metrics");
        if (!metrics) return;

        const revenueEl = document.getElementById("metric-revenue");
        const ordersEl = document.getElementById("metric-orders");
        const activeEl = document.getElementById("metric-active");
        const deliveringEl = document.getElementById("metric-delivering");

        if (revenueEl) revenueEl.textContent = `$${Number(metrics.total_revenue || 0).toFixed(2)}`;
        if (ordersEl) ordersEl.textContent = metrics.total_orders || 0;
        if (activeEl) activeEl.textContent = metrics.active_kitchen_orders || 0;
        if (deliveringEl) deliveringEl.textContent = metrics.delivering_orders || 0;

    } catch (error) {
        console.warn("Failed to refresh admin metrics:", error);
    }
}


/* =============================================================
   3. NAVIGATION TABS & UTILITIES
   ============================================================= */

function initNavigationTabs() {
    const tabOrders = document.getElementById("admin-tab-orders");
    const tabInventory = document.getElementById("admin-tab-inventory");
    const viewOrders = document.getElementById("admin-orders-view");
    const viewInventory = document.getElementById("admin-inventory-view");

    tabOrders?.addEventListener("click", () => {
        tabOrders.classList.add("active");
        tabInventory?.classList.remove("active");
        viewOrders?.classList.remove("hidden");
        viewInventory?.classList.add("hidden");
        loadAdminOrders();
    });

    tabInventory?.addEventListener("click", () => {
        tabInventory.classList.add("active");
        tabOrders?.classList.remove("active");
        viewInventory?.classList.remove("hidden");
        viewOrders?.classList.add("hidden");
        loadAdminInventory();
    });

    // Manual Refresh button
    document.getElementById("refresh-orders-btn")?.addEventListener("click", () => {
        refreshDashboard();
    });
}

function refreshDashboard() {
    loadExecutiveMetrics();
    loadAdminOrders();
}


/* =============================================================
   4. REAL-TIME POLLING LOOP (KEEPS TICKETS SYNCED)
   ============================================================= */

function startOrderPollingLoop() {
    // Poll every 12 seconds for fresh orders
    pollIntervalId = setInterval(async () => {
        const ordersView = document.getElementById("admin-orders-view");
        if (ordersView && !ordersView.classList.contains("hidden")) {
            await silentOrdersCheck();
            loadExecutiveMetrics();
        }
    }, 12000);
}

async function silentOrdersCheck() {
    try {
        const orders = await getAdminOrders(currentStatusFilter || null);
        allOrdersCache = orders;
        renderFilteredOrders();
    } catch (err) {
        console.warn("Silent polling check:", err);
    }
}


/* =============================================================
   5. KDS FILTER & SEARCH TOOLBAR
   ============================================================= */

function initFilterButtons() {
    const filterButtons = document.querySelectorAll(".order-filter-btn");

    filterButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            filterButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            currentStatusFilter = btn.dataset.status || "";
            loadAdminOrders();
        });
    });
}

function initSearchInputs() {
    // 1. Orders live search
    const ordersSearchInput = document.getElementById("admin-orders-search");
    ordersSearchInput?.addEventListener("input", () => {
        renderFilteredOrders();
    });

    // 2. 80-Dish inventory live search
    const invSearchInput = document.getElementById("inventory-search-input");
    invSearchInput?.addEventListener("input", () => {
        renderFilteredInventory();
    });
}


/* =============================================================
   6. LOAD & RENDER KITCHEN ORDER TICKETS
   ============================================================= */

async function loadAdminOrders() {
    const container = document.getElementById("admin-orders-container");
    if (!container) return;

    container.innerHTML = `
        <div class="loading-state" style="grid-column: 1 / -1;">
            <p>Connecting to kitchen dispatch stream...</p>
        </div>
    `;

    try {
        const orders = await getAdminOrders(currentStatusFilter || null);
        allOrdersCache = orders;
        renderFilteredOrders();

    } catch (error) {
        console.error("Failed to load admin orders:", error);
        container.innerHTML = `
            <div style="grid-column: 1 / -1; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); color: #F87171; padding: 24px; border-radius: 12px; text-align: center;">
                <p><strong>Failed to load orders:</strong> ${escapeHtml(error.message)}</p>
                <button onclick="loadAdminOrders()" class="btn-storefront-switch" style="margin-top: 12px;">Retry</button>
            </div>
        `;
    }
}

function renderFilteredOrders() {
    const container = document.getElementById("admin-orders-container");
    if (!container) return;

    const searchTerm = (document.getElementById("admin-orders-search")?.value || "").toLowerCase().trim();

    // In-memory instant filtering
    let visibleOrders = allOrdersCache;

    if (searchTerm) {
        visibleOrders = visibleOrders.filter(order => {
            const idMatch = String(order.id).includes(searchTerm);
            const nameMatch = (order.customer_name || "").toLowerCase().includes(searchTerm);
            const phoneMatch = (order.customer_phone || "").toLowerCase().includes(searchTerm);
            const itemMatch = (order.items || []).some(item =>
                (item.item_name_snapshot || "").toLowerCase().includes(searchTerm)
            );
            return idMatch || nameMatch || phoneMatch || itemMatch;
        });
    }

    if (visibleOrders.length === 0) {
        container.innerHTML = `
            <div style="grid-column: 1 / -1; background: #111827; padding: 60px 24px; text-align: center; border-radius: 14px; border: 1px solid #1F2937;">
                <span style="font-size: 3rem; display: block; margin-bottom: 12px;">🎉</span>
                <h3 style="font-size: 1.25rem; font-weight: 700; color: #FFFFFF; margin-bottom: 6px;">Queue is Clean</h3>
                <p style="color: #94A3B8; font-size: 0.9rem;">No active tickets matching the selected filter.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = visibleOrders.map(order => renderKitchenTicket(order)).join("");
    attachTicketActionListeners();
}

function renderKitchenTicket(order) {
    const statusClassMap = {
        "PENDING": "kds-status-pending",
        "PREPARING": "kds-status-preparing",
        "OUT_FOR_DELIVERY": "kds-status-delivering",
        "DELIVERED": "kds-status-delivered",
        "CANCELLED": "kds-status-cancelled"
    };

    const statusBadgeMap = {
        "PENDING": `<span class="ticket-badge badge-pending">⏳ New Ticket</span>`,
        "PREPARING": `<span class="ticket-badge badge-preparing">🔥 Cooking</span>`,
        "OUT_FOR_DELIVERY": `<span class="ticket-badge badge-delivering">🛵 En Route</span>`,
        "DELIVERED": `<span class="ticket-badge badge-delivered">✅ Delivered</span>`,
        "CANCELLED": `<span class="ticket-badge badge-cancelled">✕ Cancelled</span>`
    };

    const cardStatusClass = statusClassMap[order.status] || "kds-status-pending";
    const statusBadge = statusBadgeMap[order.status] || `<span class="ticket-badge">${order.status}</span>`;
    const timeAgo = formatTimeAgo(order.created_at);

    // Items list
    const itemsHtml = (order.items || []).map(item => `
        <div class="ticket-item-row">
            <div>
                <span class="ticket-item-qty">${item.quantity}x</span>
                <span class="ticket-item-name">${escapeHtml(item.item_name_snapshot)}</span>
            </div>
            <span class="ticket-item-price">$${(Number(item.price_per_unit) * item.quantity).toFixed(2)}</span>
        </div>
    `).join("");

    // Next Action Buttons
    let actionButtonsHtml = "";
    if (order.status === "PENDING") {
        actionButtonsHtml = `
            <div class="ticket-actions-bar">
                <button class="btn-kds-action btn-kds-cook" data-order-id="${order.id}" data-next-status="PREPARING">
                    <span>👨‍🍳</span>
                    <span>Start Cooking</span>
                </button>
                <button class="btn-kds-cancel" data-order-id="${order.id}" data-next-status="CANCELLED" title="Cancel this order">
                    ✕
                </button>
            </div>
        `;
    } else if (order.status === "PREPARING") {
        actionButtonsHtml = `
            <div class="ticket-actions-bar">
                <button class="btn-kds-action btn-kds-dispatch" data-order-id="${order.id}" data-next-status="OUT_FOR_DELIVERY">
                    <span>🛵</span>
                    <span>Dispatch Rider</span>
                </button>
                <button class="btn-kds-cancel" data-order-id="${order.id}" data-next-status="CANCELLED" title="Cancel this order">
                    ✕
                </button>
            </div>
        `;
    } else if (order.status === "OUT_FOR_DELIVERY") {
        actionButtonsHtml = `
            <div class="ticket-actions-bar">
                <button class="btn-kds-action btn-kds-deliver" data-order-id="${order.id}" data-next-status="DELIVERED">
                    <span>✅</span>
                    <span>Mark Delivered</span>
                </button>
            </div>
        `;
    } else if (order.status === "DELIVERED") {
        actionButtonsHtml = `
            <div style="text-align: center; padding: 8px 0; color: #34D399; font-size: 0.82rem; font-weight: 700;">
                ✨ Order Completed & Settled
            </div>
        `;
    } else {
        actionButtonsHtml = `
            <div style="text-align: center; padding: 8px 0; color: #94A3B8; font-size: 0.82rem; font-weight: 600;">
                🚫 Ticket Cancelled
            </div>
        `;
    }

    return `
        <article class="kds-ticket-card ${cardStatusClass}" id="ticket-${order.id}">
            <div>
                <!-- Ticket Header -->
                <div class="ticket-header">
                    <div class="ticket-id-wrap">
                        <span class="ticket-id">#${order.id}</span>
                        <span class="ticket-time-ago">${timeAgo}</span>
                    </div>
                    ${statusBadge}
                </div>

                <!-- Customer Details Block -->
                <div class="ticket-customer-info">
                    <div class="customer-name">${escapeHtml(order.customer_name || 'Customer')}</div>
                    <div class="customer-meta">
                        <span>📞 ${escapeHtml(order.customer_phone || 'No phone provided')}</span>
                        <span>📍 ${escapeHtml(order.delivery_address || 'Delivery Address')}</span>
                    </div>
                </div>

                <!-- Food Items Ordered -->
                <div class="ticket-items-list">
                    ${itemsHtml || '<div style="color: #64748B; font-size: 0.8rem;">No items recorded</div>'}
                </div>
            </div>

            <div>
                <!-- Payment & Total Summary -->
                <div class="ticket-footer-summary">
                    <span class="ticket-pay-badge ${order.payment_method === 'ONLINE' ? 'ticket-pay-paid' : 'ticket-pay-pending'}">
                        ${order.payment_method === 'ONLINE' ? '💳 Paid Online' : '💵 Cash on Delivery'}
                    </span>
                    <span class="ticket-total-price">$${Number(order.total_amount).toFixed(2)}</span>
                </div>

                <!-- Progression Action Buttons -->
                ${actionButtonsHtml}
            </div>
        </article>
    `;
}

function attachTicketActionListeners() {
    // 1. Advance buttons (Cook, Dispatch, Deliver)
    document.querySelectorAll(".btn-kds-action").forEach(btn => {
        btn.addEventListener("click", async () => {
            const orderId = btn.dataset.orderId;
            const nextStatus = btn.dataset.nextStatus;
            await handleStatusAdvance(orderId, nextStatus, btn);
        });
    });

    // 2. Cancellation buttons
    document.querySelectorAll(".btn-kds-cancel").forEach(btn => {
        btn.addEventListener("click", async () => {
            const orderId = btn.dataset.orderId;
            const confirmCancel = confirm(`Are you sure you want to cancel Order #${orderId}?`);
            if (confirmCancel) {
                await handleStatusAdvance(orderId, "CANCELLED", btn);
            }
        });
    });
}

async function handleStatusAdvance(orderId, nextStatus, buttonElement) {
    const originalText = buttonElement.innerHTML;
    buttonElement.disabled = true;
    buttonElement.innerHTML = `<span>⏳ Updating...</span>`;

    try {
        await updateOrderStatus(orderId, nextStatus);

        // Update local cache optimistically
        const order = allOrdersCache.find(o => o.id === Number(orderId));
        if (order) {
            order.status = nextStatus;
        }

        // Re-render and refresh metrics
        renderFilteredOrders();
        loadExecutiveMetrics();

    } catch (error) {
        alert(`Failed to update ticket: ${error.message}`);
        buttonElement.disabled = false;
        buttonElement.innerHTML = originalText;
    }
}


/* =============================================================
   7. 80-DISH INVENTORY STOCK CONTROLLER (VIEW 2)
   ============================================================= */

async function loadAdminInventory() {
    const container = document.getElementById("admin-inventory-table-container");
    if (!container) return;

    container.innerHTML = `
        <div class="loading-state">
            <p>Retrieving 80 dishes from database...</p>
        </div>
    `;

    try {
        const dishes = await apiRequest("/admin/menu");
        allInventoryCache = dishes;
        renderFilteredInventory();

    } catch (error) {
        console.error("Failed to load inventory:", error);
        container.innerHTML = `
            <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); color: #F87171; padding: 24px; border-radius: 12px; text-align: center;">
                <p>Failed to load inventory catalog: ${escapeHtml(error.message)}</p>
                <button onclick="loadAdminInventory()" class="btn-storefront-switch" style="margin-top: 12px;">Retry</button>
            </div>
        `;
    }
}

function renderFilteredInventory() {
    const container = document.getElementById("admin-inventory-table-container");
    if (!container) return;

    const searchTerm = (document.getElementById("inventory-search-input")?.value || "").toLowerCase().trim();

    let visibleDishes = allInventoryCache;
    if (searchTerm) {
        visibleDishes = visibleDishes.filter(d =>
            d.name.toLowerCase().includes(searchTerm) ||
            (CATEGORY_NAMES[d.category_id] || "").toLowerCase().includes(searchTerm)
        );
    }

    if (visibleDishes.length === 0) {
        container.innerHTML = `
            <div style="padding: 40px; text-align: center; color: #94A3B8;">
                No dishes found matching "<strong>${escapeHtml(searchTerm)}</strong>".
            </div>
        `;
        return;
    }

    const rowsHtml = visibleDishes.map(dish => {
        const fallbackImg = CATEGORY_FALLBACK_IMAGES[dish.category_id] || CATEGORY_FALLBACK_IMAGES[1];
        const categoryName = CATEGORY_NAMES[dish.category_id] || "Specialties";

        return `
            <tr id="inventory-row-${dish.id}">
                <td>
                    <div class="dish-thumb-cell">
                        <img 
                            src="${dish.image_url || fallbackImg}" 
                            alt="${escapeHtml(dish.name)}" 
                            class="dish-thumb-img"
                            onerror="this.onerror=null; this.src='${fallbackImg}';"
                        >
                        <div>
                            <div class="dish-name-cell">${escapeHtml(dish.name)}</div>
                            <div class="dish-desc-sub">${escapeHtml(dish.description || '')}</div>
                        </div>
                    </div>
                </td>
                <td>
                    <span class="diet-pill ${dish.is_veg ? 'diet-veg' : 'diet-nonveg'}">
                        ${dish.is_veg ? '🌱 VEG' : '🍖 NON-VEG'}
                    </span>
                </td>
                <td>
                    <span class="category-pill">${categoryName}</span>
                </td>
                <td class="price-cell">
                    $${Number(dish.price).toFixed(2)}
                </td>
                <td>
                    <!-- iOS-Style Instant Stock Toggle Switch -->
                    <div style="display: flex; align-items: center;">
                        <label class="stock-toggle-switch">
                            <input 
                                type="checkbox" 
                                class="stock-toggle-input" 
                                data-dish-id="${dish.id}" 
                                ${dish.is_available ? 'checked' : ''}
                            >
                            <span class="stock-slider"></span>
                        </label>
                        <span class="stock-status-label ${dish.is_available ? 'stock-in' : 'stock-out'}" id="stock-label-${dish.id}">
                            ${dish.is_available ? 'In Stock' : 'Sold Out'}
                        </span>
                    </div>
                </td>
            </tr>
        `;
    }).join("");

    container.innerHTML = `
        <table class="admin-table">
            <thead>
                <tr>
                    <th>Dish Details</th>
                    <th>Diet</th>
                    <th>Category</th>
                    <th>Price</th>
                    <th>Stock Availability</th>
                </tr>
            </thead>
            <tbody>
                ${rowsHtml}
            </tbody>
        </table>
    `;

    attachInventoryToggleListeners();
}

function attachInventoryToggleListeners() {
    document.querySelectorAll(".stock-toggle-input").forEach(toggle => {
        toggle.addEventListener("change", async (e) => {
            const dishId = toggle.dataset.dishId;
            const isChecked = toggle.checked;
            const labelEl = document.getElementById(`stock-label-${dishId}`);

            // Optimistic UI update
            if (labelEl) {
                labelEl.textContent = isChecked ? "In Stock" : "Sold Out";
                labelEl.className = `stock-status-label ${isChecked ? 'stock-in' : 'stock-out'}`;
            }

            try {
                // Call PATCH /api/admin/menu/{id}/toggle-stock
                await toggleDishStock(dishId);

                // Update cached dish state
                const dish = allInventoryCache.find(d => d.id === Number(dishId));
                if (dish) {
                    dish.is_available = isChecked;
                }

                // Refresh metrics in background
                loadExecutiveMetrics();

            } catch (error) {
                // Revert on failure
                alert(`Failed to update stock: ${error.message}`);
                toggle.checked = !isChecked;
                if (labelEl) {
                    labelEl.textContent = !isChecked ? "In Stock" : "Sold Out";
                    labelEl.className = `stock-status-label ${!isChecked ? 'stock-in' : 'stock-out'}`;
                }
            }
        });
    });
}


/* =============================================================
   8. UTILITY HELPERS
   ============================================================= */

function formatTimeAgo(dateString) {
    if (!dateString) return "just now";
    const date = new Date(dateString);
    const now = new Date();
    const diffSeconds = Math.max(0, Math.floor((now - date) / 1000));

    if (diffSeconds < 60) return "just now";
    const diffMinutes = Math.floor(diffSeconds / 60);
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
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