// Order history list and receipts

// In-memory cache of orders for instant 1-click reordering
let currentCustomerOrders = [];

document.addEventListener("DOMContentLoaded", () => {
    loadCustomerOrders();
});


// Fetch order history

async function loadCustomerOrders() {
    const container = document.getElementById("orders-list-container");
    const countLabel = document.getElementById("orders-count-label");
    if (!container) return;

    // 1. Guard Clause: Must be logged in to view order history
    if (!isAuthenticated()) {
        container.innerHTML = `
            <div class="empty-cart-state" style="padding: 60px 20px; text-align: center; background: white; border-radius: var(--radius-md); border: 1px solid var(--border);">
                <h3 style="margin: 14px 0 8px; font-weight: 700;">Please Sign In</h3>
                <p style="color: var(--text-muted); margin-bottom: 20px;">You need to be logged in to view your past orders and receipts.</p>
                <a href="index.html" class="place-order-btn" style="display: inline-block; text-decoration: none; max-width: 200px; margin: 0 auto;">Go to Storefront</a>
            </div>
        `;
        if (countLabel) countLabel.textContent = "Login required";
        return;
    }

    try {
        // 2. Fetch orders from FastAPI /api/orders/my-orders
        const orders = await getMyOrders();
        currentCustomerOrders = orders; // Save in-memory for reorder lookup

        // Update count label
        if (countLabel) {
            countLabel.textContent = `${orders.length} ${orders.length === 1 ? "order" : "orders"} found`;
        }

        // 3. Handle Empty State (No orders yet)
        if (orders.length === 0) {
            container.innerHTML = `
                <div class="empty-cart-state" style="padding: 60px 20px; text-align: center; background: white; border-radius: var(--radius-md); border: 1px solid var(--border);">
                    <h3 style="margin: 14px 0 8px; font-weight: 700;">No Orders Yet</h3>
                    <p style="color: var(--text-muted); margin-bottom: 20px;">You haven't placed any food orders yet. Ready to try something delicious?</p>
                    <a href="index.html" class="place-order-btn" style="display: inline-block; text-decoration: none; max-width: 200px; margin: 0 auto;">Browse Menu</a>
                </div>
            `;
            return;
        }

        // 4. Render the list of order cards
        container.innerHTML = orders.map(order => renderOrderCard(order)).join("");

    } catch (error) {
        console.error("[Orders] Failed to load customer orders:", error);
        container.innerHTML = `
            <div style="background: #FEF2F2; border: 1px solid #FCA5A5; color: #991B1B; padding: 20px; border-radius: var(--radius-md); text-align: center;">
                <p><strong>Failed to load orders:</strong> ${error.message}</p>
                <button onclick="loadCustomerOrders()" class="btn-login" style="margin: 12px auto 0; background: white;">Try Again</button>
            </div>
        `;
        if (countLabel) countLabel.textContent = "Error loading";
    }
}


// Render order card

function renderOrderCard(order) {
    const orderDate = new Date(order.created_at).toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "numeric",
        minute: "2-digit",
        hour12: true
    });

    const statusClass = `status-${order.status.toLowerCase()}`;
    const statusDisplay = order.status.replace(/_/g, " ");

    // Build items snapshot rows
    const itemsHtml = order.items.map(item => `
        <div style="display: flex; justify-content: space-between; font-size: 0.92rem; padding: 4px 0; color: var(--text-main);">
            <span>${item.quantity} × ${item.item_name_snapshot}</span>
            <span style="font-weight: 600;">$${(Number(item.price_per_unit) * item.quantity).toFixed(2)}</span>
        </div>
    `).join("");

    return `
        <article class="checkout-card" style="background: white; border: 1px solid var(--border); border-radius: var(--radius-md); padding: 20px; box-shadow: var(--shadow-sm); margin-bottom: 16px;">
            
            <!-- Card Header: Order ID, Date, and Status Badge -->
            <div style="display: flex; justify-content: space-between; align-items: flex-start; padding-bottom: 14px; border-bottom: 1px solid var(--border); margin-bottom: 14px;">
                <div>
                    <h3 style="font-size: 1.15rem; font-weight: 800; color: var(--text-main); margin-bottom: 2px;">
                        Order #${order.id}
                    </h3>
                    <small style="color: var(--text-muted); font-size: 0.82rem;">Placed on ${orderDate}</small>
                </div>
                <span class="status-pill ${statusClass}">${statusDisplay}</span>
            </div>

            <!-- Ordered Items Snapshot -->
            <div style="background: #F8FAFC; border-radius: var(--radius-sm); padding: 12px 14px; margin-bottom: 14px;">
                ${itemsHtml}
            </div>

            <!-- Card Footer: Total Amount, Payment Method, and Contextual Actions -->
            <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 10px; flex-wrap: wrap; gap: 12px;">
                <div>
                    <span style="font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; display: block;">
                        Total (${order.payment_method})
                    </span>
                    <span style="font-size: 1.25rem; font-weight: 800; color: var(--text-main);">$${Number(order.total_amount).toFixed(2)}</span>
                </div>

                <div style="display: flex; gap: 10px; align-items: center;">
                    ${renderOrderActionButtons(order)}
                </div>
            </div>

        </article>
    `;
}

/**
 * Contextual Action Buttons depending on whether order is Pending, Active, Delivered, or Cancelled
 */
