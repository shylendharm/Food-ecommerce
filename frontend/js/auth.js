// Authentication controller, Google SSO, and navigation bar

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


// Route guards

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


// Navbar user menu

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
                    ${escapeHtml(displayName)}
                    <span style="display: inline-block; background: rgba(225, 29, 72, 0.1); color: var(--primary, #E11D48); border: 1px solid rgba(225, 29, 72, 0.25); font-size: 0.7rem; font-weight: 700; padding: 2px 7px; border-radius: 999px; vertical-align: middle; margin-left: 6px; text-transform: uppercase;">Admin</span>
                </div>
                <div class="dropdown-user-email">${escapeHtml(user?.email || "")}</div>
            </div>
            <div class="dropdown-divider"></div>
            <a href="profile-setup.html" class="dropdown-item">
                <span>Edit Profile</span>
            </a>
            <button type="button" id="logout-btn" class="dropdown-item logout">
                <span>Sign Out</span>
            </button>
        `;
    } else {
        dropdownBody = `
            <div class="dropdown-header">
                <div class="dropdown-user-name">${escapeHtml(displayName)}</div>
                <div class="dropdown-user-email">${escapeHtml(user?.email || "")}</div>
                ${user?.default_address ? `
                    <div style="font-size: 0.75rem; color: var(--text-muted, #71717A); margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 220px;">
                        ${escapeHtml(user.default_address)}
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
            <button type="button" id="logout-btn" class="dropdown-item logout">
                <span>Sign Out</span>
            </button>
        `;
    }

    // Restored pure typographic presentation matching style.css selectors
    authNavContainer.innerHTML = `
        <div class="user-menu-container">
            <button type="button" id="user-menu-btn" class="user-menu-btn" aria-label="Open User Menu">
                <span>Hi, ${escapeHtml(displayName)}</span>
                <span style="font-size: 0.72rem; margin-left: 4px;">▼</span>
            </button>
            <div id="user-dropdown" class="user-dropdown">
                ${dropdownBody}
            </div>
        </div>
    `;

    // Dropdown toggle logic using .show class defined in style.css:248
    const menuBtn = document.getElementById("user-menu-btn");
    const dropdown = document.getElementById("user-dropdown");
    const logoutBtn = document.getElementById("logout-btn");

    if (menuBtn && dropdown) {
        menuBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            dropdown.classList.toggle("show");
        });

        document.addEventListener("click", (e) => {
            if (!dropdown.contains(e.target) && e.target !== menuBtn) {
                dropdown.classList.remove("show");
            }
        });
    }

    if (logoutBtn) {
        logoutBtn.addEventListener("click", handleUserSignOut);
    }
}

/**
 * Clean Sign Out flow with Unified Modal Confirmation
 */
async function handleUserSignOut() {
    let confirmed = true;
    if (typeof showAppConfirm === "function") {
        confirmed = await showAppConfirm({
            title: "Sign Out",
            message: "Are you sure you want to end your FoodExpress session?",
            tag: "Session",
            confirmText: "Sign Out",
            cancelText: "Stay Logged In"
        });
    } else {
        confirmed = window.confirm("Are you sure you want to sign out?");
    }

    if (confirmed) {
        logoutUser();
    }
}


// Login and registration form

