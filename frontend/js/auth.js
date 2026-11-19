/* =============================================================
   AUTHENTICATION & NAVBAR CONTROLLER (frontend/js/auth.js)
   Manages the login/registration popup modal, form submissions,
   and dynamic user navbar dropdown state across pages.
   ============================================================= */

document.addEventListener("DOMContentLoaded", () => {
    initAuthNavbar();
    initAuthModal();
});


/* =============================================================
   1. NAVBAR STATE CONTROLLER (Sign In vs User Profile)
   ============================================================= */

function initAuthNavbar() {
    const authNavContainer = document.getElementById("auth-nav-container");
    if (!authNavContainer) return;

    if (!isAuthenticated()) {
        // --- 1. GUEST STATE: Render "Sign In" button ---
        authNavContainer.innerHTML = `
            <button id="open-auth-btn" class="btn-login">
                <span>👤</span>
                <span>Sign In</span>
            </button>
        `;

        document.getElementById("open-auth-btn")?.addEventListener("click", () => {
            openAuthModal("login");
        });
    } else {
        // --- 2. LOGGED-IN STATE: Render User Profile Dropdown ---
        const user = getStoredUser();
        const firstName = user?.name ? user.name.split(" ")[0] : "Account";
        const initial = user?.name ? user.name.charAt(0).toUpperCase() : "U";
        const userIsAdmin = isAdmin();

        authNavContainer.innerHTML = `
            <div class="user-menu-container">
                <button id="user-menu-btn" class="user-menu-btn" aria-label="Open User Menu">
                    <span class="user-avatar">${initial}</span>
                    <span>Hi, ${firstName}</span>
                    <span style="font-size: 0.75rem;">▼</span>
                </button>

                <div id="user-dropdown" class="user-dropdown">
                    <div class="dropdown-header">
                        <div class="dropdown-user-name">${user?.name || "Customer"}</div>
                        <div class="dropdown-user-email">${user?.email || ""}</div>
                    </div>

                    <a href="my-orders.html" class="dropdown-item">
                        <span>📦</span>
                        <span>My Orders</span>
                    </a>

                    ${userIsAdmin ? `
                        <a href="admin.html" class="dropdown-item admin-link">
                            <span>🍳</span>
                            <span>Kitchen Portal (Admin)</span>
                        </a>
                    ` : ""}

                    <div class="dropdown-divider"></div>

                    <button id="logout-btn" class="dropdown-item logout">
                        <span>🚪</span>
                        <span>Sign Out</span>
                    </button>
                </div>
            </div>
        `;

        // Toggle dropdown open/close on click
        const menuBtn = document.getElementById("user-menu-btn");
        const dropdown = document.getElementById("user-dropdown");
        const logoutBtn = document.getElementById("logout-btn");

        menuBtn?.addEventListener("click", (e) => {
            e.stopPropagation();
            dropdown?.classList.toggle("show");
        });

        // Close dropdown when clicking anywhere else on the document
        document.addEventListener("click", (e) => {
            if (!dropdown?.contains(e.target) && e.target !== menuBtn) {
                dropdown?.classList.remove("show");
            }
        });

        // Sign out button handler
        logoutBtn?.addEventListener("click", () => {
            logoutUser();
        });
    }
}


/* =============================================================
   2. AUTHENTICATION POPUP MODAL CONTROLLER
   ============================================================= */

function initAuthModal() {
    const modal = document.getElementById("auth-modal");
    if (!modal) return;

    const closeBtn = document.getElementById("close-auth-modal-btn");
    const tabLogin = document.getElementById("tab-login-btn");
    const tabRegister = document.getElementById("tab-register-btn");
    const loginForm = document.getElementById("login-form");
    const registerForm = document.getElementById("register-form");
    const errorBanner = document.getElementById("auth-error-banner");

    // Close modal handlers
    closeBtn?.addEventListener("click", closeAuthModal);
    modal.addEventListener("click", (e) => {
        if (e.target === modal) closeAuthModal();
    });

    // Escape key closes modal
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && modal.classList.contains("open")) {
            closeAuthModal();
        }
    });

    // Tab Switching (Sign In vs Register)
    tabLogin?.addEventListener("click", () => switchAuthTab("login"));
    tabRegister?.addEventListener("click", () => switchAuthTab("register"));

    // Quick 1-Click Demo Fillers
    document.getElementById("demo-customer-btn")?.addEventListener("click", async () => {
        document.getElementById("login-email").value = "alice@example.com";
        document.getElementById("login-password").value = "customer123";
        await handleLoginSubmit("alice@example.com", "customer123");
    });

    document.getElementById("demo-admin-btn")?.addEventListener("click", async () => {
        document.getElementById("login-email").value = "admin@restaurant.com";
        document.getElementById("login-password").value = "admin123";
        await handleLoginSubmit("admin@restaurant.com", "admin123");
    });

    // Sign In form submit
    loginForm?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("login-email").value.trim();
        const password = document.getElementById("login-password").value;
        await handleLoginSubmit(email, password);
    });

    // Create Account form submit
    registerForm?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const name = document.getElementById("reg-name").value.trim();
        const email = document.getElementById("reg-email").value.trim();
        const phone = document.getElementById("reg-phone").value.trim() || null;
        const password = document.getElementById("reg-password").value;

        showAuthError(null); // Clear previous errors

        try {
            await registerUser(name, email, password, phone);
            // Auto login immediately after successful registration
            await loginUser(email, password);
            closeAuthModal();
            initAuthNavbar();
        } catch (error) {
            showAuthError(error.message);
        }
    });
}

// Opens the modal and selects the requested tab
function openAuthModal(tab = "login") {
    const modal = document.getElementById("auth-modal");
    if (!modal) return;
    showAuthError(null);
    switchAuthTab(tab);
    modal.classList.add("open");
}

// Closes the modal
function closeAuthModal() {
    const modal = document.getElementById("auth-modal");
    if (modal) modal.classList.remove("open");
}

// Switches between login and register views
function switchAuthTab(tab) {
    const tabLogin = document.getElementById("tab-login-btn");
    const tabRegister = document.getElementById("tab-register-btn");
    const loginForm = document.getElementById("login-form");
    const registerForm = document.getElementById("register-form");

    showAuthError(null);

    if (tab === "login") {
        tabLogin?.classList.add("active");
        tabRegister?.classList.remove("active");
        loginForm?.classList.remove("hidden");
        registerForm?.classList.add("hidden");
    } else {
        tabRegister?.classList.add("active");
        tabLogin?.classList.remove("active");
        registerForm?.classList.remove("hidden");
        loginForm?.classList.add("hidden");
    }
}

// Helper: Performs login and updates UI
async function handleLoginSubmit(email, password) {
    showAuthError(null);
    try {
        await loginUser(email, password);
        closeAuthModal();
        initAuthNavbar();
    } catch (error) {
        showAuthError(error.message);
    }
}

// Helper: Displays or clears error banners in the modal
function showAuthError(message) {
    const errorBanner = document.getElementById("auth-error-banner");
    if (!errorBanner) return;

    if (message) {
        errorBanner.textContent = message;
        errorBanner.classList.add("show");
    } else {
        errorBanner.textContent = "";
        errorBanner.classList.remove("show");
    }
}
