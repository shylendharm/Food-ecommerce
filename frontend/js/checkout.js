/* =============================================================
   FILE: frontend/js/checkout.js
   CHECKOUT & ORDER SUBMISSION CONTROLLER
   Validates delivery info, auto-hydrates saved customer profile & default
   address, handles COD, and provides resilient, deferred Online Payment flows.
   ============================================================= */

// Key name used to remember delivery address across sessions
const SAVED_ADDRESS_KEY = "foodexpress_saved_address";

// In-memory holder for the validated checkout payload while payment modal is open
let pendingOrderPayload = null;

document.addEventListener("DOMContentLoaded", () => {
  // 1. Guard Clause A: If the cart is empty, redirect back to menu
  if (!cart || cart.length === 0) {
    alert("Your shopping cart is empty. Redirecting you to the menu.");
    window.location.href = "index.html";
    return;
  }

  // 2. Guard Clause B: Mandatory Authentication Gate
  if (typeof isAuthenticated === "function" && !isAuthenticated()) {
    sessionStorage.setItem("post_login_redirect", "checkout.html");
    window.location.href = "login.html";
    return;
  }

  // 3. Render the order summary on the right side
  renderCheckoutSummary();

  // 4. Auto-fill form from user profile and default address
  autoFillUserDetails();

  // 5. Listen for payment method radio selection changes
  initPaymentMethodToggles();

  // 6. Listen for main checkout form submission
  const form = document.getElementById("checkout-order-form");
  if (form) {
    form.addEventListener("submit", handleOrderSubmit);
  }

  // 7. Listen for sandbox modal payment and abort actions
  initSandboxPaymentModal();
});


/* =============================================================
   1. AUTO-FILL LOGGED-IN CUSTOMER DATA & DEFAULT ADDRESS
   ============================================================= */

function autoFillUserDetails() {
  if (typeof isAuthenticated !== "function" || !isAuthenticated()) return;

  const user = getStoredUser();
  if (!user) return;

  const nameInput = document.getElementById("cust-name");
  const emailInput = document.getElementById("cust-email");
  const phoneInput = document.getElementById("cust-phone");
  const addressInput = document.getElementById("cust-address");

  // Auto-fill authenticated profile identity
  if (nameInput && user.name) nameInput.value = user.name;
  if (emailInput && user.email) emailInput.value = user.email;
  if (phoneInput && user.phone) phoneInput.value = user.phone;

  // Auto-populate default address from profile while allowing per-order edits
  const effectiveAddress = user.default_address || localStorage.getItem(SAVED_ADDRESS_KEY) || "";
  if (addressInput && effectiveAddress && !addressInput.value) {
    addressInput.value = effectiveAddress;
  }

  // Visual badge confirming authenticated order linkage
  const cardHeader = document.querySelector(".checkout-form-section .checkout-card h3");
  if (cardHeader && !document.getElementById("auth-linked-badge")) {
    const badge = document.createElement("div");
    badge.id = "auth-linked-badge";
    badge.style.cssText = "background: #111827; border: 1px solid #1F2937; color: #E2E8F0; padding: 12px 14px; border-radius: 8px; font-size: 0.84rem; font-weight: 500; margin-bottom: 20px; line-height: 1.4;";
    badge.innerHTML = `Ordering as <strong>${user.name}</strong> (${user.email}). Default address auto-populated from profile.`;
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
      document.querySelectorAll(".payment-option").forEach(opt => opt.classList.remove("selected"));
      radio.closest(".payment-option")?.classList.add("selected");

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
   4. HANDLE ORDER SUBMISSION (COD vs DEFERRED ONLINE)
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

  // Cache entered address for immediate browser recall
  localStorage.setItem(SAVED_ADDRESS_KEY, addressInput);

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

  // ROUTE A: Cash on Delivery -> Commit order immediately to MySQL
  if (paymentMethod === "COD") {
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<span>Placing order...</span>`;
    }

    try {
      const createdOrder = await submitOrder(orderPayload);
      console.log("[Checkout] COD Order created. ID:", createdOrder.id);

      cart = [];
      if (typeof saveCartToStorage === "function") saveCartToStorage();
      window.location.href = `tracking.html?order_id=${createdOrder.id}`;
    } catch (error) {
      console.error("[Checkout] COD Order failed:", error);
      alert(`Failed to place order: ${error.message}`);
      if (submitBtn) {
        submitBtn.disabled = false;
        renderCheckoutSummary();
      }
    }
    return;
  }

  // ROUTE B: Online Payment -> Open Sandbox Modal WITHOUT creating an order yet!
  pendingOrderPayload = orderPayload;
  openPaymentModal();
}


/* =============================================================
   5. SANDBOX PAYMENT MODAL LOGIC (Deferred Order Creation)
   ============================================================= */

function openPaymentModal() {
  const modal = document.getElementById("payment-modal");
  const modalAmount = document.getElementById("payment-modal-amount");
  const btnAmount = document.getElementById("btn-pay-modal-amount");

  const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  const formattedTotal = `$${subtotal.toFixed(2)}`;

  if (modalAmount) modalAmount.textContent = formattedTotal;
  if (btnAmount) btnAmount.textContent = ` • ${formattedTotal}`;

  if (modal) modal.classList.add("open");
}

function closePaymentModal() {
  const modal = document.getElementById("payment-modal");
  if (modal) modal.classList.remove("open");

  // Clear in-memory pending payload on cancel
  pendingOrderPayload = null;

  // Restore main submit button so customer can retry or choose COD
  const submitBtn = document.getElementById("submit-order-btn");
  if (submitBtn) {
    submitBtn.disabled = false;
    renderCheckoutSummary();
  }
}

function initSandboxPaymentModal() {
  const modal = document.getElementById("payment-modal");
  const closeBtn = document.getElementById("close-payment-modal-btn");
  const paymentForm = document.getElementById("sandbox-payment-form");
  const payBtn = document.getElementById("btn-pay-sandbox");

  // Clicking cancel icon aborts cleanly: NO order created, NO redirection
  closeBtn?.addEventListener("click", () => {
    closePaymentModal();
  });

  // Clicking outside modal aborts cleanly
  modal?.addEventListener("click", (e) => {
    if (e.target === modal) {
      closePaymentModal();
    }
  });

  // Authorize & Pay: NOW we commit the order to MySQL and process the payment
  paymentForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!pendingOrderPayload) return;

    if (payBtn) {
      payBtn.disabled = true;
      payBtn.innerHTML = `<span>Authorizing Payment...</span>`;
    }

    try {
      // Step 1: Commit order to MySQL now that customer authorized payment
      const createdOrder = await submitOrder(pendingOrderPayload);
      console.log("[Checkout] Online Order committed to MySQL. ID:", createdOrder.id);

      // Step 2: Initialize Payment Intent with Gateway
      await createPaymentIntent(createdOrder.id);

      // Step 3: Clear shopping cart
      cart = [];
      if (typeof saveCartToStorage === "function") saveCartToStorage();

      // Step 4: Navigate to live GPS tracking
      window.location.href = `tracking.html?order_id=${createdOrder.id}`;

    } catch (error) {
      console.error("[Checkout] Payment authorization failed:", error);
      alert(`Payment authorization failed: ${error.message}`);
      if (payBtn) {
        payBtn.disabled = false;
        payBtn.innerHTML = `<span>Authorize & Pay</span>`;
      }
    }
  });
}