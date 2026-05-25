"""Users API routes."""
import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.dependencies import DB, CurrentUser
from app.models.user import User
from app.schemas.user import UserProfileResponse, UserProfileUpdate, UserResponse, UserUpdate

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: CurrentUser):
    """Get current user's full profile."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_user(payload: UserUpdate, current_user: CurrentUser, db: DB):
    """Update user display info."""
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.put("/me/profile", response_model=UserProfileResponse)
async def update_profile(payload: UserProfileUpdate, current_user: CurrentUser, db: DB):
    """Update health profile including goals, conditions, biometrics."""
    profile = current_user.profile
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    # Recalculate derived metrics
    profile.calculate_bmi()
    profile.calculate_bmr()
    profile.calculate_tdee()

    # Set nutrition targets based on TDEE and goal
    if profile.tdee and current_user.profile.primary_goal:
        goal_name = profile.primary_goal.value if profile.primary_goal else "maintenance"
        from app.services.recommendation_service import RuleEngine
        rule_engine = RuleEngine()
        goal_rules = rule_engine.get_goal_rules(goal_name)
        cal_adj = goal_rules.get("calorie_adjustment", 0)
        macro_split = goal_rules.get("macro_split", {"protein": 0.25, "carbs": 0.45, "fat": 0.30})

        calorie_target = max(1200, profile.tdee + cal_adj)
        profile.daily_calorie_target = calorie_target
        profile.daily_protein_target_g = round(calorie_target * macro_split["protein"] / 4, 1)
        profile.daily_carb_target_g = round(calorie_target * macro_split["carbs"] / 4, 1)
        profile.daily_fat_target_g = round(calorie_target * macro_split["fat"] / 9, 1)
        profile.daily_fiber_target_g = 25.0

    profile.onboarding_completed = True
    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/me/stats")
async def get_user_stats(current_user: CurrentUser, db: DB):
    """Get user statistics summary."""
    return {
        "total_meals_logged": current_user.profile.total_meals_logged if current_user.profile else 0,
        "streak_days": current_user.profile.streak_days if current_user.profile else 0,
        "consistency_score": current_user.profile.consistency_score if current_user.profile else 0,
        "member_since": current_user.created_at.isoformat(),
    }


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(current_user: CurrentUser, db: DB):
    """Delete current user account and all data."""
    await db.delete(current_user)
    await db.commit()