function initLoginPage() {
    const isLoginPage = window.location.pathname.toLowerCase().endsWith("login.html");
    if (!isLoginPage) return;

    const tabLogin = document.getElementById("tab-login");
    const tabRegister = document.getElementById("tab-register");
    const fieldNameGroup = document.getElementById("field-name-group");
    const submitBtn = document.getElementById("portal-submit-btn");
    const form = document.getElementById("portal-form");
    const subtitle = document.getElementById("portal-subtitle");

    let isRegisterMode = false;

    function setAuthMode(register) {
        isRegisterMode = register;
        if (isRegisterMode) {
            tabRegister?.classList.add("active");
            tabLogin?.classList.remove("active");
            fieldNameGroup?.classList.remove("auth-field-hidden");
            if (submitBtn) submitBtn.textContent = "Create Account";
            if (subtitle) subtitle.textContent = "Join FoodExpress to start ordering fresh meals";
        } else {
            tabLogin?.classList.add("active");
            tabRegister?.classList.remove("active");
            fieldNameGroup?.classList.add("auth-field-hidden");
            if (submitBtn) submitBtn.textContent = "Sign In";
            if (subtitle) subtitle.textContent = "Sign in to your account to continue";
        }
        showPortalError("");
    }

    tabLogin?.addEventListener("click", () => setAuthMode(false));
    tabRegister?.addEventListener("click", () => setAuthMode(true));

    form?.addEventListener("submit", async (e) => {
        e.preventDefault();
        showPortalError("");

        const email = document.getElementById("input-email")?.value.trim();
        const password = document.getElementById("input-password")?.value;
        const name = document.getElementById("input-name")?.value.trim();

        if (!email || !password) {
            showPortalError("Email address and password are required.");
            return;
        }

        if (isRegisterMode && !name) {
            showPortalError("Full Name is required to create your account.");
            return;
        }

        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = isRegisterMode ? "Creating Account..." : "Signing In...";
        }

        try {
            if (isRegisterMode) {
                await registerUser({ name, email, password });
            } else {
                await loginUser(email, password);
            }

            const user = getStoredUser();

            // Redirect flow
            if (user?.role === "ADMIN") {
                window.location.href = "admin.html";
                return;
            }

            if (!user?.phone || !user?.default_address) {
                window.location.href = "profile-setup.html";
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
            showPortalError(error.message || "Authentication failed. Please verify credentials.");
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = isRegisterMode ? "Create Account" : "Sign In";
            }
        }
    });
}


// Google OAuth2 integration

function initGoogleIdentityServices() {
    if (!window.GOOGLE_CLIENT_ID) return;

    function renderResponsiveGoogleButton() {
        const googleContainer = document.getElementById("google-sso-btn");
        const wrapper = document.getElementById("google-sso-wrapper");
        if (!googleContainer || !window.google?.accounts?.id) return;

        // Measure available container width (subtracting any inner card padding)
        const parentCard = googleContainer.closest(".auth-portal-card");
        let availableWidth = 320;

        if (wrapper && wrapper.clientWidth > 0) {
            availableWidth = wrapper.clientWidth;
        } else if (parentCard && parentCard.clientWidth > 0) {
            availableWidth = parentCard.clientWidth - 36;
        } else if (window.innerWidth < 440) {
            availableWidth = Math.floor(window.innerWidth - 64);
        }

        // Google Identity Services strictly requires width between 200px and 400px
        const calculatedWidth = Math.max(200, Math.min(376, Math.floor(availableWidth)));

        googleContainer.innerHTML = "";
        window.google.accounts.id.renderButton(googleContainer, {
            theme: "outline",
            size: "large",
            type: "standard",
            text: "continue_with",
            shape: "rectangular",
            logo_alignment: "left",
            width: calculatedWidth
        });
    }

    function setupGsi() {
        if (!window.google?.accounts?.id) return;

        try {
            // 1. Initialize Google Identity Services
            window.google.accounts.id.initialize({
                client_id: window.GOOGLE_CLIENT_ID,
                callback: window.handleGoogleCredentialResponse,
                auto_select: false,
                cancel_on_tap_outside: true
            });

            // 2. Render responsive Google button
            renderResponsiveGoogleButton();

            // 3. Prompt One Tap if on login page
            const isLoginPage = window.location.pathname.toLowerCase().endsWith("login.html");
            if (isLoginPage) {
                window.google.accounts.id.prompt();
            }

            // 4. Listen for orientation / viewport resize to maintain flush card bounds
            let resizeTimer;
            window.addEventListener("resize", () => {
                clearTimeout(resizeTimer);
                resizeTimer = setTimeout(renderResponsiveGoogleButton, 200);
            });

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


// Helpers

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

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}