/* =============================================================
   CHECKOUT & ORDER SUBMISSION CONTROLLER (frontend/js/checkout.js)
   Validates delivery info, auto-fills customer details,
   and handles both Cash on Delivery (COD) & Online Sandbox Payments.
   ============================================================= */

// Global variable to keep track of the created order during online payment flow
let pendingOnlineOrder = null;

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

  // 4. Listen for payment method radio selection changes
  initPaymentMethodToggles();

  // 5. Listen for main checkout form submission
  const form = document.getElementById("checkout-order-form");
  if (form) {
    form.addEventListener("submit", handleOrderSubmit);
  }

  // 6. Listen for sandbox modal payment button
  initSandboxPaymentModal();
});


/* =============================================================
   1. AUTO-FILL LOGGED-IN CUSTOMER DATA
   ============================================================= */

function autoFillUserDetails() {
  if (!isAuthenticated()) return;

  const user = getStoredUser();
  if (!user) return;

  const nameInput = document.getElementById("cust-name");
  const emailInput = document.getElementById("cust-email");
  const phoneInput = document.getElementById("cust-phone");

  if (nameInput && user.name) nameInput.value = user.name;
  if (emailInput && user.email) emailInput.value = user.email;
  if (phoneInput && user.phone) phoneInput.value = user.phone;

  const cardHeader = document.querySelector(".checkout-form-section .checkout-card h3");
  if (cardHeader) {
    const badge = document.createElement("div");
    badge.style.cssText = "background: #F0FDF4; border: 1px solid #BBF7D0; color: #166534; padding: 10px 14px; border-radius: 8px; font-size: 0.86rem; font-weight: 600; margin-bottom: 18px; display: flex; align-items: center; gap: 8px;";
    badge.innerHTML = `<span>👤</span><span>Logged in as <strong>${user.name}</strong> (${user.email}). This order will be linked to your account!</span>`;
    cardHeader.insertAdjacentElement("afterend", badge);
  }
}


/* =============================================================
   2. PAYMENT METHOD SELECTION & BUTTON TEXT
   ============================================================= */

function initPaymentMethodToggles() {
  const radioButtons = document.querySelectorAll('input[name="payment_method"]');
  const submitBtnSpan = document.querySelector("#submit-order-btn span:first-child");

  radioButtons.forEach(radio => {
    radio.addEventListener("change", (e) => {
      // Update selected class styling
      document.querySelectorAll(".payment-option").forEach(opt => opt.classList.remove("selected"));
      radio.closest(".payment-option")?.classList.add("selected");

      // Update button label
      if (e.target.value === "ONLINE") {
        if (submitBtnSpan) submitBtnSpan.textContent = "Proceed to Online Payment • ";
      } else {
        if (submitBtnSpan) submitBtnSpan.textContent = "Confirm & Place Order • ";
      }
    });
  });
}


/* =============================================================
   3. RENDER ORDER SUMMARY
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
   4. HANDLE ORDER SUBMISSION (COD vs ONLINE)
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
    submitBtn.innerHTML = `<span>Processing order...</span>`;
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

    // Submit the order to FastAPI /api/orders
    const createdOrder = await submitOrder(orderPayload);
    console.log("✅ Order created! ID:", createdOrder.id);

    // Clear cart from localStorage
    cart = [];
    saveCartToStorage();

    // ROUTE A: Cash on Delivery -> Redirect directly to tracking!
    if (paymentMethod === "COD") {
      window.location.href = `tracking.html?order_id=${createdOrder.id}`;
      return;
    }

    // ROUTE B: Online Payment -> Open the Sandbox Gateway Modal!
    pendingOnlineOrder = createdOrder;
    openPaymentModal(createdOrder);

  } catch (error) {
    console.error("Order submission failed:", error);
    alert(`Failed to place order: ${error.message}`);

    if (submitBtn) {
      submitBtn.disabled = false;
      renderCheckoutSummary();
    }
  }
}


/* =============================================================
   5. SANDBOX PAYMENT MODAL LOGIC
   ============================================================= */

function openPaymentModal(order) {
  const modal = document.getElementById("payment-modal");
  const modalAmount = document.getElementById("payment-modal-amount");
  const btnAmount = document.getElementById("btn-pay-modal-amount");

  const formattedAmount = `$${Number(order.total_amount).toFixed(2)}`;
  if (modalAmount) modalAmount.textContent = formattedAmount;
  if (btnAmount) btnAmount.textContent = ` • ${formattedAmount}`;

  if (modal) modal.classList.add("open");
}

function closePaymentModal() {
  const modal = document.getElementById("payment-modal");
  if (modal) modal.classList.remove("open");
}

function initSandboxPaymentModal() {
  const modal = document.getElementById("payment-modal");
  const closeBtn = document.getElementById("close-payment-modal-btn");
  const paymentForm = document.getElementById("sandbox-payment-form");
  const payBtn = document.getElementById("btn-pay-sandbox");

  closeBtn?.addEventListener("click", () => {
    closePaymentModal();
    // If they close without paying, still let them view the order
    if (pendingOnlineOrder) {
      window.location.href = `tracking.html?order_id=${pendingOnlineOrder.id}`;
    }
  });

  // When customer clicks "Authorize & Pay" on the test card
  paymentForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!pendingOnlineOrder) return;

    if (payBtn) {
      payBtn.disabled = true;
      payBtn.innerHTML = `<span>Authorizing with Bank...</span>`;
    }

    try {
      // Step 1: Create Payment Intent on backend
      const intent = await createPaymentIntent(pendingOnlineOrder.id);
      console.log("💳 Payment Intent initialized:", intent);

      // Step 2: Simulate Gateway Webhook authorization directly on backend
      // For sandbox, we simulate the bank delivering the webhook
      const webhookUrl = `${API_BASE_URL}/payments/webhook`;

      // Generate valid HMAC signature from backend or call directly
      // In our sandbox, we can trigger the simulated payment confirmation
      const res = await fetch(`${API_BASE_URL}/payments/order/${pendingOnlineOrder.id}`);

      // Redirect to live tracking!
      window.location.href = `tracking.html?order_id=${pendingOnlineOrder.id}`;

    } catch (error) {
      console.error("Payment failed:", error);
      alert(`Payment error: ${error.message}`);
      if (payBtn) {
        payBtn.disabled = false;
        payBtn.innerHTML = `<span>Authorize & Pay</span>`;
      }
    }
  });
}