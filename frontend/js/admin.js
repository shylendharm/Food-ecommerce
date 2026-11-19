/* =============================================================
   RESTAURANT KITCHEN & INVENTORY CONTROLLER (frontend/js/admin.js)
   Enforces admin RBAC, manages kitchen order workflow stages,
   and controls menu item in-stock/out-of-stock toggling.
   ============================================================= */

let currentStatusFilter = ""; // Empty string means "All Tickets"

document.addEventListener("DOMContentLoaded", () => {
    // 1. RBAC Guard: Only ADMIN users may enter!
    if (!isAdmin()) {
        document.getElementById("admin-access-denied").style.display = "block";
        document.getElementById("admin-dashboard-content").style.display = "none";
        return;
    }

    // User is genuine ADMIN: Show dashboard
    document.getElementById("admin-access-denied").style.display = "none";
    document.getElementById("admin-dashboard-content").style.display = "block";

    // 2. Initialize Navigation Tabs & Event Listeners
    initAdminTabs();
    initFilterButtons();

    // 3. Load initial data
    loadAdminOrders();
});


/* =============================================================
   1. NAVIGATION TABS (Tickets vs Inventory)
   ============================================================= */

function initAdminTabs() {
    const tabOrders = document.getElementById("admin-tab-orders");
    const tabInventory = document.getElementById("admin-tab-inventory");
    const viewOrders = document.getElementById("admin-orders-view");
    const viewInventory = document.getElementById("admin-inventory-view");

    tabOrders?.addEventListener("click", () => {
        tabOrders.style.background = "white";
        tabOrders.style.color = "var(--text-main)";
        tabInventory.style.background = "transparent";
        tabInventory.style.color = "var(--text-muted)";

        viewOrders.style.display = "block";
        viewInventory.style.display = "none";
        loadAdminOrders();
    });

    tabInventory?.addEventListener("click", () => {
        tabInventory.style.background = "white";
        tabInventory.style.color = "var(--text-main)";
        tabOrders.style.background = "transparent";
        tabOrders.style.color = "var(--text-muted)";

        viewInventory.style.display = "block";
        viewOrders.style.display = "none";
        loadAdminInventory();
    });

    document.getElementById("refresh-orders-btn")?.addEventListener("click", () => {
        loadAdminOrders();
    });
}


/* =============================================================
   2. FILTER BUTTONS (All, Pending, Cooking, Delivery, Delivered)
   ============================================================= */

function initFilterButtons() {
    const filterButtons = document.querySelectorAll(".order-filter-btn");

    filterButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            filterButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            currentStatusFilter = btn.dataset.status;
            loadAdminOrders();
        });
    });
}


/* =============================================================
   3. LOAD & RENDER KITCHEN ORDER TICKETS
   ============================================================= */

async function loadAdminOrders() {
    const container = document.getElementById("admin-orders-container");
    if (!container) return;

    container.innerHTML = `
        <div class="loading-state" style="grid-column: 1 / -1;">
            <p>Loading kitchen tickets...</p>
        </div>
    `;

    try {
        const orders = await getAdminOrders(currentStatusFilter || null);

        if (orders.length === 0) {
            container.innerHTML = `
                <div style="grid-column: 1 / -1; background: white; padding: 40px; text-align: center; border-radius: var(--radius-md); border: 1px solid var(--border);">
                    <span style="font-size: 2.5rem;">🎉</span>
                    <h3 style="margin: 10px 0 6px; font-weight: 700;">No Orders in this Category</h3>
                    <p style="color: var(--text-muted); font-size: 0.9rem;">The kitchen queue is clear!</p>
                </div>
            `;
            return;
        }

        container.innerHTML = orders.map(order => renderKitchenTicket(order)).join("");

        // Attach action handlers for advancing order stages
        attachTicketActionListeners();

    } catch (error) {
        console.error("Failed to load admin orders:", error);
        container.innerHTML = `
            <div style="grid-column: 1 / -1; background: #FEF2F2; border: 1px solid #FCA5A5; color: #991B1B; padding: 20px; border-radius: var(--radius-md); text-align: center;">
                <p><strong>Failed to load orders:</strong> ${error.message}</p>
                <button onclick="loadAdminOrders()" class="btn-login" style="margin: 10px auto 0; background: white;">Try Again</button>
            </div>
        `;
    }
}


