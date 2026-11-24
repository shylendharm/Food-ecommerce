/* =============================================================
   FILE: frontend/js/auth.js
   AUTHENTICATION & ROUTE GUARD CONTROLLER
   Enforces mandatory global authentication guards, onboarding
   lifecycle routing, typographic navbar, live Google OAuth2 SSO,
   and clean minimalist sign-out confirmation.
   ============================================================= */

// Official Google Cloud OAuth 2.0 Web Client ID
const GOOGLE_CLIENT_ID = "689639687351-pfvpvkc0gen8slip0jj6ff6b4ibpbeu6.apps.googleusercontent.com";
window.GOOGLE_CLIENT_ID = GOOGLE_CLIENT_ID;

document.addEventListener("DOMContentLoaded", () => {
    // 1. Mandatory Route Guard: Run first before rendering any UI
    const canProceed = enforceRouteGuard();
    if (!canProceed) return;

    // 2. Initialize page-specific controllers
    initLoginPage();
    initAuthNavbar();
    initGoogleIdentityServices();
});


/* =============================================================
   1. GLOBAL ROUTE GUARD & ROLE ROUTER
   ============================================================= */

function enforceRouteGuard() {
    const rawPath = window.location.pathname.toLowerCase();
    const isAuthPage = rawPath.endsWith("login.html");
    const isOnboardingPage = rawPath.endsWith("profile-setup.html");
    const authed = isAuthenticated();
    const user = getStoredUser();

    // 1. GUEST LOCKOUT: Unauthenticated users are redirected to login.html
    if (!authed) {
        if (!isAuthPage) {
            window.location.href = "login.html";
            return false;
        }
        return true;
    }

    // 2. ONBOARDING GATE: Missing phone or default address requires profile setup
    const profileIncomplete = !user || !user.phone || !user.default_address;
    if (profileIncomplete) {
        if (!isOnboardingPage) {
            window.location.href = "profile-setup.html";
            return false;
        }
        return true;
    }

    // 3. LOGGED-IN USERS VISITING LOGIN PAGE: Redirect to home or admin
    if (isAuthPage) {
        if (isAdmin()) {
            window.location.href = "admin.html";
        } else {
            window.location.href = "index.html";
        }
        return false;
    }

    // 4. ROLE ISOLATION: Admin visiting customer storefront -> KDS Operations
    if (isAdmin() && !rawPath.endsWith("admin.html") && !isOnboardingPage) {
        window.location.href = "admin.html";
        return false;
    }

    // 5. ROLE ISOLATION: Customer attempting to access admin portal -> Storefront
    if (!isAdmin() && rawPath.endsWith("admin.html")) {
        window.location.href = "index.html";
        return false;
    }

    return true;
}


/* =============================================================
   2. NAVBAR STATE CONTROLLER (Typographic Name Only - No Avatars)
   ============================================================= */

