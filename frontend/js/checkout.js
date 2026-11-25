// Checkout page controller and order submission

// Key name used to remember delivery address across sessions
const SAVED_ADDRESS_KEY = "foodexpress_saved_address";

// In-memory holder for the validated checkout payload while payment modal is open
let pendingOrderPayload = null;

document.addEventListener("DOMContentLoaded", () => {
  // 1. Guard Clause A: If the cart is empty, notify cleanly and redirect back to menu
  if (!cart || cart.length === 0) {
    if (typeof showAppAlert === "function") {
      showAppAlert({
        title: "Your Cart is Empty",
        message: "Your shopping basket is currently empty. Redirecting you to the menu to pick your favorite dishes.",
        type: "info",
        tag: "Order Notice",
        confirmText: "Browse Menu"
      }).then(() => {
        window.location.href = "index.html";
      });
    } else {
      window.location.href = "index.html";
    }
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


// Pre-fill user profile and delivery address

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
}


// Payment method selection

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


// Order summary and calculation

function renderCheckoutSummary() {
  const itemsContainer = document.getElementById("checkout-items-list");
  const subtotalEl = document.getElementById("checkout-subtotal");
  const totalEl = document.getElementById("checkout-total");
  const btnTotalEl = document.getElementById("checkout-btn-total");

  if (!itemsContainer) return;

  const subtotal = cart.reduce((sum, item) => {
    const itemPrice = parseFloat(item.price) || 0;
    const itemQty = parseInt(item.quantity, 10) || 0;
    return sum + (itemPrice * itemQty);
  }, 0);

  const formattedTotal = `$${subtotal.toFixed(2)}`;
  if (subtotalEl) subtotalEl.textContent = formattedTotal;
  if (totalEl) totalEl.textContent = formattedTotal;
  if (btnTotalEl) btnTotalEl.textContent = formattedTotal;

  itemsContainer.innerHTML = cart.map(item => `
    <div class="checkout-item-row">
      <div class="checkout-item-info">
        <h4>${escapeCheckoutText(item.name)}</h4>
        <span>Qty: ${item.quantity} × $${(parseFloat(item.price) || 0).toFixed(2)}</span>
      </div>
      <span class="checkout-item-price">$${((parseFloat(item.price) || 0) * (parseInt(item.quantity, 10) || 0)).toFixed(2)}</span>
    </div>
  `).join("");
}

function escapeCheckoutText(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}


// Order placement handler

async function handleOrderSubmit(e) {
  e.preventDefault();

  const name = document.getElementById("cust-name")?.value.trim();
  const email = document.getElementById("cust-email")?.value.trim();
  const phone = document.getElementById("cust-phone")?.value.trim();
  const address = document.getElementById("cust-address")?.value.trim();
  const paymentMethodInput = document.querySelector('input[name="payment_method"]:checked');
  const paymentMethod = paymentMethodInput ? paymentMethodInput.value : "COD";

  // Validate required delivery details
  if (!name || !email || !phone || !address) {
    if (typeof showAppAlert === "function") {
      await showAppAlert({
        title: "Incomplete Details",
        message: "Please fill in all required delivery fields (name, email, phone, and delivery address).",
        type: "warning",
        tag: "Required Field"
      });
    }
    return;
  }

  // Validate phone number format (10-15 digits)
  const phoneClean = phone.replace(/[\s\-\(\)\+]/g, "");
  if (phoneClean.length < 10 || phoneClean.length > 15 || isNaN(phoneClean)) {
    if (typeof showAppAlert === "function") {
      await showAppAlert({
        title: "Invalid Phone Number",
        message: "Please provide a valid contact phone number consisting of 10 to 15 digits.",
        type: "warning",
        tag: "Validation"
      });
    }
    return;
  }

  // Remember address in local storage for subsequent visits
  localStorage.setItem(SAVED_ADDRESS_KEY, address);

  // Construct standard order payload strictly matching backend OrderCreate schema
  const orderPayload = {
    customer_name: name,
    customer_email: email,
    customer_phone: phone,
    delivery_address: address,
    payment_method: paymentMethod,
    items: cart.map(item => ({
      menu_item_id: parseInt(item.id, 10),
      quantity: parseInt(item.quantity, 10)
    }))
  };

  // ROUTE A: Cash on Delivery (COD) -> Commit order immediately
  if (paymentMethod === "COD") {
    const submitBtn = document.getElementById("submit-order-btn");
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<span>Placing Order...</span>`;
    }

    try {
      const createdOrder = await submitOrder(orderPayload);
      console.log("[Checkout] COD Order created successfully. ID:", createdOrder.id);

      // Clear user-scoped cart
      cart = [];
      if (typeof saveCartToStorage === "function") saveCartToStorage();

      // Redirect immediately to live tracking
      window.location.href = `tracking.html?order_id=${createdOrder.id}`;
    } catch (error) {
      console.error("[Checkout] Order placement failed:", error);
      if (typeof showAppAlert === "function") {
        await showAppAlert({
          title: "Order Placement Failed",
          message: error.message || "An unexpected error occurred while transmitting your order. Please try again.",
          type: "danger",
          tag: "Server Error"
        });
      }
      if (submitBtn) {
        submitBtn.disabled = false;
        renderCheckoutSummary();
      }
    }
    return;
  }

  // ROUTE B: Online Payment -> Open Sandbox Modal WITHOUT creating an order yet
  pendingOrderPayload = orderPayload;
  openPaymentModal();
}


// Mock payment gateway modal

function openPaymentModal() {
  const modal = document.getElementById("payment-modal");
  const modalAmount = document.getElementById("payment-modal-amount");
  const btnAmount = document.getElementById("btn-pay-modal-amount");

  const subtotal = cart.reduce((sum, item) => {
    const itemPrice = parseFloat(item.price) || 0;
    const itemQty = parseInt(item.quantity, 10) || 0;
    return sum + (itemPrice * itemQty);
  }, 0);

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

  // Authorize & Pay: Commit the order to MySQL and process payment
  paymentForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!pendingOrderPayload) return;

    if (payBtn) {
      payBtn.disabled = true;
      payBtn.innerHTML = `<span>Authorizing Payment...</span>`;
    }

    try {
      // Create order record
      const createdOrder = await submitOrder(pendingOrderPayload);
      console.log("[Checkout] Online Order committed to MySQL. ID:", createdOrder.id);

      // Initiate payment intent
      await createPaymentIntent(createdOrder.id);

      // Clear cart
      cart = [];
      if (typeof saveCartToStorage === "function") saveCartToStorage();

      // Step 4: Navigate to live GPS tracking
      window.location.href = `tracking.html?order_id=${createdOrder.id}`;

    } catch (error) {
      console.error("[Checkout] Payment authorization failed:", error);
      if (typeof showAppAlert === "function") {
        await showAppAlert({
          title: "Payment Authorization Failed",
          message: error.message || "The sandbox transaction could not be authorized. Please verify details and try again.",
          type: "danger",
          tag: "Payment Gateway"
        });
      }
      if (payBtn) {
        payBtn.disabled = false;
        payBtn.innerHTML = `<span>Authorize & Pay</span>`;
      }
    }
  });
}