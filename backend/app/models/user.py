"""
User and UserProfile SQLAlchemy models.
"""
import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"
    prefer_not_to_say = "prefer_not_to_say"


class ActivityLevel(str, enum.Enum):
    sedentary = "sedentary"          # Little or no exercise
    lightly_active = "lightly_active"  # Light exercise 1-3 days/week
    moderately_active = "moderately_active"  # Moderate exercise 3-5 days/week
    very_active = "very_active"       # Hard exercise 6-7 days/week
    extremely_active = "extremely_active"  # Very hard exercise + physical job


class HealthGoal(str, enum.Enum):
    weight_loss = "weight_loss"
    muscle_gain = "muscle_gain"
    maintenance = "maintenance"
    diabetes_management = "diabetes_management"
    heart_health = "heart_health"
    general_wellness = "general_wellness"
    athletic_performance = "athletic_performance"
    gut_health = "gut_health"


class HealthCondition(str, enum.Enum):
    diabetes_type1 = "diabetes_type1"
    diabetes_type2 = "diabetes_type2"
    hypertension = "hypertension"
    high_cholesterol = "high_cholesterol"
    pcos = "pcos"
    thyroid = "thyroid"
    kidney_disease = "kidney_disease"
    celiac = "celiac"
    lactose_intolerance = "lactose_intolerance"
    none = "none"


class AuthProvider(str, enum.Enum):
    email = "email"
    google = "google"


class User(Base):
    """User authentication model."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    auth_provider: Mapped[AuthProvider] = mapped_column(
        Enum(AuthProvider), default=AuthProvider.email
    )
    google_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    meals: Mapped[List["Meal"]] = relationship(
        "Meal", back_populates="user", cascade="all, delete-orphan"
    )
    analytics: Mapped[List["NutritionAnalytics"]] = relationship(
        "NutritionAnalytics", back_populates="user", cascade="all, delete-orphan"
    )
    ai_conversations: Mapped[List["AIConversation"]] = relationship(
        "AIConversation", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class UserProfile(Base):
    """User health profile with goals, conditions, and biometrics."""
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )

    # Biometrics
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gender: Mapped[Optional[Gender]] = mapped_column(Enum(Gender), nullable=True)
    height_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Computed fields (updated on profile save)
    bmi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bmr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)   # Basal Metabolic Rate
    tdee: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Total Daily Energy Expenditure

    # Lifestyle
    activity_level: Mapped[Optional[ActivityLevel]] = mapped_column(Enum(ActivityLevel), nullable=True)
    primary_goal: Mapped[Optional[HealthGoal]] = mapped_column(Enum(HealthGoal), nullable=True)

    # Health conditions (stored as JSON array of enum strings)
    health_conditions: Mapped[Optional[list]] = mapped_column(ARRAY(String), default=list)

    # Dietary preferences & restrictions
    dietary_restrictions: Mapped[Optional[list]] = mapped_column(ARRAY(String), default=list)
    allergies: Mapped[Optional[list]] = mapped_column(ARRAY(String), default=list)
    cuisine_preferences: Mapped[Optional[list]] = mapped_column(ARRAY(String), default=list)

    # Daily targets (calculated from TDEE + goals)
    daily_calorie_target: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    daily_protein_target_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    daily_carb_target_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    daily_fat_target_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    daily_fiber_target_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    daily_water_target_ml: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Gamification
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    total_meals_logged: Mapped[int] = mapped_column(Integer, default=0)
    consistency_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Metadata
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="profile")

    def calculate_bmi(self) -> Optional[float]:
        """Calculate BMI from height and weight."""
        if self.height_cm and self.weight_kg:
            height_m = self.height_cm / 100
            self.bmi = round(self.weight_kg / (height_m ** 2), 1)
            return self.bmi
        return None

    def calculate_bmr(self) -> Optional[float]:
        """Calculate Basal Metabolic Rate using Mifflin-St Jeor equation."""
        if all([self.weight_kg, self.height_cm, self.age, self.gender]):
            if self.gender == Gender.male:
                self.bmr = (10 * self.weight_kg) + (6.25 * self.height_cm) - (5 * self.age) + 5
            else:
                self.bmr = (10 * self.weight_kg) + (6.25 * self.height_cm) - (5 * self.age) - 161
            return self.bmr
        return None

    def calculate_tdee(self) -> Optional[float]:
        """Calculate Total Daily Energy Expenditure."""
        if not self.bmr:
            self.calculate_bmr()
        if self.bmr and self.activity_level:
            multipliers = {
                ActivityLevel.sedentary: 1.2,
                ActivityLevel.lightly_active: 1.375,
                ActivityLevel.moderately_active: 1.55,
                ActivityLevel.very_active: 1.725,
                ActivityLevel.extremely_active: 1.9,
            }
            self.tdee = round(self.bmr * multipliers.get(self.activity_level, 1.2))
            return self.tdee
        return None


class AIConversation(Base):
    """AI Coach conversation history."""
    __tablename__ = "ai_conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="ai_conversations")
