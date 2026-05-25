"""
Authentication API routes: register, login, refresh, logout, Google OAuth.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import DB, CurrentUser
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_user_id_from_token,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models.user import User, UserProfile
from app.redis_client import redis_client
from app.schemas.user import Token, TokenRefresh, UserLogin, UserRegister, UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, db: DB):
    """Register a new user with email and password."""
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        is_verified=False,
    )
    db.add(user)
    await db.flush()

    # Create empty profile
    profile = UserProfile(user_id=user.id)
    db.add(profile)
    await db.commit()
    await db.refresh(user)

    return user


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, db: DB):
    """Login with email and password, returns JWT tokens."""
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disabled",
        )

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # Cache refresh token in Redis
    await redis_client.set(
        f"refresh:{str(user.id)}",
        refresh_token,
        ttl=30 * 24 * 3600,  # 30 days
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=3600,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(payload: TokenRefresh, db: DB):
    """Refresh access token using refresh token."""
    user_id = get_user_id_from_token(payload.refresh_token, token_type="refresh")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Validate refresh token matches cached one
    cached = await redis_client.get(f"refresh:{str(user_id)}")
    if cached != payload.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked",
        )

    # Verify user still exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    new_access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)

    # Rotate refresh token
    await redis_client.set(f"refresh:{str(user.id)}", new_refresh_token, ttl=30 * 24 * 3600)

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=3600,
    )


@router.post("/logout")
async def logout(current_user: CurrentUser, db: DB):
    """Logout: revoke tokens."""
    await redis_client.delete(f"refresh:{str(current_user.id)}")
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    """Get current authenticated user's info."""
    return current_user


@router.get("/google")
async def google_auth_redirect():
    """Redirect to Google OAuth consent screen."""
    auth_service = AuthService()
    url = auth_service.get_google_auth_url()
    return {"auth_url": url}


@router.get("/google/callback", response_model=Token)
async def google_auth_callback(code: str, db: DB):
    """Handle Google OAuth callback and issue tokens."""
    auth_service = AuthService()
    user = await auth_service.handle_google_callback(code, db)

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    await redis_client.set(f"refresh:{str(user.id)}", refresh_token, ttl=30 * 24 * 3600)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=3600,
    )
