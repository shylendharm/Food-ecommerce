# =============================================================
# FILE: backend/tests/test_auth.py
# =============================================================

"""
Automated Test Suite: Authentication, Security & Profile Management
Location: backend/tests/test_auth.py

Tests:
1. Unit: Bcrypt password hashing and verification.
2. Integration: User registration, duplicate email handling, and JWT issuance.
3. Profile Management: PUT /api/auth/profile (Happy path, persistence, auth guard, Pydantic validation).
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.security import hash_password, verify_password

client = TestClient(app)


# =============================================================
# 1. UNIT TESTS: PASSWORD HASHING
# =============================================================

def test_password_hashing_unit():
    """
    Unit Test: Verifies that bcrypt hashes are salted and verify correctly.
    """
    raw_password = "SuperSecretPassword123"

    # 1. Hash the password
    hashed = hash_password(raw_password)

    # Assert that the hash is NOT the plain text
    assert hashed != raw_password
    assert hashed.startswith("$2b$")  # Bcrypt identifier tag

    # Assert that the correct password verifies to True
    assert verify_password(raw_password, hashed) is True

    # Assert that a wrong password verifies to False
    assert verify_password("WrongPassword!", hashed) is False


# =============================================================
# 2. INTEGRATION TESTS: AUTH API ENDPOINTS
# =============================================================

# Unique test email suffix to guarantee idempotent test isolation across multiple runs
TEST_UUID = uuid.uuid4().hex[:8]
TEST_EMAIL = f"tester_{TEST_UUID}@restaurant.com"
TEST_PASSWORD = "StrongTestPassword!123"


def test_register_new_user():
    """
    Integration Test: Registering a brand new user.
    Expects: HTTP 201 Created, default_address serialization, and password_hash omitted.
    """
    payload = {
        "name": "Automated Tester",
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "phone": "9998887771",
        "default_address": "404 Main Street, Bengaluru"
    }

    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["email"] == TEST_EMAIL
    assert data["name"] == "Automated Tester"
    assert data["phone"] == "9998887771"
    assert data["default_address"] == "404 Main Street, Bengaluru"
    assert "id" in data
    assert "password" not in data       # Sensitive field security check
    assert "password_hash" not in data  # Sensitive field security check


def test_register_duplicate_email_fails():
    """
    Edge Case: Registering an account with an email that is already taken.
    Expects: HTTP 400 Bad Request.
    """
    payload = {
        "name": "Imposter Tester",
        "email": TEST_EMAIL,
        "password": "AnotherPassword456",
        "phone": "9998887772"
    }

    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


def test_login_wrong_password_fails():
    """
    Edge Case: Attempting login with an incorrect password.
    Expects: HTTP 401 Unauthorized.
    """
    payload = {
        "email": TEST_EMAIL,
        "password": "CompletelyWrongPassword!"
    }

    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 401
    assert "invalid email or password" in response.json()["detail"].lower()


def test_login_success_returns_jwt():
    """
    Happy Path: Logging in with valid credentials.
    Expects: HTTP 200 OK, a valid JWT access_token, and serialized default_address.
    """
    payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }

    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == TEST_EMAIL
    assert data["user"]["default_address"] == "404 Main Street, Bengaluru"


# =============================================================
# 3. ONBOARDING PROFILE MANAGEMENT TESTS (PUT /api/auth/profile)
# =============================================================

def test_update_profile_unauthenticated_fails():
    """
    Security Test: Attempting to update a profile without a valid JWT token.
    Expects: HTTP 401 Unauthorized with credentials validation error.
    """
    payload = {
        "name": "Hacker Name",
        "phone": "9876543210",
        "default_address": "Unauthorized Address"
    }

    response = client.put("/api/auth/profile", json=payload)
    assert response.status_code == 401

    # Checks for the actual detail string raised by get_current_user in security.py
    detail_lower = response.json()["detail"].lower()
    assert "credentials" in detail_lower or "not authenticated" in detail_lower


def test_update_user_profile_success():
    """
    Happy Path: Authenticated user updates their Full Name, Phone, and Default Address.
    Expects: HTTP 200 OK with mutated fields reflected in the response.
    """
    # 1. Obtain an authenticated JWT token
    login_res = client.post("/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Mutate profile via PUT /api/auth/profile
    update_payload = {
        "name": "Shylendhar Mohan",
        "phone": "9123456789",
        "default_address": "Tower 4, Flat 102, Palm Meadows, Bengaluru, 560066"
    }

    update_res = client.put("/api/auth/profile", json=update_payload, headers=headers)
    assert update_res.status_code == 200

    updated_user = update_res.json()
    assert updated_user["name"] == "Shylendhar Mohan"
    assert updated_user["phone"] == "9123456789"
    assert updated_user["default_address"] == "Tower 4, Flat 102, Palm Meadows, Bengaluru, 560066"
    assert updated_user["email"] == TEST_EMAIL


def test_profile_persistence_via_get_me():
    """
    Persistence Test: Verifies that the profile mutation was truly committed
    to MySQL and is reflected when calling GET /api/auth/me.
    """
    login_res = client.post("/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200

    me_data = me_res.json()
    assert me_data["name"] == "Shylendhar Mohan"
    assert me_data["phone"] == "9123456789"
    assert me_data["default_address"] == "Tower 4, Flat 102, Palm Meadows, Bengaluru, 560066"


def test_update_profile_validation_errors():
    """
    Contract Validation Test: Verifies that Pydantic rejects payloads that
    violate schema constraints (e.g. name < 2 chars, address < 5 chars).
    Expects: HTTP 422 Unprocessable Entity.
    """
    login_res = client.post("/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Case A: Name is too short (min_length=2)
    invalid_name_payload = {
        "name": "A",
        "phone": "9123456789",
        "default_address": "Valid Address Long Enough"
    }
    res_a = client.put("/api/auth/profile", json=invalid_name_payload, headers=headers)
    assert res_a.status_code == 422

    # Case B: Address is too short (min_length=5)
    invalid_address_payload = {
        "name": "Valid Name",
        "phone": "9123456789",
        "default_address": "123"
    }
    res_b = client.put("/api/auth/profile", json=invalid_address_payload, headers=headers)
    assert res_b.status_code == 422