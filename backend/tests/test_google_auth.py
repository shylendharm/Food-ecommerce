"""
Automated Test Suite: Google OAuth2 Single Sign-On (SSO) & Account Linking
Location: backend/tests/test_google_auth.py

Verifies:
1. Auto-provisioning a new customer account upon first Google Sign-In.
2. Account linking when an existing email logs in with Google (Idempotent with UUID).
3. Automatic ADMIN role assignment for the master owner (shylendharm369@gmail.com).
4. Security guard: Google accounts cannot be accessed via empty local passwords.
5. Validating that Google-issued JWT tokens unlock protected endpoints (/api/auth/me).
6. Rejection of invalid, forged, or expired Google tokens (401 Unauthorized).
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# =============================================================
# 1. NEW CUSTOMER AUTO-PROVISIONING TEST
# =============================================================

def test_google_auth_new_customer_registration():
    """
    Verifies that a first-time Google visitor is automatically
    registered in MySQL as a CUSTOMER with auth_provider='GOOGLE'
    and password_hash=None.
    """
    payload = {
        "credential": "mock_google_token_firsttime_customer@gmail.com"
    }

    res = client.post("/api/auth/google", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

    user = data["user"]
    assert user["email"] == "firsttime_customer@gmail.com"
    assert user["role"] == "CUSTOMER"
    assert user["auth_provider"] == "GOOGLE"
    assert user["picture_url"] is not None


# =============================================================
# 2. ACCOUNT LINKING WITH EXISTING LOCAL USER TEST (IDEMPOTENT)
# =============================================================

def test_google_auth_account_linking_existing_user():
    """
    Verifies that if a user already registered locally with a password,
    subsequently logging in with Google links their Google identity
    to the same account without creating a duplicate row in MySQL.
    Uses uuid to guarantee repeatability across infinite test runs.
    """
    unique_suffix = uuid.uuid4().hex[:8]
    email = f"hybrid_{unique_suffix}@gmail.com"

    # 1. Register locally first with email + password
    local_reg_payload = {
        "name": f"Hybrid User {unique_suffix}",
        "email": email,
        "password": "Password123!"
    }
    reg_res = client.post("/api/auth/register", json=local_reg_payload)
    assert reg_res.status_code == 201
    existing_user_id = reg_res.json()["id"]

    # 2. Now log in via Google SSO using the same email
    google_payload = {
        "credential": f"mock_google_token_{email}"
    }
    google_res = client.post("/api/auth/google", json=google_payload)
    assert google_res.status_code == 200
    google_user = google_res.json()["user"]

    # Must preserve the exact same user ID (no duplicate created!)
    assert google_user["id"] == existing_user_id
    assert google_user["email"] == email
    assert google_user["auth_provider"] == "GOOGLE"


# =============================================================
# 3. ADMIN ROLE RECOGNITION TEST (shylendharm369@gmail.com)
# =============================================================

def test_google_auth_admin_role_assignment():
    """
    Verifies that the designated master administrator (shylendharm369@gmail.com)
    logging in via Google is automatically recognized and granted the ADMIN role.
    """
    payload = {
        "credential": "mock_google_token_shylendharm369@gmail.com"
    }

    res = client.post("/api/auth/google", json=payload)
    assert res.status_code == 200
    data = res.json()

    user = data["user"]
    assert user["email"] == "shylendharm369@gmail.com"
    assert user["role"] == "ADMIN"


# =============================================================
# 4. SECURITY GUARD: NO EMPTY PASSWORD BYPASS
# =============================================================

def test_google_user_cannot_login_with_local_password():
    """
    Verifies that an account created via Google SSO cannot be logged
    into via the traditional /api/auth/login endpoint using an empty
    or arbitrary password string.
    """
    # 1. Create a Google-only customer
    email = "google_only_shopper@gmail.com"
    client.post("/api/auth/google", json={"credential": f"mock_google_token_{email}"})

    # 2. Attempt local login with empty password -> Must be rejected with 401
    bad_login_res = client.post("/api/auth/login", json={
        "email": email,
        "password": ""
    })
    assert bad_login_res.status_code == 401

    # 3. Attempt local login with random password -> Must be rejected with 401
    bad_login_res2 = client.post("/api/auth/login", json={
        "email": email,
        "password": "GuessPassword123"
    })
    assert bad_login_res2.status_code == 401


# =============================================================
# 5. PROTECTED ENDPOINTS WITH GOOGLE JWT TEST
# =============================================================

def test_google_token_jwt_can_access_protected_routes():
    """
    Verifies that the JWT issued upon Google login unlocks protected
    customer endpoints like /api/auth/me seamlessly.
    """
    payload = {
        "credential": "mock_google_token_traveler@gmail.com"
    }

    login_res = client.post("/api/auth/google", json=payload)
    assert login_res.status_code == 200
    access_token = login_res.json()["access_token"]

    # Access protected profile endpoint with Bearer token
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "traveler@gmail.com"
    assert me_data["auth_provider"] == "GOOGLE"


# =============================================================
# 6. FORGED OR INVALID GOOGLE TOKEN REJECTION TEST
# =============================================================

def test_invalid_google_token_rejected():
    """
    Verifies that sending an invalid, forged, or expired token to
    /api/auth/google is rejected with HTTP 401 Unauthorized.
    """
    payload = {
        "credential": "invalid_forged_unauthorized_token_xyz"
    }

    res = client.post("/api/auth/google", json=payload)
    assert res.status_code == 401
    assert "Invalid, expired, or forged" in res.json()["detail"]