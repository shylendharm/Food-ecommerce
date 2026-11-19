/* =============================================================
   CHECKOUT & ORDER SUBMISSION CONTROLLER (frontend/js/checkout.js)
   Validates delivery info, auto-fills logged-in customer data,
   submits order to FastAPI, and redirects to live tracking.
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

  // 3. Auto-fill form if the customer is already logged in
  autoFillUserDetails();

  // 4. Listen for form submission when user clicks "Confirm & Place Order"
  const form = document.getElementById("checkout-order-form");
  if (form) {
    form.addEventListener("submit", handleOrderSubmit);
  }
});


/* =============================================================
   1. AUTO-FILL LOGGED-IN CUSTOMER DATA
   ============================================================= */

function autoFillUserDetails() {
  // If not logged in, leave inputs empty for guest checkout
  if (!isAuthenticated()) return;

  const user = getStoredUser();
  if (!user) return;

  const nameInput = document.getElementById("cust-name");
  const emailInput = document.getElementById("cust-email");
  const phoneInput = document.getElementById("cust-phone");

  // Auto-fill values from the stored user profile
  if (nameInput && user.name) nameInput.value = user.name;
  if (emailInput && user.email) emailInput.value = user.email;
  if (phoneInput && user.phone) phoneInput.value = user.phone;

  // Display a reassuring banner telling the customer the order is linked to their account
  const cardHeader = document.querySelector(".checkout-form-section .checkout-card h3");
  if (cardHeader) {
    const badge = document.createElement("div");
    badge.style.cssText = "background: #F0FDF4; border: 1px solid #BBF7D0; color: #166534; padding: 10px 14px; border-radius: 8px; font-size: 0.86rem; font-weight: 600; margin-bottom: 18px; display: flex; align-items: center; gap: 8px;";
    badge.innerHTML = `<span>👤</span><span>Logged in as <strong>${user.name}</strong> (${user.email}). This order will be linked to your account!</span>`;
    cardHeader.insertAdjacentElement("afterend", badge);
  }
}


/* =============================================================
   2. RENDER ORDER SUMMARY
   ============================================================= */

function renderCheckoutSummary() {
  const itemsContainer = document.getElementById("checkout-items-list");
  const subtotalEl = document.getElementById("checkout-subtotal");
  const totalEl = document.getElementById("checkout-total");
  const btnTotalEl = document.getElementById("checkout-btn-total");

  if (!itemsContainer) return;

  const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  const formattedTotal = `$${subtotal.toFixed(2)}`;

  if (subtotalEl) subtotalEl.textContent = formattedTotal;
  if (totalEl) totalEl.textContent = formattedTotal;
  if (btnTotalEl) btnTotalEl.textContent = formattedTotal;

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
   3. HANDLE FORM SUBMISSION & POST TO BACKEND
   ============================================================= */

async function handleOrderSubmit(e) {
  e.preventDefault();

  const submitBtn = document.getElementById("submit-order-btn");

  const nameInput = document.getElementById("cust-name").value.trim();
  const emailInput = document.getElementById("cust-email").value.trim();
  const phoneInput = document.getElementById("cust-phone").value.trim();
  const addressInput = document.getElementById("cust-address").value.trim();

  const paymentMethodInput = document.querySelector('input[name="payment_method"]:checked');
  const paymentMethod = paymentMethodInput ? paymentMethodInput.value : "COD";

  if (!nameInput || !emailInput || !phoneInput || !addressInput) {
    alert("Please fill in all required delivery fields.");
    return;
  }

  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span>Placing order in kitchen...</span>`;
  }

  try {
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

    // submitOrder automatically includes the Bearer JWT token if logged in!
    const createdOrder = await submitOrder(orderPayload);

    console.log("✅ Order created successfully! ID:", createdOrder.id);

    // Clear cart
    cart = [];
    saveCartToStorage();

    // Redirect to tracking page
    window.location.href = `tracking.html?order_id=${createdOrder.id}`;

  } catch (error) {
    console.error("Order submission failed:", error);
    alert(`Failed to place order: ${error.message}`);

    if (submitBtn) {
      submitBtn.disabled = false;
      renderCheckoutSummary();
    }
  }
}