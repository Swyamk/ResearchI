"""
Pydantic schemas for Analytics endpoints.
"""
import uuid
from datetime import date, datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class DailySnapshot(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    snapshot_date: date
    meals_logged: int
    calories_actual: float
    calories_target: Optional[float]
    protein_g_actual: float
    protein_g_target: Optional[float]
    carbs_g_actual: float
    fat_g_actual: float
    fiber_g_actual: float
    sugar_g_actual: float
    sodium_mg_actual: float
    water_ml_actual: float
    nutrition_score: float
    goal_achievement_pct: float
    deficiencies: Optional[Dict]


class WeeklySummary(BaseModel):
    model_config = {"from_attributes": True}

    week_start: date
    week_end: date
    week_number: int
    avg_daily_calories: float
    avg_daily_protein_g: float
    avg_daily_carbs_g: float
    avg_daily_fat_g: float
    avg_daily_fiber_g: float
    avg_daily_sugar_g: float
    avg_daily_water_ml: float
    total_meals_logged: int
    days_logged: int
    consistency_score: float
    calorie_trend: Optional[str]
    weight_change_kg: Optional[float]
    top_foods: Optional[Dict]
    recurring_deficiencies: Optional[Dict]
    ai_summary: Optional[str]


class MonthlyReport(BaseModel):
    model_config = {"from_attributes": True}

    year: int
    month: int
    avg_daily_calories: float
    avg_daily_protein_g: float
    total_meals_logged: int
    days_logged: int
    consistency_score: float
    streak_best: int
    goal_achievement_pct: float
    weight_start_kg: Optional[float]
    weight_end_kg: Optional[float]
    weight_change_kg: Optional[float]
    top_achievements: Optional[Dict]
    areas_for_improvement: Optional[Dict]
    ai_monthly_summary: Optional[str]


class NutritionTrend(BaseModel):
    """Trend data for charting."""
    dates: List[date]
    calories: List[float]
    protein_g: List[float]
    carbs_g: List[float]
    fat_g: List[float]
    fiber_g: List[float]
    sugar_g: List[float]


class MacroBreakdown(BaseModel):
    """Macro percentage breakdown."""
    protein_pct: float
    carbs_pct: float
    fat_pct: float
    protein_g: float
    carbs_g: float
    fat_g: float
    total_calories: float


class DeficiencyReport(BaseModel):
    """Nutrient deficiency analysis."""
    deficient_nutrients: List[Dict]
    borderline_nutrients: List[Dict]
    sufficient_nutrients: List[str]
    recommendations: List[str]


class StreakData(BaseModel):
    current_streak: int
    longest_streak: int
    consistency_score: float
    total_days_logged: int
    last_log_date: Optional[date]


class DashboardSummary(BaseModel):
    """Complete dashboard data for today."""
    today_calories: float
    calorie_target: Optional[float]
    calorie_pct: float
    today_protein_g: float
    today_carbs_g: float
    today_fat_g: float
    today_fiber_g: float
    today_sugar_g: float
    today_water_ml: float
    meals_today: int
    nutrition_score: float
    streak: StreakData
    macro_breakdown: MacroBreakdown
    weekly_trend: NutritionTrend
    deficiencies: DeficiencyReport
    top_recommendations: List[str]
