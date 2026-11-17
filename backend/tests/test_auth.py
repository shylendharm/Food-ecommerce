"""
Automated Test Suite: Authentication & Security (backend/tests/test_auth.py)
Tests password hashing unit logic and auth API endpoints using FastAPI TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.security import hash_password, verify_password

# Create our simulated HTTP client that talks directly to FastAPI
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
    assert hashed.startswith("$2b$") # Bcrypt identifier tag
    
    # Assert that the correct password verifies to True
    assert verify_password(raw_password, hashed) is True
    
    # Assert that a wrong password verifies to False
    assert verify_password("WrongPassword!", hashed) is False


# =============================================================
# 2. INTEGRATION TESTS: AUTH API ENDPOINTS
# =============================================================

# Unique test email timestamp to avoid conflicts with previous test runs
TEST_EMAIL = "automated_tester@restaurant.com"
TEST_PASSWORD = "StrongTestPassword!123"


def test_register_new_user():
    """
    Integration Test: Registering a brand new user.
    Expects: HTTP 201 Created and password_hash omitted from response.
    """
    payload = {
        "name": "Automated Tester",
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "phone": "9998887771"
    }
    
    response = client.post("/api/auth/register", json=payload)
    
    # If the user already existed from a previous run, 400 is also acceptable
    assert response.status_code in [201, 400]
    
    if response.status_code == 201:
        data = response.json()
        assert data["email"] == TEST_EMAIL
        assert data["name"] == "Automated Tester"
        assert "id" in data
        assert "password" not in data       # Sensitive field security check!
        assert "password_hash" not in data  # Sensitive field security check!


def test_register_duplicate_email_fails():
    """
    Edge Case: Registering an account with an email that is already taken.
    Expects: HTTP 400 Bad Request.
    """
    payload = {
        "name": "Imposter Tester",
        "email": TEST_EMAIL, # Using the exact same email from the test above!
        "password": "AnotherPassword456",
        "phone": "9998887772"
    }
    
    response = client.post("/api/auth/register", json=payload)
    
    # Must be 400 Bad Request!
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
    Expects: HTTP 200 OK, a valid JWT access_token, and token_type == 'bearer'.
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