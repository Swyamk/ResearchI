"""
Analytics API routes: daily, weekly, monthly, dashboard, trends.
"""
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Query

from app.core.dependencies import DB, CurrentUser
from app.schemas.analytics import (
    DailySnapshot,
    DashboardSummary,
    DeficiencyReport,
    MonthlyReport,
    NutritionTrend,
    StreakData,
    WeeklySummary,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard(current_user: CurrentUser, db: DB):
    """
    Get complete dashboard data for today including:
    calories, macros, goals, streak, recommendations.
    """
    service = AnalyticsService(db)
    return await service.get_dashboard_summary(current_user)


@router.get("/daily", response_model=DailySnapshot)
async def get_daily_snapshot(
    current_user: CurrentUser,
    db: DB,
    target_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
):
    """Get daily nutrition snapshot for a specific date (defaults to today)."""
    service = AnalyticsService(db)
    parsed_date = date.fromisoformat(target_date) if target_date else date.today()
    return await service.get_daily_snapshot(current_user.id, parsed_date)


@router.get("/weekly", response_model=WeeklySummary)
async def get_weekly_summary(
    current_user: CurrentUser,
    db: DB,
    week_offset: int = Query(0, description="0=current week, 1=last week, etc."),
):
    """Get weekly nutrition summary."""
    service = AnalyticsService(db)
    return await service.get_weekly_summary(current_user.id, week_offset)


@router.get("/monthly", response_model=MonthlyReport)
async def get_monthly_report(
    current_user: CurrentUser,
    db: DB,
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
):
    """Get monthly nutrition report."""
    service = AnalyticsService(db)
    now = datetime.now(timezone.utc)
    return await service.get_monthly_report(
        current_user.id,
        year or now.year,
        month or now.month,
    )


@router.get("/trend", response_model=NutritionTrend)
async def get_nutrition_trend(
    current_user: CurrentUser,
    db: DB,
    days: int = Query(30, ge=7, le=365, description="Number of days to include"),
):
    """Get nutrition trend data for charting (last N days)."""
    service = AnalyticsService(db)
    return await service.get_nutrition_trend(current_user.id, days)


@router.get("/deficiencies", response_model=DeficiencyReport)
async def get_deficiency_report(
    current_user: CurrentUser,
    db: DB,
    days: int = Query(7, ge=1, le=30, description="Analysis window in days"),
):
    """Get nutrient deficiency analysis based on recent meals."""
    service = AnalyticsService(db)
    return await service.get_deficiency_report(current_user.id, days)


@router.get("/streak", response_model=StreakData)
async def get_streak(current_user: CurrentUser, db: DB):
    """Get current streak and consistency score."""
    service = AnalyticsService(db)
    return await service.get_streak_data(current_user.id)


@router.post("/sync")
async def sync_daily_analytics(current_user: CurrentUser, db: DB):
    """Manually trigger daily analytics recalculation for today."""
    service = AnalyticsService(db)
    await service.sync_daily_snapshot(current_user)
    return {"message": "Analytics synced successfully"}
