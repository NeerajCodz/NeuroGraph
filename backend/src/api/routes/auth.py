"""Authentication routes."""

from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field

from src.auth.jwt import create_access_token, create_refresh_token, verify_token
from src.auth.passwords import hash_password, verify_password
from src.core.config import get_settings
from src.core.exceptions import AuthenticationError

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class UserCreate(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None


class UserResponse(BaseModel):
    """User response model."""
    id: UUID
    email: str
    full_name: str | None
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate) -> UserResponse:
    """Register a new user."""
    # TODO: Implement user registration with database
    from uuid import uuid4
    
    # Placeholder implementation
    return UserResponse(
        id=uuid4(),
        email=user_data.email,
        full_name=user_data.full_name,
        is_active=True,
        created_at=datetime.utcnow(),
    )


@router.post("/login", response_model=TokenResponse)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> TokenResponse:
    """Login and get access token."""
    from src.db.postgres import get_postgres_driver
    import bcrypt
    
    settings = get_settings()
    postgres = get_postgres_driver()
    
    # Validate credentials against database
    user = await postgres.fetchrow(
        "SELECT id, email, hashed_password FROM auth.users WHERE email = $1",
        form_data.username,
    )
    
    if not user:
        raise AuthenticationError("Invalid email or password")
    
    # Verify password
    if not bcrypt.checkpw(
        form_data.password.encode('utf-8'),
        user["hashed_password"].encode('utf-8'),
    ):
        raise AuthenticationError("Invalid email or password")
    
    access_token = create_access_token(
        data={"sub": str(user["id"]), "email": user["email"], "type": "access"},
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user["id"]), "type": "refresh"},
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest) -> TokenResponse:
    """Refresh access token."""
    settings = get_settings()
    
    payload = verify_token(request.refresh_token)
    if payload.get("type") != "refresh":
        raise AuthenticationError("Invalid refresh token")
    
    access_token = create_access_token(
        data={"sub": payload["sub"], "type": "access"},
    )
    new_refresh_token = create_refresh_token(
        data={"sub": payload["sub"], "type": "refresh"},
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> UserResponse:
    """Get current authenticated user."""
    from src.db.postgres import get_postgres_driver
    from uuid import UUID
    
    payload = verify_token(token)
    user_id = payload["sub"]
    
    # Fetch user from database
    postgres = get_postgres_driver()
    user = await postgres.fetchrow(
        "SELECT id, email, full_name, is_active, created_at FROM auth.users WHERE id = $1",
        UUID(user_id),
    )
    
    if not user:
        raise AuthenticationError("User not found")
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        full_name=user["full_name"],
        is_active=user["is_active"],
        created_at=user["created_at"],
    )


@router.post("/logout")
async def logout(token: Annotated[str, Depends(oauth2_scheme)]) -> dict[str, str]:
    """Logout (invalidate token)."""
    # TODO: Add token to blacklist in Redis
    return {"message": "Successfully logged out"}
