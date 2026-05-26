"""
JWT Security utilities: token creation, validation, password hashing.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import bcrypt as _bcrypt
from jose import JWTError, jwt

from app.config import settings


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode()[:72], _bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode()[:72], hashed.encode())


def create_access_token(user_id: UUID, extra_claims: dict = None) -> str:
    """Create a JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: UUID) -> str:
    """Create a JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None


def get_user_id_from_token(token: str, token_type: str = "access") -> Optional[UUID]:
    """Extract user ID from token."""
    payload = decode_token(token, token_type)
    if not payload:
        return None
    try:
        return UUID(payload["sub"])
    except (KeyError, ValueError):
        return None