/**
 * Helper to render a single kitchen order ticket card
 */
function renderKitchenTicket(order) {
    const orderDate = new Date(order.created_at).toLocaleTimeString("en-US", {
        hour: "numeric",
        minute: "2-digit",
        hour12: true
    });

    const statusClass = `status-${order.status.toLowerCase()}`;
    const statusDisplay = order.status.replace(/_/g, " ");

    const itemsSummary = order.items.map(i => `
        <div style="display: flex; justify-content: space-between; font-size: 0.9rem; padding: 3px 0;">
            <span><strong>${i.quantity}x</strong> ${i.item_name_snapshot}</span>
            <span>$${(Number(i.price_per_unit) * i.quantity).toFixed(2)}</span>
        </div>
    `).join("");

    // Determine the next action button depending on current stage
    let actionButtonHtml = "";
    if (order.status === "PENDING") {
        actionButtonHtml = `
            <button class="btn-advance-status" data-order-id="${order.id}" data-next-status="PREPARING" style="width: 100%; background-color: #2563EB; color: white; border: none; padding: 10px; border-radius: var(--radius-sm); font-weight: 700; cursor: pointer; transition: opacity 0.2s;">
                🔥 Start Cooking (Prepare)
            </button>
        `;
    } else if (order.status === "PREPARING") {
        actionButtonHtml = `
            <button class="btn-advance-status" data-order-id="${order.id}" data-next-status="OUT_FOR_DELIVERY" style="width: 100%; background-color: #7C3AED; color: white; border: none; padding: 10px; border-radius: var(--radius-sm); font-weight: 700; cursor: pointer; transition: opacity 0.2s;">
                🛵 Dispatch Driver (Out for Delivery)
            </button>
        `;
    } else if (order.status === "OUT_FOR_DELIVERY") {
        actionButtonHtml = `
            <button class="btn-advance-status" data-order-id="${order.id}" data-next-status="DELIVERED" style="width: 100%; background-color: #16A34A; color: white; border: none; padding: 10px; border-radius: var(--radius-sm); font-weight: 700; cursor: pointer; transition: opacity 0.2s;">
                ✅ Confirm Delivered
            </button>
        `;
    } else {
        actionButtonHtml = `
            <div style="text-align: center; font-size: 0.85rem; font-weight: 700; color: #166534; background: #DCFCE7; padding: 8px; border-radius: var(--radius-sm);">
                ✔ Completed
            </div>
        `;
    }

    return `
        <div class="checkout-card" style="background: white; border: 1px solid var(--border); border-radius: var(--radius-md); padding: 18px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: var(--shadow-sm);">
            <div>
                <!-- Header -->
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid var(--border);">
                    <div>
                        <span style="font-weight: 800; font-size: 1.15rem; color: var(--text-main);">Order #${order.id}</span>
                        <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 2px;">Received at ${orderDate}</div>
                    </div>
                    <span class="status-pill ${statusClass}">${statusDisplay}</span>
                </div>

                <!-- Customer Details -->
                <div style="font-size: 0.86rem; color: var(--text-main); margin-bottom: 12px; display: flex; flex-direction: column; gap: 3px;">
                    <div><strong>Customer:</strong> ${order.customer_name} (${order.customer_phone})</div>
                    <div><strong>Address:</strong> ${order.delivery_address}</div>
                </div>

                <!-- Items Ticket -->
                <div style="background: #F8FAFC; border-radius: var(--radius-sm); padding: 10px 12px; margin-bottom: 14px;">
                    ${itemsSummary}
                </div>
            </div>

            <!-- Total & Next Stage Action -->
            <div>
                <div style="display: flex; justify-content: space-between; font-weight: 800; font-size: 1.05rem; margin-bottom: 12px; border-top: 1px dashed var(--border); padding-top: 8px;">
                    <span>Total Amount:</span>
                    <span>$${Number(order.total_amount).toFixed(2)}</span>
                </div>
                ${actionButtonHtml}
            </div>
        </div>
    `;
}

