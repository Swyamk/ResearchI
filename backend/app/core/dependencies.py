"""
FastAPI dependencies for authentication, rate limiting, and database access.
"""
from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_user_id_from_token
from app.database import get_db
from app.models.user import User
from app.redis_client import redis_client
from app.config import settings

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Get authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id = get_user_id_from_token(credentials.credentials, token_type="access")
    if not user_id:
        raise credentials_exception

    # Check if token is blacklisted
    if await redis_client.exists(f"blacklist:{credentials.credentials}"):
        raise credentials_exception

    # Load user with profile
    result = await db.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.profile))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


async def get_current_superuser(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


async def rate_limit(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Apply per-user rate limiting."""
    key = f"rate_limit:{current_user.id}:{request.url.path}"
    is_allowed, remaining = await redis_client.rate_limit_check(
        key, settings.RATE_LIMIT_PER_MINUTE
    )
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"X-RateLimit-Remaining": str(remaining)},
        )


async def ai_rate_limit(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Apply stricter rate limiting for AI endpoints."""
    key = f"ai_rate_limit:{current_user.id}"
    is_allowed, remaining = await redis_client.rate_limit_check(
        key, settings.AI_RATE_LIMIT_PER_MINUTE
    )
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="AI rate limit exceeded. Please wait before making another AI request.",
            headers={"X-RateLimit-Remaining": str(remaining)},
        )


# Type aliases
CurrentUser = Annotated[User, Depends(get_current_user)]
ActiveUser = Annotated[User, Depends(get_current_active_user)]
SuperUser = Annotated[User, Depends(get_current_superuser)]
DB = Annotated[AsyncSession, Depends(get_db)]
