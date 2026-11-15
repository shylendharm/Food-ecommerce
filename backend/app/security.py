import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

# 1. Load secret environment variables
load_dotenv()

# The secret key used to digitally sign our login tokens (like a wax seal on a royal letter)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-fallback-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # Tokens stay valid for 24 hours

# 2. Setup the Bcrypt password hashing engine
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
# JWT (JSON WEB TOKEN) FUNCTIONS
# =============================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a tamper-proof digital login passport (JWT) for the user.
    """
    to_encode = data.copy()

    # Set the expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # 'exp' is a standard JWT claim for expiration timestamp
    to_encode.update({"exp": expire})

    # Digitally sign the token using our SECRET_KEY and HS256 algorithm
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt