from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Import our database provider, ORM models, and Pydantic schemas
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserLogin, UserResponse
from app.security import hash_password, verify_password, create_access_token

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication & Users"]
)


# Schema representing the successful login token response
class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Register a new customer account")
def register_user(user_payload: UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new user:
    1. Checks if the email is already in use.
    2. Hashes the password using Bcrypt.
    3. Saves the user to MySQL.
    4. Returns safe public user info (password hash is omitted).
    """
    # Step 1: Check for duplicate email
    existing_user = db.query(User).filter(User.email == user_payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Step 2: Hash the password securely
    hashed_pwd = hash_password(user_payload.password)

    # Step 3: Create the User ORM object
    new_user = User(
        name=user_payload.name,
        email=user_payload.email,
        phone=user_payload.phone,
        password_hash=hashed_pwd
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=LoginResponse, summary="Log in and receive a JWT access token")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticates a user:
    1. Looks up the user by email.
    2. Verifies the password using the bcrypt hash.
    3. Issues a signed 24-hour JWT access token.
    """
    # Step 1: Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()

    # Step 2: Verify password
    # Security note: Return the same generic error whether the email doesn't exist OR the password is wrong!
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # Step 3: Create the JWT login token
    token_payload = {
        "sub": str(user.id),       # 'sub' (subject) standard claim: the user's primary key
        "email": user.email,
        "role": user.role.value
    }
    access_token = create_access_token(data=token_payload)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }