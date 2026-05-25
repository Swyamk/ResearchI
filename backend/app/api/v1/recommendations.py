"""Recommendations API routes – personalized nutrition recommendations."""
from typing import Optional

from fastapi import APIRouter, Query

from app.core.dependencies import DB, CurrentUser
from app.services.recommendation_service import RecommendationEngine

router = APIRouter()


@router.get("/today")
async def get_today_recommendations(
    current_user: CurrentUser,
    db: DB,
    limit: int = Query(5, ge=1, le=10),
):
    """Get personalized recommendations for today based on recent nutrition data."""
    engine = RecommendationEngine(db)
    recommendations = await engine.generate_recommendations(current_user, limit=limit)
    return {"recommendations": recommendations, "count": len(recommendations)}


@router.get("/meals/{meal_type}")
async def get_meal_suggestions(
    meal_type: str,
    current_user: CurrentUser,
    db: DB,
):
    """Get meal suggestions for a specific meal type (breakfast/lunch/dinner/snack)."""
    valid_types = ["breakfast", "lunch", "dinner", "snack", "pre_workout", "post_workout"]
    if meal_type not in valid_types:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Invalid meal type. Choose from: {valid_types}")

    engine = RecommendationEngine(db)
    suggestions = await engine.get_meal_suggestions(current_user, meal_type)
    return {"meal_type": meal_type, "suggestions": suggestions}


@router.get("/workout")
async def get_workout_suggestions(current_user: CurrentUser, db: DB):
    """Get workout suggestions aligned with user's nutrition and goals."""
    profile = current_user.profile
    goal = profile.primary_goal.value if profile and profile.primary_goal else "maintenance"
    activity = profile.activity_level.value if profile and profile.activity_level else "moderately_active"

    workout_map = {
        "weight_loss": [
            "45 min moderate cardio (walking, cycling, swimming)",
            "3x full-body strength training per week",
            "HIIT sessions 2-3x per week (20-30 min)",
            "Daily 10,000 steps walking",
        ],
        "muscle_gain": [
            "5-day push/pull/legs split",
            "Progressive overload compound lifts (squat, deadlift, bench)",
            "2x cardio sessions per week (light, 20 min)",
            "Ensure 7-9 hours sleep for muscle recovery",
        ],
        "diabetes_management": [
            "30 min brisk walking after meals",
            "Resistance training 3x per week",
            "Yoga and stress management daily",
            "Avoid high-intensity exercise on empty stomach",
        ],
        "maintenance": [
            "150 min moderate aerobic activity per week",
            "2x strength training sessions",
            "Daily flexibility/mobility work",
            "Active hobbies (cycling, swimming, sports)",
        ],
        "heart_health": [
            "30 min moderate cardio daily",
            "Zone 2 heart rate training (50-60% max HR)",
            "2x light strength training per week",
            "Yoga/meditation for stress reduction",
        ],
    }

    return {
        "goal": goal,
        "activity_level": activity,
        "suggestions": workout_map.get(goal, workout_map["maintenance"]),
    }