function initAuthNavbar() {
    const authNavContainer = document.getElementById("auth-nav-container");
    if (!authNavContainer) return;

    if (!isAuthenticated()) {
        authNavContainer.innerHTML = `
            <a href="login.html" class="btn-login">
                <span>Sign In</span>
            </a>
        `;
        return;
    }

    const user = getStoredUser();
    // Display full name entered in profile creation, never email prefix
    const displayName = user?.name ? user.name.trim() : "Account";
    const userIsAdmin = isAdmin();

    let dropdownBody = "";

    if (userIsAdmin) {
        dropdownBody = `
            <div class="dropdown-header">
                <div class="dropdown-user-name">
                    ${displayName}
                    <span style="display: inline-block; background: rgba(225, 29, 72, 0.1); color: var(--primary, #E11D48); border: 1px solid rgba(225, 29, 72, 0.25); font-size: 0.7rem; font-weight: 700; padding: 2px 7px; border-radius: 999px; vertical-align: middle; margin-left: 6px; text-transform: uppercase;">Admin</span>
                </div>
                <div class="dropdown-user-email">${user?.email || ""}</div>
            </div>
            <div class="dropdown-divider"></div>
            <a href="profile-setup.html" class="dropdown-item">
                <span>Edit Profile</span>
            </a>
            <button id="logout-btn" class="dropdown-item logout">
                <span>Sign Out</span>
            </button>
        `;
    } else {
        dropdownBody = `
            <div class="dropdown-header">
                <div class="dropdown-user-name">${displayName}</div>
                <div class="dropdown-user-email">${user?.email || ""}</div>
                ${user?.default_address ? `
                    <div style="font-size: 0.75rem; color: var(--text-muted, #71717A); margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 220px;">
                        ${user.default_address}
                    </div>
                ` : ""}
            </div>
            <a href="my-orders.html" class="dropdown-item">
                <span>My Orders</span>
            </a>
            <a href="profile-setup.html" class="dropdown-item">
                <span>Edit Profile</span>
            </a>
            <div class="dropdown-divider"></div>
            <button id="logout-btn" class="dropdown-item logout">
                <span>Sign Out</span>
            </button>
        `;
    }

    // Pure typographic presentation: NO profile images and NO avatar circles
    authNavContainer.innerHTML = `
        <div class="user-menu-container">
            <button id="user-menu-btn" class="user-menu-btn" aria-label="Open User Menu">
                <span>Hi, ${displayName}</span>
                <span style="font-size: 0.72rem; margin-left: 4px;">▼</span>
            </button>
            <div id="user-dropdown" class="user-dropdown">
                ${dropdownBody}
            </div>
        </div>
    `;

    const menuBtn = document.getElementById("user-menu-btn");
    const dropdown = document.getElementById("user-dropdown");
    const logoutBtn = document.getElementById("logout-btn");

    menuBtn?.addEventListener("click", (e) => {
        e.stopPropagation();
        dropdown?.classList.toggle("show");
    });

    document.addEventListener("click", (e) => {
        if (!dropdown?.contains(e.target) && e.target !== menuBtn) {
            dropdown?.classList.remove("show");
        }
    });

    // Intercept Sign Out with Clean Minimalist Confirmation Modal
    logoutBtn?.addEventListener("click", async () => {
        dropdown?.classList.remove("show");

        const confirmed = await showAppConfirm({
            title: "Sign Out",
            message: "Are you sure you want to sign out of FoodExpress? You will need to sign in again to place orders.",
            confirmText: "Sign Out",
            cancelText: "Stay",
            isDanger: true
        });

        if (confirmed) {
            logoutUser();
            window.location.href = "login.html";
        }
    });
}


/* =============================================================
   3. DEDICATED LOGIN PORTAL CONTROLLER (login.html)
   ============================================================= */

function initLoginPage() {
    const form = document.getElementById("portal-form");
    if (!form) return;

    let mode = "login"; // "login" | "register"

    const tabLogin = document.getElementById("tab-login");
    const tabRegister = document.getElementById("tab-register");
    const nameGroup = document.getElementById("field-name-group");
    const nameInput = document.getElementById("input-name");
    const emailInput = document.getElementById("input-email");
    const passwordInput = document.getElementById("input-password");
    const submitBtn = document.getElementById("portal-submit-btn");
    const subtitle = document.getElementById("portal-subtitle");

    function setMode(newMode) {
        mode = newMode;
        showPortalError(null);
        if (mode === "login") {
            tabLogin?.classList.add("active");
            tabRegister?.classList.remove("active");
            nameGroup?.classList.add("auth-field-hidden");
            nameInput?.removeAttribute("required");
            if (submitBtn) submitBtn.textContent = "Sign In";
            if (subtitle) subtitle.textContent = "Sign in to your account to continue";
        } else {
            tabRegister?.classList.add("active");
            tabLogin?.classList.remove("active");
            nameGroup?.classList.remove("auth-field-hidden");
            nameInput?.setAttribute("required", "true");
            if (submitBtn) submitBtn.textContent = "Create Account";
            if (subtitle) subtitle.textContent = "Create your FoodExpress account";
        }
    }

    tabLogin?.addEventListener("click", () => setMode("login"));
    tabRegister?.addEventListener("click", () => setMode("register"));

    // Form Submission: Sign In or Create Account
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        showPortalError(null);
        if (submitBtn) submitBtn.disabled = true;

        const email = emailInput.value.trim();
        const password = passwordInput.value;

        try {
            if (mode === "register") {
                const name = nameInput.value.trim();
                if (name.length < 2) {
                    throw new Error("Full Name must contain at least 2 characters.");
                }

                // 1. Create account in database
                await registerUser(name, email, password);

                // 2. Log in with newly created credentials to receive JWT token
                await loginUser(email, password);

                // 3. Immediately route to mandatory profile onboarding setup
                window.location.href = "profile-setup.html";
            } else {
                // Sign In mode
                const loginData = await loginUser(email, password);
                const user = loginData.user;

                // If profile missing phone or address, intercept to onboarding
                if (!user.phone || !user.default_address) {
                    window.location.href = "profile-setup.html";
                    return;
                }

                if (user.role === "ADMIN") {
                    window.location.href = "admin.html";
                } else {
                    window.location.href = "index.html";
                }
            }
        } catch (err) {
            showPortalError(err.message || "Authentication failed. Please verify credentials.");
        } finally {
            if (submitBtn) submitBtn.disabled = false;
        }
    });
}