function renderOrderActionButtons(order) {
    const isCancelled = order.status === "CANCELLED";
    const isDelivered = order.status === "DELIVERED";
    const isPending = order.status === "PENDING";
    const isActive = !isCancelled && !isDelivered;

    let trackButtonHtml = "";

    if (isActive) {
        trackButtonHtml = `
            <a href="tracking.html?order_id=${order.id}" class="btn-login" style="background-color: var(--primary); color: white; border-color: var(--primary); text-decoration: none; padding: 8px 18px; display: inline-flex; align-items: center; gap: 7px; font-weight: 700;">
                <span style="width: 8px; height: 8px; background: #86EFAC; border-radius: 50%; display: inline-block;"></span>
                <span>Track Live</span>
                <span>→</span>
            </a>
        `;
    } else if (isDelivered) {
        trackButtonHtml = `
            <a href="tracking.html?order_id=${order.id}" class="btn-login" style="background-color: #F0FDF4; color: #166534; border: 1px solid #BBF7D0; text-decoration: none; padding: 8px 16px; font-weight: 600;">
                <span>View Receipt</span>
            </a>
        `;
    } else {
        trackButtonHtml = `
            <a href="tracking.html?order_id=${order.id}" class="btn-login" style="background-color: #F8FAFC; color: #64748B; border: 1px solid #CBD5E1; text-decoration: none; padding: 8px 16px; font-weight: 600;">
                <span>View Status</span>
            </a>
        `;
    }

    // Cancel Button: Available exclusively when order is PENDING
    const cancelButtonHtml = isPending ? `
        <button id="cancel-btn-${order.id}" onclick="handleCancelFromHistory(${order.id})" class="btn-login" style="background: #FFF1F2; color: #E11D48; border: 1.5px solid #FECDD3; padding: 8px 14px; font-weight: 700; cursor: pointer; display: inline-flex; align-items: center; gap: 5px; transition: all 0.2s ease;">
            <span>Cancel</span>
        </button>
    ` : "";

    // 1-Click Reorder Button: Available on past Delivered or Cancelled orders
    const reorderButtonHtml = (isDelivered || isCancelled) ? `
        <button onclick="handleReorder(${order.id})" class="btn-login" style="background: white; border: 1.5px solid var(--border); color: var(--text-main); padding: 8px 14px; font-weight: 700; cursor: pointer; display: inline-flex; align-items: center; gap: 5px;">
            <span>Reorder</span>
        </button>
    ` : "";

    return `${cancelButtonHtml} ${reorderButtonHtml} ${trackButtonHtml}`;
}


// Reorder items

window.handleReorder = async function (orderId) {
    const order = currentCustomerOrders.find(o => o.id === orderId);
    if (!order || !order.items || order.items.length === 0) {
        await showAppAlert({
            title: "Reorder Notice",
            tag: "Cart",
            message: "Unable to retrieve items for this order.",
            type: "warning"
        });
        return;
    }

    // Load active cart from localStorage
    let activeCart = [];
    try {
        const saved = localStorage.getItem("foodexpress_cart");
        activeCart = saved ? JSON.parse(saved) : [];
    } catch (e) {
        activeCart = [];
    }

    // Hydrate cart with items from the selected past order
    order.items.forEach(item => {
        if (!item.menu_item_id) return;
        const existing = activeCart.find(c => c.id === item.menu_item_id);
        if (existing) {
            existing.quantity += item.quantity;
        } else {
            activeCart.push({
                id: item.menu_item_id,
                name: item.item_name_snapshot,
                price: parseFloat(item.price_per_unit),
                quantity: item.quantity,
                is_veg: true
            });
        }
    });

    localStorage.setItem("foodexpress_cart", JSON.stringify(activeCart));

    await showAppAlert({
        title: "Cart Updated",
        tag: "Reorder",
        message: `Added ${order.items.length} items from Order #${orderId} to your cart.`,
        confirmText: "Go to Menu",
        type: "info"
    });

    window.location.href = "index.html";
};


// Order cancellation

window.handleCancelFromHistory = async function (orderId) {
    // Design System Confirmation Modal
    const confirmed = await showAppConfirm({
        title: "Cancel Order",
        tag: "Order Cancellation",
        message: `Are you sure you want to cancel Order #${orderId}? This action cannot be undone.`,
        confirmText: "Yes, Cancel Order",
        cancelText: "Keep Order",
        isDanger: true
    });

    if (!confirmed) return;

    const btn = document.getElementById(`cancel-btn-${orderId}`);
    if (btn) {
        btn.disabled = true;
        btn.textContent = "Cancelling...";
        btn.style.opacity = "0.6";
        btn.style.cursor = "not-allowed";
    }

    try {
        await cancelOrder(orderId);
        // Refresh the order history list in-place
        await loadCustomerOrders();
    } catch (error) {
        console.error(`[Order History] Failed to cancel Order #${orderId}:`, error);
        await showAppAlert({
            title: "Cancellation Failed",
            tag: "State Machine",
            message: error.message || `Could not cancel Order #${orderId}.`,
            confirmText: "Understand",
            type: "danger"
        });

        if (btn) {
            btn.disabled = false;
            btn.textContent = "Cancel";
            btn.style.opacity = "1";
            btn.style.cursor = "pointer";
        }
    }
};