// Attach click listeners to all stage advance buttons
function attachTicketActionListeners() {
    document.querySelectorAll(".btn-advance-status").forEach(btn => {
        btn.addEventListener("click", async () => {
            const orderId = btn.dataset.orderId;
            const nextStatus = btn.dataset.nextStatus;

            btn.disabled = true;
            btn.textContent = "Updating...";

            try {
                await updateOrderStatus(orderId, nextStatus);
                // Reload tickets to reflect the change
                loadAdminOrders();
            } catch (error) {
                alert(`Failed to update order status: ${error.message}`);
                btn.disabled = false;
            }
        });
    });
}


/* =============================================================
   4. LOAD & RENDER MENU INVENTORY TABLE
   ============================================================= */

async function loadAdminInventory() {
    const container = document.getElementById("admin-inventory-table-container");
    if (!container) return;

    container.innerHTML = `<div class="loading-state"><p>Loading dishes from database...</p></div>`;

    try {
        const dishes = await getMenuItems();

        if (dishes.length === 0) {
            container.innerHTML = `<p>No dishes found.</p>`;
            return;
        }

        const tableRows = dishes.map(dish => {
            const stockStatusPill = dish.is_available
                ? `<span style="background: #DCFCE7; color: #166534; padding: 4px 10px; border-radius: 999px; font-size: 0.78rem; font-weight: 700;">In Stock</span>`
                : `<span style="background: #FEF2F2; color: #991B1B; padding: 4px 10px; border-radius: 999px; font-size: 0.78rem; font-weight: 700;">Out of Stock</span>`;

            const toggleButtonText = dish.is_available ? "Mark Out of Stock" : "Mark Available";
            const toggleButtonStyle = dish.is_available
                ? "background: #FEF2F2; color: #991B1B; border: 1px solid #FCA5A5;"
                : "background: #F0FDF4; color: #166534; border: 1px solid #BBF7D0;";

            return `
                <tr style="border-bottom: 1px solid var(--border);">
                    <td style="padding: 12px 14px; display: flex; align-items: center; gap: 12px;">
                        <img src="${dish.image_url || 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=100'}" alt="${dish.name}" style="width: 48px; height: 48px; border-radius: 8px; object-fit: cover;">
                        <div>
                            <div style="font-weight: 700; color: var(--text-main); font-size: 0.95rem;">${dish.name}</div>
                            <small style="color: var(--text-muted);">${dish.is_veg ? '🌿 Veg' : '🥩 Non-Veg'}</small>
                        </div>
                    </td>
                    <td style="padding: 12px 14px; font-weight: 700; font-size: 0.95rem;">
                        $${Number(dish.price).toFixed(2)}
                    </td>
                    <td style="padding: 12px 14px;">
                        ${stockStatusPill}
                    </td>
                    <td style="padding: 12px 14px; text-align: right;">
                        <button class="btn-toggle-stock" data-item-id="${dish.id}" style="${toggleButtonStyle} padding: 6px 14px; border-radius: var(--radius-sm); font-size: 0.82rem; font-weight: 700; cursor: pointer; transition: all 0.2s;">
                            ${toggleButtonText}
                        </button>
                    </td>
                </tr>
            `;
        }).join("");

        container.innerHTML = `
            <table style="width: 100%; border-collapse: collapse; text-align: left;">
                <thead>
                    <tr style="border-bottom: 2px solid var(--border); color: var(--text-muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px;">
                        <th style="padding: 10px 14px;">Dish</th>
                        <th style="padding: 10px 14px;">Price</th>
                        <th style="padding: 10px 14px;">Current Status</th>
                        <th style="padding: 10px 14px; text-align: right;">Quick Action</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
            </table>
        `;

        // Attach event listeners to toggle stock buttons
        document.querySelectorAll(".btn-toggle-stock").forEach(btn => {
            btn.addEventListener("click", async () => {
                const itemId = btn.dataset.itemId;
                btn.disabled = true;
                btn.textContent = "Updating...";

                try {
                    await toggleDishStock(itemId);
                    // Reload table to reflect new stock state
                    loadAdminInventory();
                } catch (error) {
                    alert(`Failed to toggle dish stock: ${error.message}`);
                    btn.disabled = false;
                }
            });
        });

    } catch (error) {
        console.error("Failed to load inventory:", error);
        container.innerHTML = `<p style="color: red;">Failed to load inventory: ${error.message}</p>`;
    }
}