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


/* =============================================================
   2. HANDLE FORM SUBMISSION & POST TO BACKEND
   ============================================================= */

async function handleOrderSubmit(e) {
  // Crucial: Stop the browser from doing a default 1995 page-reload!
  e.preventDefault();

  const submitBtn = document.getElementById("submit-order-btn");

  // Read the form values typed by the human customer
  const nameInput = document.getElementById("cust-name").value.trim();
  const emailInput = document.getElementById("cust-email").value.trim();
  const phoneInput = document.getElementById("cust-phone").value.trim();
  const addressInput = document.getElementById("cust-address").value.trim();

  // Read the selected radio button for payment method (e.g., "COD")
  const paymentMethodInput = document.querySelector('input[name="payment_method"]:checked');
  const paymentMethod = paymentMethodInput ? paymentMethodInput.value : "COD";

  // Simple validation
  if (!nameInput || !emailInput || !phoneInput || !addressInput) {
    alert("Please fill in all required delivery fields.");
    return;
  }

  // Disable button and show loading spinner so customer doesn't double-click!
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span>Placing order in kitchen...</span>`;
  }

  try {
    // Bundle the payload to match our Python OrderCreate schema perfectly!
    const orderPayload = {
      customer_name: nameInput,
      customer_email: emailInput,
      customer_phone: phoneInput,
      delivery_address: addressInput,
      payment_method: paymentMethod,
      items: cart.map(item => ({
        menu_item_id: item.id,
        quantity: item.quantity
      }))
    };

    console.log("🚀 Submitting order payload to backend:", orderPayload);

    // Call POST /api/orders via api.js!
    const createdOrder = await submitOrder(orderPayload);

    console.log("✅ Order created successfully! ID:", createdOrder.id);

    // Clear the cart from localStorage since the order is now placed!
    cart = [];
    saveCartToStorage();

    // Redirect to the live order tracking page with the new order ID!
    window.location.href = `tracking.html?order_id=${createdOrder.id}`;

  } catch (error) {
    console.error("Order submission failed:", error);
    alert(`Failed to place order: ${error.message}`);

    // Re-enable the button so they can fix their details and try again
    if (submitBtn) {
      submitBtn.disabled = false;
      renderCheckoutSummary(); // Restores original button text
    }
  }
}