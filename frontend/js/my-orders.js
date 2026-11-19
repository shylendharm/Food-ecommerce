/* =============================================================
   CUSTOMER PAST ORDERS CONTROLLER (frontend/js/my-orders.js)
   Fetches and renders order history for the authenticated customer.
   ============================================================= */

document.addEventListener("DOMContentLoaded", () => {
    loadCustomerOrders();
});


async function loadCustomerOrders() {
    const container = document.getElementById("orders-list-container");
    const countLabel = document.getElementById("orders-count-label");
    if (!container) return;

    // 1. Guard Clause: Must be logged in to view order history
    if (!isAuthenticated()) {
        container.innerHTML = `
            <div class="empty-cart-state" style="padding: 60px 20px; text-align: center; background: white; border-radius: var(--radius-md); border: 1px solid var(--border);">
                <span class="empty-icon" style="font-size: 3rem;">🔒</span>
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

        // Update count label
        if (countLabel) {
            countLabel.textContent = `${orders.length} ${orders.length === 1 ? "order" : "orders"} found`;
        }

        // 3. Handle Empty State (No orders yet)
        if (orders.length === 0) {
            container.innerHTML = `
                <div class="empty-cart-state" style="padding: 60px 20px; text-align: center; background: white; border-radius: var(--radius-md); border: 1px solid var(--border);">
                    <span class="empty-icon" style="font-size: 3rem;">🍽️</span>
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
        console.error("Failed to load customer orders:", error);
        container.innerHTML = `
            <div style="background: #FEF2F2; border: 1px solid #FCA5A5; color: #991B1B; padding: 20px; border-radius: var(--radius-md); text-align: center;">
                <p><strong>Failed to load orders:</strong> ${error.message}</p>
                <button onclick="loadCustomerOrders()" class="btn-login" style="margin: 12px auto 0; background: white;">Try Again</button>
            </div>
        `;
        if (countLabel) countLabel.textContent = "Error loading";
    }
}


/**
 * Helper to generate HTML for a single order card
 */
function renderOrderCard(order) {
    // Format timestamp nicely (e.g., Nov 19, 2026, 03:00 PM)
    const orderDate = new Date(order.created_at).toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "numeric",
        minute: "2-digit",
        hour12: true
    });

    // Format status CSS class name (e.g. status-out_for_delivery)
    const statusClass = `status-${order.status.toLowerCase()}`;
    const statusDisplay = order.status.replace(/_/g, " ");

    // Build items summary rows
    const itemsHtml = order.items.map(item => `
        <div style="display: flex; justify-content: space-between; font-size: 0.92rem; padding: 4px 0; color: var(--text-main);">
            <span>${item.quantity} × ${item.item_name_snapshot}</span>
            <span style="font-weight: 600;">$${(Number(item.price_per_unit) * item.quantity).toFixed(2)}</span>
        </div>
    `).join("");

    return `
        <article class="checkout-card" style="background: white; border: 1px solid var(--border); border-radius: var(--radius-md); padding: 20px; box-shadow: var(--shadow-sm);">
            
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

            <!-- Card Footer: Total Amount, Payment Method, and Track Button -->
            <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 10px;">
                <div>
                    <span style="font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; display: block;">Total Paid (${order.payment_method})</span>
                    <span style="font-size: 1.25rem; font-weight: 800; color: var(--text-main);">$${Number(order.total_amount).toFixed(2)}</span>
                </div>

                <a href="tracking.html?order_id=${order.id}" class="btn-login" style="background-color: var(--primary); color: white; border-color: var(--primary); text-decoration: none; padding: 8px 18px;">
                    <span>Track Live</span>
                    <span>→</span>
                </a>
            </div>

        </article>
    `;
}