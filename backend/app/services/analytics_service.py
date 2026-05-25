"""
Analytics Service – Nutrition Memory Engine.
Aggregates daily/weekly/monthly nutrition data and computes trends.
"""
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.analytics import (
    DailyNutritionSnapshot,
    MonthlyNutritionReport,
    WeeklyNutritionSummary,
)
from app.models.meal import FoodItem, Meal
from app.models.user import User, UserProfile
from app.redis_client import redis_client
from app.schemas.analytics import (
    DailySnapshot,
    DashboardSummary,
    DeficiencyReport,
    MacroBreakdown,
    MonthlyReport,
    NutritionTrend,
    StreakData,
    WeeklySummary,
)


# Reference Daily Intakes (WHO/ICMR guidelines)
RDI = {
    "vitamin_c_mg": 65,
    "vitamin_d_mcg": 15,
    "calcium_mg": 1000,
    "iron_mg": 18,
    "fiber_g": 25,
    "omega3_g": 1.6,
    "potassium_mg": 3500,
    "magnesium_mg": 310,
    "zinc_mg": 8,
    "sodium_mg": 2300,  # upper limit
}


class AnalyticsService:
    """Nutrition Memory Engine – tracks trends, deficiencies, and consistency."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def sync_daily_snapshot(self, user: User) -> DailyNutritionSnapshot:
        """Aggregate today's meals into a daily snapshot (upsert)."""
        today = date.today()

        # Get today's meals
        result = await self.db.execute(
            select(Meal)
            .where(
                Meal.user_id == user.id,
                func.date(Meal.meal_time) == today,
                Meal.analysis_status == "completed",
            )
            .options(selectinload(Meal.food_items))
        )
        meals = result.scalars().all()

        # Aggregate totals
        totals = {
            "calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0,
            "fat_g": 0.0, "fiber_g": 0.0, "sugar_g": 0.0,
            "sodium_mg": 0.0, "vitamin_c_mg": 0.0, "vitamin_d_mcg": 0.0,
            "calcium_mg": 0.0, "iron_mg": 0.0, "omega3_g": 0.0,
        }

        for meal in meals:
            totals["calories"] += meal.total_calories or 0
            totals["protein_g"] += meal.total_protein_g or 0
            totals["carbs_g"] += meal.total_carbs_g or 0
            totals["fat_g"] += meal.total_fat_g or 0
            totals["fiber_g"] += meal.total_fiber_g or 0
            totals["sugar_g"] += meal.total_sugar_g or 0
            totals["sodium_mg"] += meal.total_sodium_mg or 0
            for item in meal.food_items:
                totals["vitamin_c_mg"] += item.vitamin_c_mg or 0
                totals["vitamin_d_mcg"] += item.vitamin_d_mcg or 0
                totals["calcium_mg"] += item.calcium_mg or 0
                totals["iron_mg"] += item.iron_mg or 0
                totals["omega3_g"] += item.omega3_g or 0

        # Get user targets
        profile = user.profile
        calorie_target = profile.daily_calorie_target if profile else None
        protein_target = profile.daily_protein_target_g if profile else None

        # Compute nutrition score (0-100)
        score = self._compute_nutrition_score(totals, profile)

        # Detect deficiencies
        deficiencies = self._detect_deficiencies(totals)

        # Find existing snapshot or create
        result = await self.db.execute(
            select(DailyNutritionSnapshot).where(
                DailyNutritionSnapshot.user_id == user.id,
                DailyNutritionSnapshot.snapshot_date == today,
            )
        )
        snapshot = result.scalar_one_or_none()

        if not snapshot:
            snapshot = DailyNutritionSnapshot(
                user_id=user.id, snapshot_date=today
            )
            self.db.add(snapshot)

        # Update snapshot
        snapshot.meals_logged = len(meals)
        snapshot.calories_actual = round(totals["calories"], 1)
        snapshot.calories_target = calorie_target
        snapshot.protein_g_actual = round(totals["protein_g"], 1)
        snapshot.protein_g_target = protein_target
        snapshot.carbs_g_actual = round(totals["carbs_g"], 1)
        snapshot.fat_g_actual = round(totals["fat_g"], 1)
        snapshot.fiber_g_actual = round(totals["fiber_g"], 1)
        snapshot.sugar_g_actual = round(totals["sugar_g"], 1)
        snapshot.sodium_mg_actual = round(totals["sodium_mg"], 1)
        snapshot.vitamin_c_mg = round(totals["vitamin_c_mg"], 1)
        snapshot.vitamin_d_mcg = round(totals["vitamin_d_mcg"], 1)
        snapshot.calcium_mg = round(totals["calcium_mg"], 1)
        snapshot.iron_mg = round(totals["iron_mg"], 1)
        snapshot.omega3_g = round(totals["omega3_g"], 2)
        snapshot.nutrition_score = score
        snapshot.deficiencies = deficiencies

        if calorie_target and calorie_target > 0:
            snapshot.goal_achievement_pct = min(
                100, round(totals["calories"] / calorie_target * 100, 1)
            )

        await self.db.commit()
        await self.db.refresh(snapshot)

        # Update streak
        await self._update_streak(user)

        # Invalidate dashboard cache
        await redis_client.delete(f"dashboard:{user.id}")

        return snapshot

    def _compute_nutrition_score(self, totals: dict, profile: Optional[UserProfile]) -> float:
        """Compute a 0-100 nutrition score based on goal achievement and balance."""
        score = 50.0  # Base score

        calorie_target = profile.daily_calorie_target if profile else 2000

        if calorie_target and totals["calories"] > 0:
            cal_ratio = totals["calories"] / calorie_target
            # Best score when at 90-110% of target
            if 0.9 <= cal_ratio <= 1.1:
                score += 20
            elif 0.8 <= cal_ratio <= 1.2:
                score += 10
            elif cal_ratio < 0.5 or cal_ratio > 1.5:
                score -= 10

        # Fiber bonus
        if totals["fiber_g"] >= 25:
            score += 10
        elif totals["fiber_g"] >= 15:
            score += 5

        # Sugar penalty
        if totals["sugar_g"] > 50:
            score -= 10
        elif totals["sugar_g"] > 25:
            score -= 5

        # Sodium penalty
        if totals["sodium_mg"] > 2300:
            score -= 10

        # Protein bonus
        protein_target = profile.daily_protein_target_g if profile else 50
        if protein_target and totals["protein_g"] >= protein_target:
            score += 10

        return round(max(0, min(100, score)), 1)

    def _detect_deficiencies(self, totals: dict) -> Dict[str, list]:
        """Detect nutritional deficiencies based on RDI thresholds."""
        deficient = []
        borderline = []

        checks = {
            "Vitamin C": (totals.get("vitamin_c_mg", 0), RDI["vitamin_c_mg"]),
            "Vitamin D": (totals.get("vitamin_d_mcg", 0), RDI["vitamin_d_mcg"]),
            "Calcium": (totals.get("calcium_mg", 0), RDI["calcium_mg"]),
            "Iron": (totals.get("iron_mg", 0), RDI["iron_mg"]),
            "Fiber": (totals.get("fiber_g", 0), RDI["fiber_g"]),
            "Omega-3": (totals.get("omega3_g", 0), RDI["omega3_g"]),
        }

        for nutrient, (actual, rdi) in checks.items():
            pct = (actual / rdi * 100) if rdi > 0 else 100
            if pct < 50:
                deficient.append({"nutrient": nutrient, "actual": actual, "target": rdi, "pct": round(pct, 1)})
            elif pct < 80:
                borderline.append({"nutrient": nutrient, "actual": actual, "target": rdi, "pct": round(pct, 1)})

        return {"deficient": deficient, "borderline": borderline}

    async def _update_streak(self, user: User):
        """Update user's logging streak."""
        profile = user.profile
        if not profile:
            return

        # Count consecutive days with meals
        today = date.today()
        streak = 0
        check_date = today

        for _ in range(365):  # Max 1 year
            result = await self.db.execute(
                select(func.count(Meal.id)).where(
                    Meal.user_id == user.id,
                    func.date(Meal.meal_time) == check_date,
                    Meal.analysis_status == "completed",
                )
            )
            count = result.scalar()
            if count > 0:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break

        profile.streak_days = streak
        await self.db.commit()

    async def get_daily_snapshot(
        self, user_id: uuid.UUID, target_date: date
    ) -> DailySnapshot:
        """Get daily snapshot for a specific date."""
        result = await self.db.execute(
            select(DailyNutritionSnapshot).where(
                DailyNutritionSnapshot.user_id == user_id,
                DailyNutritionSnapshot.snapshot_date == target_date,
            )
        )
        snapshot = result.scalar_one_or_none()

        if not snapshot:
            # Return empty snapshot
            return DailySnapshot(
                id=uuid.uuid4(),
                snapshot_date=target_date,
                meals_logged=0,
                calories_actual=0,
                calories_target=None,
                protein_g_actual=0,
                protein_g_target=None,
                carbs_g_actual=0,
                fat_g_actual=0,
                fiber_g_actual=0,
                sugar_g_actual=0,
                sodium_mg_actual=0,
                water_ml_actual=0,
                nutrition_score=0,
                goal_achievement_pct=0,
                deficiencies=None,
            )

        return DailySnapshot.model_validate(snapshot)

    async def get_weekly_summary(
        self, user_id: uuid.UUID, week_offset: int = 0
    ) -> WeeklySummary:
        """Get weekly aggregated summary."""
        today = date.today()
        week_start = today - timedelta(days=today.weekday() + week_offset * 7)
        week_end = week_start + timedelta(days=6)

        result = await self.db.execute(
            select(DailyNutritionSnapshot).where(
                DailyNutritionSnapshot.user_id == user_id,
                DailyNutritionSnapshot.snapshot_date >= week_start,
                DailyNutritionSnapshot.snapshot_date <= week_end,
            )
        )
        snapshots = result.scalars().all()

        if not snapshots:
            return WeeklySummary(
                week_start=week_start, week_end=week_end,
                week_number=week_start.isocalendar()[1],
                avg_daily_calories=0, avg_daily_protein_g=0,
                avg_daily_carbs_g=0, avg_daily_fat_g=0,
                avg_daily_fiber_g=0, avg_daily_sugar_g=0,
                avg_daily_water_ml=0, total_meals_logged=0,
                days_logged=0, consistency_score=0,
                calorie_trend=None, weight_change_kg=None,
                top_foods=None, recurring_deficiencies=None, ai_summary=None,
            )

        n = len(snapshots)
        avg = lambda field: round(sum(getattr(s, field) for s in snapshots) / n, 1)

        consistency = round(n / 7 * 100, 1)

        return WeeklySummary(
            week_start=week_start,
            week_end=week_end,
            week_number=week_start.isocalendar()[1],
            avg_daily_calories=avg("calories_actual"),
            avg_daily_protein_g=avg("protein_g_actual"),
            avg_daily_carbs_g=avg("carbs_g_actual"),
            avg_daily_fat_g=avg("fat_g_actual"),
            avg_daily_fiber_g=avg("fiber_g_actual"),
            avg_daily_sugar_g=avg("sugar_g_actual"),
            avg_daily_water_ml=avg("water_ml_actual"),
            total_meals_logged=sum(s.meals_logged for s in snapshots),
            days_logged=n,
            consistency_score=consistency,
            calorie_trend="stable",
            weight_change_kg=None,
            top_foods=None,
            recurring_deficiencies=None,
            ai_summary=None,
        )

    async def get_monthly_report(
        self, user_id: uuid.UUID, year: int, month: int
    ) -> MonthlyReport:
        """Get monthly aggregated report."""
        import calendar
        last_day = calendar.monthrange(year, month)[1]
        month_start = date(year, month, 1)
        month_end = date(year, month, last_day)

        result = await self.db.execute(
            select(DailyNutritionSnapshot).where(
                DailyNutritionSnapshot.user_id == user_id,
                DailyNutritionSnapshot.snapshot_date >= month_start,
                DailyNutritionSnapshot.snapshot_date <= month_end,
            )
        )
        snapshots = result.scalars().all()

        n = len(snapshots) or 1
        avg = lambda field: round(sum(getattr(s, field) for s in snapshots) / n, 1)

        return MonthlyReport(
            year=year, month=month,
            avg_daily_calories=avg("calories_actual"),
            avg_daily_protein_g=avg("protein_g_actual"),
            total_meals_logged=sum(s.meals_logged for s in snapshots),
            days_logged=len(snapshots),
            consistency_score=round(len(snapshots) / last_day * 100, 1),
            streak_best=0,
            goal_achievement_pct=avg("goal_achievement_pct"),
            weight_start_kg=None, weight_end_kg=None, weight_change_kg=None,
            top_achievements=None, areas_for_improvement=None, ai_monthly_summary=None,
        )

    async def get_nutrition_trend(
        self, user_id: uuid.UUID, days: int = 30
    ) -> NutritionTrend:
        """Get nutrition trend data for charting."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        result = await self.db.execute(
            select(DailyNutritionSnapshot).where(
                DailyNutritionSnapshot.user_id == user_id,
                DailyNutritionSnapshot.snapshot_date >= start_date,
                DailyNutritionSnapshot.snapshot_date <= end_date,
            ).order_by(DailyNutritionSnapshot.snapshot_date)
        )
        snapshots = result.scalars().all()

        snap_map = {s.snapshot_date: s for s in snapshots}
        dates, cals, proteins, carbs, fats, fibers, sugars = [], [], [], [], [], [], []

        current = start_date
        while current <= end_date:
            snap = snap_map.get(current)
            dates.append(current)
            cals.append(snap.calories_actual if snap else 0)
            proteins.append(snap.protein_g_actual if snap else 0)
            carbs.append(snap.carbs_g_actual if snap else 0)
            fats.append(snap.fat_g_actual if snap else 0)
            fibers.append(snap.fiber_g_actual if snap else 0)
            sugars.append(snap.sugar_g_actual if snap else 0)
            current += timedelta(days=1)

        return NutritionTrend(
            dates=dates, calories=cals, protein_g=proteins,
            carbs_g=carbs, fat_g=fats, fiber_g=fibers, sugar_g=sugars,
        )

    async def get_deficiency_report(
        self, user_id: uuid.UUID, days: int = 7
    ) -> DeficiencyReport:
        """Analyze nutrient deficiencies over recent days."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        result = await self.db.execute(
            select(DailyNutritionSnapshot).where(
                DailyNutritionSnapshot.user_id == user_id,
                DailyNutritionSnapshot.snapshot_date >= start_date,
            )
        )
        snapshots = result.scalars().all()

        # Average nutrient intakes
        n = len(snapshots) or 1
        avg_totals = {
            "vitamin_c_mg": sum(s.vitamin_c_mg for s in snapshots) / n,
            "vitamin_d_mcg": sum(s.vitamin_d_mcg for s in snapshots) / n,
            "calcium_mg": sum(s.calcium_mg for s in snapshots) / n,
            "iron_mg": sum(s.iron_mg for s in snapshots) / n,
            "fiber_g": sum(s.fiber_g_actual for s in snapshots) / n,
            "omega3_g": sum(s.omega3_g for s in snapshots) / n,
        }

        deficient, borderline, sufficient = [], [], []

        labels = {
            "vitamin_c_mg": "Vitamin C",
            "vitamin_d_mcg": "Vitamin D",
            "calcium_mg": "Calcium",
            "iron_mg": "Iron",
            "fiber_g": "Fiber",
            "omega3_g": "Omega-3",
        }

        recs = []
        for key, label in labels.items():
            actual = avg_totals.get(key, 0)
            rdi = RDI.get(key, 1)
            pct = min(100, actual / rdi * 100)
            entry = {"nutrient": label, "actual": round(actual, 1), "target": rdi, "pct": round(pct, 1)}

            if pct < 50:
                deficient.append(entry)
                recs.append(f"Increase {label} intake urgently.")
            elif pct < 80:
                borderline.append(entry)
                recs.append(f"Boost {label} slightly.")
            else:
                sufficient.append(label)

        return DeficiencyReport(
            deficient_nutrients=deficient,
            borderline_nutrients=borderline,
            sufficient_nutrients=sufficient,
            recommendations=recs[:5],
        )

    async def get_streak_data(self, user_id: uuid.UUID) -> StreakData:
        """Get user's streak and consistency data."""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        current_streak = profile.streak_days if profile else 0

        # Count total days logged
        result = await self.db.execute(
            select(func.count(DailyNutritionSnapshot.id)).where(
                DailyNutritionSnapshot.user_id == user_id,
                DailyNutritionSnapshot.meals_logged > 0,
            )
        )
        total_days = result.scalar() or 0

        # Last log date
        result = await self.db.execute(
            select(DailyNutritionSnapshot.snapshot_date).where(
                DailyNutritionSnapshot.user_id == user_id,
                DailyNutritionSnapshot.meals_logged > 0,
            ).order_by(desc(DailyNutritionSnapshot.snapshot_date)).limit(1)
        )
        last_date = result.scalar_one_or_none()

        return StreakData(
            current_streak=current_streak,
            longest_streak=current_streak,  # TODO: track separately
            consistency_score=profile.consistency_score if profile else 0,
            total_days_logged=total_days,
            last_log_date=last_date,
        )

    async def get_dashboard_summary(self, user: User) -> DashboardSummary:
        """Get complete dashboard data."""
        cache_key = f"dashboard:{user.id}"
        cached = await redis_client.get(cache_key)
        if cached:
            return DashboardSummary(**cached)

        today_snapshot = await self.get_daily_snapshot(user.id, date.today())
        streak = await self.get_streak_data(user.id)
        deficiencies = await self.get_deficiency_report(user.id, days=7)
        weekly_trend = await self.get_nutrition_trend(user.id, days=7)

        profile = user.profile
        calorie_target = profile.daily_calorie_target if profile else 2000
        calorie_pct = (
            round(today_snapshot.calories_actual / calorie_target * 100, 1)
            if calorie_target else 0
        )

        # Macro breakdown
        total_cal = today_snapshot.calories_actual or 1
        macro = MacroBreakdown(
            protein_pct=round(today_snapshot.protein_g_actual * 4 / total_cal * 100, 1),
            carbs_pct=round(today_snapshot.carbs_g_actual * 4 / total_cal * 100, 1),
            fat_pct=round(today_snapshot.fat_g_actual * 9 / total_cal * 100, 1),
            protein_g=today_snapshot.protein_g_actual,
            carbs_g=today_snapshot.carbs_g_actual,
            fat_g=today_snapshot.fat_g_actual,
            total_calories=today_snapshot.calories_actual,
        )

        dashboard = DashboardSummary(
            today_calories=today_snapshot.calories_actual,
            calorie_target=calorie_target,
            calorie_pct=calorie_pct,
            today_protein_g=today_snapshot.protein_g_actual,
            today_carbs_g=today_snapshot.carbs_g_actual,
            today_fat_g=today_snapshot.fat_g_actual,
            today_fiber_g=today_snapshot.fiber_g_actual,
            today_sugar_g=today_snapshot.sugar_g_actual,
            today_water_ml=today_snapshot.water_ml_actual,
            meals_today=today_snapshot.meals_logged,
            nutrition_score=today_snapshot.nutrition_score,
            streak=streak,
            macro_breakdown=macro,
            weekly_trend=weekly_trend,
            deficiencies=deficiencies,
            top_recommendations=deficiencies.recommendations[:3],
        )

        await redis_client.set(cache_key, dashboard.model_dump(), ttl=300)  # 5 min cache
        return dashboard


# Import here to avoid circular
from app.models.user import UserProfile
