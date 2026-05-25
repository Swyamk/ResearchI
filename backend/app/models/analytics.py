"""
Analytics models for the Nutrition Memory Engine.
"""
import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DailyNutritionSnapshot(Base):
    """
    Aggregated daily nutrition totals (Nutrition Memory Engine).
    One row per user per day.
    """
    __tablename__ = "daily_nutrition_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Meal counts
    meals_logged: Mapped[int] = mapped_column(Integer, default=0)
    total_meals_target: Mapped[int] = mapped_column(Integer, default=3)

    # Macros (actual vs target)
    calories_actual: Mapped[float] = mapped_column(Float, default=0.0)
    calories_target: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    protein_g_actual: Mapped[float] = mapped_column(Float, default=0.0)
    protein_g_target: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    carbs_g_actual: Mapped[float] = mapped_column(Float, default=0.0)
    carbs_g_target: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fat_g_actual: Mapped[float] = mapped_column(Float, default=0.0)
    fat_g_target: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fiber_g_actual: Mapped[float] = mapped_column(Float, default=0.0)
    fiber_g_target: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sugar_g_actual: Mapped[float] = mapped_column(Float, default=0.0)
    sodium_mg_actual: Mapped[float] = mapped_column(Float, default=0.0)
    water_ml_actual: Mapped[float] = mapped_column(Float, default=0.0)
    water_ml_target: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Key micronutrients
    vitamin_c_mg: Mapped[float] = mapped_column(Float, default=0.0)
    vitamin_d_mcg: Mapped[float] = mapped_column(Float, default=0.0)
    calcium_mg: Mapped[float] = mapped_column(Float, default=0.0)
    iron_mg: Mapped[float] = mapped_column(Float, default=0.0)
    omega3_g: Mapped[float] = mapped_column(Float, default=0.0)

    # Scores
    nutrition_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100
    goal_achievement_pct: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100

    # Deficiencies detected (list of nutrient names)
    deficiencies: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Meal breakdown by type
    meal_breakdown: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="analytics")


class WeeklyNutritionSummary(Base):
    """Aggregated weekly nutrition summary."""
    __tablename__ = "weekly_nutrition_summaries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    week_end: Mapped[date] = mapped_column(Date, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Weekly averages
    avg_daily_calories: Mapped[float] = mapped_column(Float, default=0.0)
    avg_daily_protein_g: Mapped[float] = mapped_column(Float, default=0.0)
    avg_daily_carbs_g: Mapped[float] = mapped_column(Float, default=0.0)
    avg_daily_fat_g: Mapped[float] = mapped_column(Float, default=0.0)
    avg_daily_fiber_g: Mapped[float] = mapped_column(Float, default=0.0)
    avg_daily_sugar_g: Mapped[float] = mapped_column(Float, default=0.0)
    avg_daily_water_ml: Mapped[float] = mapped_column(Float, default=0.0)

    # Weekly totals
    total_meals_logged: Mapped[int] = mapped_column(Integer, default=0)
    days_logged: Mapped[int] = mapped_column(Integer, default=0)
    consistency_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Trends
    calorie_trend: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # "improving" | "stable" | "declining"
    weight_change_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Top foods and deficiencies
    top_foods: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    recurring_deficiencies: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ai_summary: Mapped[Optional[str]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MonthlyNutritionReport(Base):
    """Comprehensive monthly nutrition report."""
    __tablename__ = "monthly_nutrition_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)

    # Monthly averages
    avg_daily_calories: Mapped[float] = mapped_column(Float, default=0.0)
    avg_daily_protein_g: Mapped[float] = mapped_column(Float, default=0.0)
    avg_daily_carbs_g: Mapped[float] = mapped_column(Float, default=0.0)
    avg_daily_fat_g: Mapped[float] = mapped_column(Float, default=0.0)

    # Progress
    total_meals_logged: Mapped[int] = mapped_column(Integer, default=0)
    days_logged: Mapped[int] = mapped_column(Integer, default=0)
    consistency_score: Mapped[float] = mapped_column(Float, default=0.0)
    streak_best: Mapped[int] = mapped_column(Integer, default=0)
    goal_achievement_pct: Mapped[float] = mapped_column(Float, default=0.0)

    # Body metrics
    weight_start_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weight_end_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weight_change_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Insights
    top_achievements: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    areas_for_improvement: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ai_monthly_summary: Mapped[Optional[str]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# Convenience alias for import in database.py
NutritionAnalytics = DailyNutritionSnapshot