/* =============================================================
   4. LIVE GOOGLE OAUTH2 IDENTITY SERVICES INITIALIZATION
   ============================================================= */

function initGoogleIdentityServices() {
    if (!window.GOOGLE_CLIENT_ID) return;

    function setupGsi() {
        if (!window.google?.accounts?.id) return;

        try {
            // 1. Initialize Google Identity Services with real Client ID
            window.google.accounts.id.initialize({
                client_id: window.GOOGLE_CLIENT_ID,
                callback: window.handleGoogleCredentialResponse,
                auto_select: false,
                cancel_on_tap_outside: true
            });

            // 2. Render Official Google Sign-In Button inside login.html container
            const googleContainer = document.getElementById("google-sso-btn");
            if (googleContainer) {
                window.google.accounts.id.renderButton(googleContainer, {
                    theme: "outline",
                    size: "large",
                    type: "standard",
                    text: "continue_with",
                    shape: "rectangular",
                    logo_alignment: "left",
                    width: 376
                });
            }

            // 3. Prompt One Tap if on login page
            const isLoginPage = window.location.pathname.toLowerCase().endsWith("login.html");
            if (isLoginPage) {
                window.google.accounts.id.prompt();
            }
        } catch (err) {
            console.error("[Auth] Google Identity Services initialization error:", err);
        }
    }

    if (window.google?.accounts?.id) {
        setupGsi();
    } else {
        window.addEventListener("load", setupGsi);
    }
}

// Global callback invoked by official Google Identity Services SDK
window.handleGoogleCredentialResponse = async function (response) {
    if (!response || !response.credential) return;

    // Visual feedback: dim container to indicate active cryptographic verification
    const googleContainer = document.getElementById("google-sso-btn");
    const submitBtn = document.getElementById("portal-submit-btn");
    if (googleContainer) googleContainer.style.opacity = "0.5";
    if (submitBtn) submitBtn.disabled = true;

    try {
        // Send authentic Google ID token to FastAPI backend
        const data = await loginWithGoogle(response.credential);
        const user = data.user;

        // Check if onboarding profile completion is required
        if (!user.phone || !user.default_address) {
            window.location.href = "profile-setup.html";
            return;
        }

        if (user.role === "ADMIN") {
            window.location.href = "admin.html";
            return;
        }

        const redirect = sessionStorage.getItem("post_login_redirect");
        if (redirect) {
            sessionStorage.removeItem("post_login_redirect");
            window.location.href = redirect;
            return;
        }

        window.location.href = "index.html";
    } catch (error) {
        if (googleContainer) googleContainer.style.opacity = "1";
        if (submitBtn) submitBtn.disabled = false;
        showPortalError(error.message || "Google Single Sign-On verification failed.");
    }
};


/* =============================================================
   5. UI ERROR HELPER
   ============================================================= */

function showPortalError(message) {
    const errorBanner = document.getElementById("portal-error-banner");
    if (!errorBanner) return;

    if (message) {
        errorBanner.textContent = message;
        errorBanner.classList.add("show");
    } else {
        errorBanner.textContent = "";
        errorBanner.classList.remove("show");
    }
}