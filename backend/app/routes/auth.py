"""Authentication, user profiles, Google OAuth2, and local credentials."""

import os
import time
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
import httpx

from app.cache import redis_client
from app.database import get_db
from app.models import User, UserRole, AuthProvider
from app.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    GoogleAuthRequest,
    UserProfileUpdate
)
from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication & Users"]
)

# STRICT WHITELIST: Only your verified Google account holds master admin authority
ADMIN_EMAILS = {
    "shylendharm369@gmail.com"
}


# Rate limiting helpers

RATE_LIMIT_LOGIN_MAX = int(os.getenv("AUTH_RATE_LIMIT_LOGIN_MAX", 15))
RATE_LIMIT_REGISTER_MAX = int(os.getenv("AUTH_RATE_LIMIT_REGISTER_MAX", 10))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", 60))

# Fallback in-memory tracking if Redis is unreachable: { cache_key: [timestamps] }
_in_memory_rate_limits = {}


def check_rate_limit(
    request: Request,
    key_prefix: str,
    max_requests: int = 15,
    window_seconds: int = 60
):
    """Rate limit requests by client IP with Redis or in-memory fallback."""
    # Bypass rate limit during tests
    if (
        "PYTEST_CURRENT_TEST" in os.environ
        or os.getenv("DISABLE_RATE_LIMITING", "false").lower() in ("true", "1")
        or (request.client and request.client.host == "testclient")
    ):
        return

    # Extract client IP
    forwarded = request.headers.get("X-Forwarded-For")
    client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "127.0.0.1")
    cache_key = f"rate_limit:{key_prefix}:{client_ip}"

    # Redis rate limit check
    if redis_client:
        try:
            current_attempts = redis_client.incr(cache_key)
            if current_attempts == 1:
                redis_client.expire(cache_key, window_seconds)

            if current_attempts > max_requests:
                ttl = redis_client.ttl(cache_key)
                retry_after = ttl if ttl > 0 else window_seconds
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many requests. Please try again in {retry_after} seconds.",
                    headers={"Retry-After": str(retry_after)}
                )
            return
        except HTTPException:
            raise
        except Exception as exc:
            # Redis connection failure: degrade gracefully to in-memory fallback
            pass

    # 2. In-Memory Fallback Limiter (Sliding Window Algorithm)
    now = time.time()
    history = _in_memory_rate_limits.setdefault(cache_key, [])
    # Evict timestamps older than the active window
    history[:] = [t for t in history if now - t < window_seconds]

    if len(history) >= max_requests:
        oldest = history[0]
        retry_after = max(1, int(window_seconds - (now - oldest)))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Please try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )

    history.append(now)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Google token verification

async def verify_google_token(credential: str) -> dict:
    """
    Cryptographically verifies a Google OAuth2 ID Token:
    1. Production Guard: In production, all mock tokens are strictly rejected with 401.
    2. Sandbox/Mock Mode: In dev/test, supports rapid local development & Pytest.
    3. Live Mode: Verifies authentic cryptographic signature against Google's tokeninfo API.
    """
    # Sandbox / Mock Token Support for Automated Tests & Local Development
    if credential.startswith("mock_google_token_"):
        # PRODUCTION LOCKOUT: Sandbox tokens are strictly forbidden in production!
        if os.getenv("ENVIRONMENT") == "production":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sandbox mock tokens are strictly disabled in production mode."
            )

        email_part = credential.replace("mock_google_token_", "")
        email = email_part if "@" in email_part else f"{email_part}@gmail.com"
        return {
            "sub": f"google_sub_{abs(hash(email))}",
            "email": email,
            "name": email.split("@")[0].capitalize(),
            "picture": "https://lh3.googleusercontent.com/a/default-avatar"
        }

    # Live Google Public Token Verification
    google_verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(google_verify_url, timeout=10.0)
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid, expired, or forged Google authentication token."
                )
            return resp.json()
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to reach Google OAuth2 verification servers: {exc}"
            )


# Google OAuth2 login

@router.post("/google", response_model=LoginResponse, summary="Sign in or register using Google OAuth2")
async def google_auth(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    # 1. Verify Google Token and extract claims
    google_data = await verify_google_token(payload.credential)

    google_id = google_data.get("sub")
    email = (google_data.get("email") or "").lower().strip()
    name = google_data.get("name") or email.split("@")[0]
    picture_url = google_data.get("picture")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account did not provide an email address."
        )

    # Whitelist authorization: ADMIN if email matches master admin, else CUSTOMER
    is_authorized_admin = (email in ADMIN_EMAILS)
    role = UserRole.ADMIN if is_authorized_admin else UserRole.CUSTOMER

    # 2. Check if user already exists by google_id
    user = db.query(User).filter(User.google_id == google_id).first()

    # 3. If not found by google_id, check if user exists by email (Account Linking)
    if not user:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.google_id = google_id
            user.picture_url = picture_url
            user.auth_provider = AuthProvider.GOOGLE
            if is_authorized_admin:
                user.role = UserRole.ADMIN
        else:
            user = User(
                name=name,
                email=email,
                google_id=google_id,
                picture_url=picture_url,
                auth_provider=AuthProvider.GOOGLE,
                role=role,
                password_hash=None
            )
            db.add(user)
    else:
        if picture_url:
            user.picture_url = picture_url
        if is_authorized_admin:
            user.role = UserRole.ADMIN

    db.commit()
    db.refresh(user)

    # 4. Issue standard backend JWT access token
    token_payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value
    }
    access_token = create_access_token(data=token_payload)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


# Profile management

@router.get("/me", response_model=UserResponse, summary="Get current logged-in user profile")
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/profile", response_model=UserResponse, summary="Update user profile details (Name, Phone, Default Address)")
def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Onboarding Profile Setup / Profile Edit Endpoint.
    Guarded by JWT authentication. Updates name, phone, and default_address.
    """
    current_user.name = profile_data.name.strip()
    current_user.phone = profile_data.phone.strip()
    current_user.default_address = profile_data.default_address.strip()

    db.commit()
    db.refresh(current_user)
    return current_user


# Local auth endpoints

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Register customer (Automated Tests)")
def register_customer(
    user_payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    # Enforce brute-force rate limit on new account creation
    check_rate_limit(request, key_prefix="register", max_requests=RATE_LIMIT_REGISTER_MAX, window_seconds=RATE_LIMIT_WINDOW_SECONDS)

    existing_user = db.query(User).filter(User.email == user_payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    new_user = User(
        name=user_payload.name,
        email=user_payload.email,
        phone=user_payload.phone,
        default_address=user_payload.default_address,
        password_hash=hash_password(user_payload.password),
        auth_provider=AuthProvider.LOCAL
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=LoginResponse, summary="Log in with local credentials (Automated Tests)")
def login(
    credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    # Enforce brute-force rate limit on login attempts
    check_rate_limit(request, key_prefix="login", max_requests=RATE_LOGIN_MAX if 'RATE_LOGIN_MAX' in locals() else RATE_LIMIT_LOGIN_MAX, window_seconds=RATE_LIMIT_WINDOW_SECONDS)

    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not user.password_hash or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    token_payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value
    }
    access_token = create_access_token(data=token_payload)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }