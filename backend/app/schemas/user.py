"""
Pydantic schemas for User and authentication endpoints.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import ActivityLevel, AuthProvider, Gender, HealthCondition, HealthGoal


# ── Auth Schemas ──────────────────────────────────────────────────────────────
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    refresh_token: str


class GoogleAuthCallback(BaseModel):
    code: str
    state: Optional[str] = None


# ── User Profile Schemas ──────────────────────────────────────────────────────
class UserProfileUpdate(BaseModel):
    age: Optional[int] = Field(None, ge=1, le=120)
    gender: Optional[Gender] = None
    height_cm: Optional[float] = Field(None, ge=50, le=300)
    weight_kg: Optional[float] = Field(None, ge=10, le=500)
    target_weight_kg: Optional[float] = Field(None, ge=10, le=500)
    activity_level: Optional[ActivityLevel] = None
    primary_goal: Optional[HealthGoal] = None
    health_conditions: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    cuisine_preferences: Optional[List[str]] = None
    daily_water_target_ml: Optional[float] = Field(None, ge=500, le=10000)


class UserProfileResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    age: Optional[int]
    gender: Optional[Gender]
    height_cm: Optional[float]
    weight_kg: Optional[float]
    target_weight_kg: Optional[float]
    bmi: Optional[float]
    bmr: Optional[float]
    tdee: Optional[float]
    activity_level: Optional[ActivityLevel]
    primary_goal: Optional[HealthGoal]
    health_conditions: Optional[List[str]]
    dietary_restrictions: Optional[List[str]]
    allergies: Optional[List[str]]
    cuisine_preferences: Optional[List[str]]
    daily_calorie_target: Optional[float]
    daily_protein_target_g: Optional[float]
    daily_carb_target_g: Optional[float]
    daily_fat_target_g: Optional[float]
    daily_fiber_target_g: Optional[float]
    daily_water_target_ml: Optional[float]
    streak_days: int
    total_meals_logged: int
    consistency_score: float
    onboarding_completed: bool
    updated_at: datetime


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    full_name: str
    avatar_url: Optional[str]
    auth_provider: AuthProvider
    is_active: bool
    is_verified: bool
    created_at: datetime
    profile: Optional[UserProfileResponse]


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    avatar_url: Optional[str] = None


class ChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)
