/* =============================================================
   CHECKOUT & ORDER SUBMISSION CONTROLLER (frontend/js/checkout.js)
   Validates delivery info, calls POST /api/orders, and redirects to tracking.
   ============================================================= */
document.addEventListener("DOMContentLoaded", () => {
    // 1. Guard Clause: If the cart is empty, redirect back to menu!
    if (!cart || cart.length === 0) {
        alert("Your shopping cart is empty! Redirecting you to the menu.");
        window.location.href = "index.html";
        return;
    }
    // 2. Render the order summary on the right side
    renderCheckoutSummary();
    // 3. Listen for form submission when user clicks "Confirm & Place Order"
    const form = document.getElementById("checkout-order-form");
    if (form) {
        form.addEventListener("submit", handleOrderSubmit);
    }
});
/* =============================================================
   1. RENDER ORDER SUMMARY
   ============================================================= */
function renderCheckoutSummary() {
    const itemsContainer = document.getElementById("checkout-items-list");
    const subtotalEl = document.getElementById("checkout-subtotal");
    const totalEl = document.getElementById("checkout-total");
    const btnTotalEl = document.getElementById("checkout-btn-total");
    if (!itemsContainer) return;
    // Calculate totals
    const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const formattedTotal = `$${subtotal.toFixed(2)}`;
    // Display the total price in all 3 price slots
    if (subtotalEl) subtotalEl.textContent = formattedTotal;
    if (totalEl) totalEl.textContent = formattedTotal;
    if (btnTotalEl) btnTotalEl.textContent = formattedTotal;
    // Build the list of ordered dishes
    itemsContainer.innerHTML = cart.map(item => `
    <div class="checkout-item-row">
      <div class="checkout-item-info">
        <h4>${item.name}</h4>
        <span>Qty: ${item.quantity} × $${item.price.toFixed(2)}</span>
      </div>
      <span class="checkout-item-price">$${(item.price * item.quantity).toFixed(2)}</span>
    </div>
  `).join("");
}