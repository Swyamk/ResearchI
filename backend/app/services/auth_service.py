"""
Auth Service – Google OAuth handling and user management.
"""
from typing import Optional

import httpx
from authlib.integrations.starlette_client import OAuth
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import AuthProvider, User, UserProfile


class AuthService:
    """Handles Google OAuth and user creation."""

    def __init__(self):
        self.oauth = OAuth()
        self.oauth.register(
            name="google",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )

    def get_google_auth_url(self) -> str:
        """Generate Google OAuth authorization URL."""
        base_url = "https://accounts.google.com/o/oauth2/auth"
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{base_url}?{query}"

    async def exchange_code_for_tokens(self, code: str) -> dict:
        """Exchange authorization code for Google tokens."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_google_user_info(self, access_token: str) -> dict:
        """Get Google user info from access token."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()

    async def handle_google_callback(self, code: str, db: AsyncSession) -> User:
        """Process Google OAuth callback: get/create user."""
        tokens = await self.exchange_code_for_tokens(code)
        user_info = await self.get_google_user_info(tokens["access_token"])

        google_id = user_info["id"]
        email = user_info["email"]
        full_name = user_info.get("name", email.split("@")[0])
        avatar_url = user_info.get("picture")

        # Check if user exists by Google ID
        result = await db.execute(select(User).where(User.google_id == google_id))
        user = result.scalar_one_or_none()

        if not user:
            # Check by email (user may have registered with email before)
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

            if user:
                # Link Google account to existing user
                user.google_id = google_id
                user.avatar_url = avatar_url or user.avatar_url
                user.auth_provider = AuthProvider.google
            else:
                # Create new user
                user = User(
                    email=email,
                    full_name=full_name,
                    avatar_url=avatar_url,
                    google_id=google_id,
                    auth_provider=AuthProvider.google,
                    is_verified=True,  # Google verifies email
                )
                db.add(user)
                await db.flush()

                # Create empty profile
                profile = UserProfile(user_id=user.id)
                db.add(profile)

        await db.commit()
        await db.refresh(user)
        return user
