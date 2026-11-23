/* =============================================================
   FILE: frontend/js/profile-setup.js
   ONBOARDING & PROFILE EDIT CONTROLLER
   Manages first-time profile onboarding, profile editing, input
   validation, and contextual post-save navigation routing.
   ============================================================= */

document.addEventListener("DOMContentLoaded", () => {
    // 1. Enforce authentication: Guest visitors cannot access profile setup
    if (!isAuthenticated()) {
        window.location.href = "login.html";
        return;
    }

    const user = getStoredUser();

    // DOM Elements
    const form = document.getElementById("profile-setup-form");
    const nameInput = document.getElementById("setup-name");
    const emailInput = document.getElementById("setup-email");
    const phoneInput = document.getElementById("setup-phone");
    const addressInput = document.getElementById("setup-address");
    const submitBtn = document.getElementById("profile-submit-btn");
    const errorBanner = document.getElementById("profile-error-banner");
    const subtitleEl = document.querySelector(".auth-subtitle");

    // 2. Detect Mode: First-time Onboarding vs Profile Editing
    const isEditing = Boolean(user?.phone && user?.default_address);

    if (isEditing) {
        if (subtitleEl) {
            subtitleEl.textContent = "Update your contact details and default delivery address.";
        }
        if (submitBtn) {
            submitBtn.textContent = "Update Profile";
        }

        // Render clean "Cancel and Return" link for existing users
        if (!document.getElementById("cancel-profile-link")) {
            const cancelLink = document.createElement("a");
            cancelLink.id = "cancel-profile-link";
            cancelLink.href = user?.role === "ADMIN" ? "admin.html" : "index.html";
            cancelLink.className = "auth-cancel-link";
            cancelLink.textContent = "Cancel and Return";
            submitBtn.insertAdjacentElement("afterend", cancelLink);
        }
    }

    // 3. Pre-populate existing user data
    if (emailInput && user?.email) {
        emailInput.value = user.email;
    }

    if (nameInput && user?.name) {
        nameInput.value = user.name;
    }

    if (phoneInput && user?.phone) {
        phoneInput.value = user.phone;
    }

    if (addressInput && user?.default_address) {
        addressInput.value = user.default_address;
    }

    // Error banner helper
    function showError(message) {
        if (!errorBanner) return;
        if (message) {
            errorBanner.textContent = message;
            errorBanner.classList.add("show");
        } else {
            errorBanner.textContent = "";
            errorBanner.classList.remove("show");
        }
    }

    // 4. Form Submission Handler
    form?.addEventListener("submit", async (e) => {
        e.preventDefault();
        showError(null);

        const fullName = nameInput.value.trim();
        const phone = phoneInput.value.trim();
        const address = addressInput.value.trim();

        // Client-side Input Validation
        if (fullName.length < 2) {
            showError("Please enter your full legal name (at least 2 characters).");
            nameInput.focus();
            return;
        }

        // Validate clean 10-15 digit phone format
        const cleanPhoneDigits = phone.replace(/[\s\-\+\(\)]/g, "");
        if (cleanPhoneDigits.length < 10 || cleanPhoneDigits.length > 15 || !/^\d+$/.test(cleanPhoneDigits)) {
            showError("Please enter a valid mobile number (10 to 15 digits).");
            phoneInput.focus();
            return;
        }

        if (address.length < 5) {
            showError("Please enter a complete delivery address (street, area, city).");
            addressInput.focus();
            return;
        }

        // Lock button during asynchronous mutation
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = isEditing ? "Updating Profile..." : "Saving Profile...";
        }

        try {
            // 5. Dispatch authenticated profile mutation to FastAPI
            const updatedUser = await updateUserProfile({
                name: fullName,
                phone: phone,
                default_address: address
            });

            console.log("[Profile] Profile updated successfully for:", updatedUser.email);

            // 6. Contextual Post-Save Navigation
            if (updatedUser.role === "ADMIN") {
                window.location.href = "admin.html";
                return;
            }

            const postLoginRedirect = sessionStorage.getItem("post_login_redirect");
            if (postLoginRedirect) {
                sessionStorage.removeItem("post_login_redirect");
                window.location.href = postLoginRedirect;
                return;
            }

            window.location.href = "index.html";

        } catch (error) {
            showError(error.message || "Failed to update profile. Please try again.");
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = isEditing ? "Update Profile" : "Save Profile & Continue";
            }
        }
    });
});