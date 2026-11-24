"""
Security & Authentication Utilities
Location: backend/app/security.py

Handles Bcrypt password hashing, JWT creation/verification,
and FastAPI route protection dependencies (get_current_user, get_current_admin).
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# Import database session provider and ORM models
from app.database import get_db
from app.models import User, UserRole

# 1. Load secret environment variables
load_dotenv()

# Cryptographic Token Signing Key Configuration
FALLBACK_SECRET_KEY = "super-secret-fallback-key-change-in-production"
SECRET_KEY = os.getenv("JWT_SECRET_KEY", FALLBACK_SECRET_KEY)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()

# Enforce Cryptographic Production Boundary (SEC-04 Remediation)
# Fail-fast startup guard: Halt boot if running in production with a default or missing secret key
if ENVIRONMENT in ("production", "prod"):
    if not SECRET_KEY or SECRET_KEY == FALLBACK_SECRET_KEY:
        raise RuntimeError(
            "CRITICAL SECURITY CONFIGURATION ERROR: JWT_SECRET_KEY environment variable "
            "must be explicitly configured with a cryptographically secure secret in production mode. "
            "Server startup halted to prevent JWT signature forgery."
        )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # Tokens stay valid for 24 hours

# 2. Setup the Bcrypt password hashing engine
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 3. OAuth2 Scheme: Instructs FastAPI to look for 'Authorization: Bearer <token>' in HTTP headers.
# auto_error=False allows optional authentication (e.g., guest checkouts) without crashing immediately.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# =============================================================
# PASSWORD HASHING FUNCTIONS
# =============================================================

def hash_password(plain_password: str) -> str:
    """
    Takes a plain password (e.g., 'secret123') and returns
    a salted, irreversible bcrypt hash (e.g., '$2b$12$e8...').
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compares a plain password typed during login against
    the stored hash in MySQL. Returns True if correct, False if wrong.
    """
    return pwd_context.verify(plain_password, hashed_password)


# =============================================================
# JWT (JSON WEB TOKEN) CREATION
# =============================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a tamper-proof digital login passport (JWT) for the user.
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# =============================================================
# AUTHENTICATION & RBAC DEPENDENCIES (THE GATEKEEPERS)
# =============================================================

def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Mandatory Authentication Guard:
    1. Extracts the Bearer token from the HTTP Authorization header.
    2. Decodes and cryptographically verifies the token using SECRET_KEY.
    3. Fetches the authenticated User from MySQL.
    4. Raises 401 Unauthorized if token is missing, expired, or invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or session expired. Please log in.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    try:
        # Decode the token and check expiration & signature
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    # Query the user in the database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional Authentication Guard:
    If a valid token is provided, returns the logged-in User.
    If no token is sent (guest user), returns None cleanly without throwing an error.
    Used for checkout: guests can order, but logged-in users get their order linked!
    """
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("sub")
        if not user_id_str:
            return None
        user_id = int(user_id_str)
        return db.query(User).filter(User.id == user_id).first()
    except Exception:
        return None


def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Role-Based Access Control (RBAC) Guard:
    1. First ensures the user is legitimately logged in via get_current_user.
    2. Verifies whether user.role == UserRole.ADMIN.
    3. Raises 403 Forbidden if a regular customer tries to access admin-only data!
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have restaurant administrator privileges."
        )
    return current_user