/* =============================================================
   AUTHENTICATION & NAVBAR CONTROLLER (frontend/js/auth.js)
   Manages pure Google OAuth2 SSO, role-based navigation routing,
   and role-specific profile dropdown states.
   ============================================================= */

document.addEventListener("DOMContentLoaded", () => {
    // 1. Role-based auto-routing: If logged in as ADMIN and currently on storefront,
    // immediately direct to the Kitchen Operations Console (KDS)
    if (isAdmin() && !window.location.pathname.endsWith("admin.html")) {
        window.location.href = "admin.html";
        return;
    }

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
            openAuthModal();
        });
    } else {
        // --- 2. LOGGED-IN STATE: Render User Profile Dropdown ---
        const user = getStoredUser();
        const firstName = user?.name ? user.name.split(" ")[0] : "Account";
        const initial = user?.name ? user.name.charAt(0).toUpperCase() : "U";
        const userIsAdmin = isAdmin();

        // If the user has a Google profile avatar, render circular <img>; otherwise initial letter
        const avatarContent = user?.picture_url
            ? `<img src="${user.picture_url}" alt="${firstName}" />`
            : `${initial}`;

        // Construct role-specific dropdown contents
        let dropdownBody = "";

        if (userIsAdmin) {
            // ADMIN DROPDOWN: Strictly Name with 'Admin' tag beside it and Sign Out
            dropdownBody = `
                <div class="dropdown-header">
                    <div class="dropdown-user-name">
                        ${user?.name || "Administrator"} 
                        <span style="display: inline-block; background: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.35); font-size: 0.7rem; font-weight: 700; padding: 2px 7px; border-radius: 999px; vertical-align: middle; margin-left: 6px; text-transform: uppercase; letter-spacing: 0.04em;">Admin</span>
                    </div>
                    <div class="dropdown-user-email">${user?.email || ""}</div>
                </div>

                <div class="dropdown-divider"></div>

                <button id="logout-btn" class="dropdown-item logout">
                    <span>🚪</span>
                    <span>Sign Out</span>
                </button>
            `;
        } else {
            // CUSTOMER DROPDOWN: Name, Email, My Orders, and Sign Out
            dropdownBody = `
                <div class="dropdown-header">
                    <div class="dropdown-user-name">${user?.name || "Customer"}</div>
                    <div class="dropdown-user-email">${user?.email || ""}</div>
                    ${user?.auth_provider === "GOOGLE" ? `
                        <div style="font-size: 0.72rem; color: #4285F4; margin-top: 4px; font-weight: 600;">
                            🔵 Verified Google Account
                        </div>
                    ` : ""}
                </div>

                <a href="my-orders.html" class="dropdown-item">
                    <span>📦</span>
                    <span>My Orders</span>
                </a>

                <div class="dropdown-divider"></div>

                <button id="logout-btn" class="dropdown-item logout">
                    <span>🚪</span>
                    <span>Sign Out</span>
                </button>
            `;
        }

        authNavContainer.innerHTML = `
            <div class="user-menu-container">
                <button id="user-menu-btn" class="user-menu-btn" aria-label="Open User Menu">
                    <span class="user-avatar">${avatarContent}</span>
                    <span>Hi, ${firstName}</span>
                    <span style="font-size: 0.75rem;">▼</span>
                </button>

                <div id="user-dropdown" class="user-dropdown">
                    ${dropdownBody}
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

        // Close dropdown when clicking anywhere else on document
        document.addEventListener("click", (e) => {
            if (!dropdown?.contains(e.target) && e.target !== menuBtn) {
                dropdown?.classList.remove("show");
            }
        });

        // Sign out button handler: Clear session and smoothly return to storefront
        logoutBtn?.addEventListener("click", () => {
            logoutUser();
            window.location.href = "index.html";
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
    const googleBtn = document.getElementById("google-signin-btn");

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

    // Primary Google SSO Button Click
    googleBtn?.addEventListener("click", handleGoogleSignIn);

    // Initialize official Google Identity Services if client ID is configured
    try {
        if (window.google?.accounts?.id && window.GOOGLE_CLIENT_ID) {
            window.google.accounts.id.initialize({
                client_id: window.GOOGLE_CLIENT_ID,
                callback: handleGoogleCredentialResponse
            });
        }
    } catch (err) {
        console.warn("Google Identity Services initialization:", err);
    }
}


/* =============================================================
   3. GOOGLE OAUTH2 SIGN-IN HANDLER
   ============================================================= */

// Global callback invoked by official Google Identity Services SDK
window.handleGoogleCredentialResponse = async function (response) {
    if (!response || !response.credential) return;
    try {
        const data = await loginWithGoogle(response.credential);
        closeAuthModal();

        // If authenticated as ADMIN, route directly to the Kitchen Operations portal
        if (data.user && data.user.role === "ADMIN") {
            window.location.href = "admin.html";
            return;
        }

        initAuthNavbar();
        console.log("✅ Authenticated via Google Identity Services");
    } catch (error) {
        showAuthError(error.message || "Google Single Sign-On failed.");
    }
};

// Invoked when user clicks the "Continue with Google" button
async function handleGoogleSignIn() {
    showAuthError(null);

    // 1. If Google Identity Services SDK is configured with a live Client ID:
    if (window.google?.accounts?.id && window.GOOGLE_CLIENT_ID) {
        window.google.accounts.id.prompt();
        return;
    }

    // 2. Interactive Development / Placement Interview Demo Mode:
    const defaultEmail = "shylendharm369@gmail.com";
    const promptMessage =
        "Google Single Sign-On (Development Demo):\n" +
        "Enter any Google email address to authenticate:\n\n" +
        "• Press OK to log in as Master Admin (shylendharm369@gmail.com)\n" +
        "• Or enter any other email (e.g. rahul@gmail.com) to test Customer role";

    const userEmail = prompt(promptMessage, defaultEmail);
    if (!userEmail) return; // User pressed Cancel

    const sanitizedEmail = userEmail.trim().toLowerCase();
    const mockCredential = `mock_google_token_${sanitizedEmail}`;

    try {
        const data = await loginWithGoogle(mockCredential);
        closeAuthModal();

        // If authenticated as ADMIN, route directly to the Kitchen Operations portal
        if (data.user && data.user.role === "ADMIN") {
            window.location.href = "admin.html";
            return;
        }

        initAuthNavbar();
        console.log(`✅ Logged in successfully via Google SSO as: ${sanitizedEmail} (Role: ${data.user.role})`);
    } catch (error) {
        showAuthError(error.message || "Google authentication failed.");
    }
}


/* =============================================================
   4. MODAL & UI HELPERS
   ============================================================= */

// Opens the Google SSO modal
function openAuthModal() {
    const modal = document.getElementById("auth-modal");
    if (!modal) return;
    showAuthError(null);
    modal.classList.add("open");
}

// Closes the modal
function closeAuthModal() {
    const modal = document.getElementById("auth-modal");
    if (modal) modal.classList.remove("open");
}

// Displays or clears error banners in the modal
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