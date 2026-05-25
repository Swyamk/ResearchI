"""
Recommendation Service – LightGBM + Rule-Based Health Logic.
Generates personalized, context-aware nutrition recommendations.
"""
import uuid
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import DailyNutritionSnapshot
from app.models.user import ActivityLevel, HealthGoal, User, UserProfile


class RuleEngine:
    """Rule-based health logic for condition-specific recommendations."""

    CONDITION_RULES = {
        "diabetes_type1": {
            "avoid": ["white rice", "sugar", "refined flour", "sugary drinks", "fruit juice"],
            "prefer": ["brown rice", "quinoa", "oats", "legumes", "leafy vegetables", "nuts"],
            "limits": {"sugar_g": 25, "carbs_g": 150},
            "message": "For diabetes management: focus on low-GI foods and complex carbohydrates.",
        },
        "diabetes_type2": {
            "avoid": ["white bread", "processed foods", "sugary drinks", "alcohol"],
            "prefer": ["whole grains", "vegetables", "lean protein", "fiber-rich foods"],
            "limits": {"sugar_g": 25, "carbs_g": 130},
            "message": "Prioritize blood sugar stability with fiber-rich, low-GI meals.",
        },
        "hypertension": {
            "avoid": ["salt", "processed meats", "canned foods", "pickles"],
            "prefer": ["bananas", "spinach", "beets", "garlic", "berries", "oats"],
            "limits": {"sodium_mg": 1500},
            "message": "Reduce sodium intake and increase potassium-rich foods.",
        },
        "high_cholesterol": {
            "avoid": ["trans fats", "fried foods", "full-fat dairy", "processed meats"],
            "prefer": ["oats", "avocado", "olive oil", "walnuts", "salmon", "legumes"],
            "limits": {"fat_g": 55, "cholesterol_mg": 200},
            "message": "Focus on healthy unsaturated fats and fiber to lower LDL cholesterol.",
        },
        "pcos": {
            "avoid": ["refined carbs", "processed sugars", "inflammatory foods"],
            "prefer": ["anti-inflammatory foods", "lean protein", "omega-3 rich foods", "turmeric", "cinnamon"],
            "limits": {"sugar_g": 30},
            "message": "Anti-inflammatory diet with adequate protein supports PCOS management.",
        },
        "thyroid": {
            "avoid": ["raw cruciferous vegetables in excess", "soy in excess"],
            "prefer": ["iodine-rich foods", "selenium-rich foods (Brazil nuts)", "lean protein"],
            "limits": {},
            "message": "Ensure adequate iodine and selenium for thyroid health.",
        },
    }

    GOAL_RULES = {
        "weight_loss": {
            "calorie_adjustment": -500,  # Deficit
            "macro_split": {"protein": 0.35, "carbs": 0.35, "fat": 0.30},
            "tips": [
                "Create a sustainable calorie deficit of 300-500 kcal/day.",
                "Prioritize high-protein foods to preserve muscle mass.",
                "Fill half your plate with non-starchy vegetables.",
                "Stay hydrated – drink 2.5-3L of water daily.",
            ],
        },
        "muscle_gain": {
            "calorie_adjustment": 300,  # Surplus
            "macro_split": {"protein": 0.30, "carbs": 0.45, "fat": 0.25},
            "tips": [
                "Consume 1.6-2.2g of protein per kg of body weight.",
                "Eat complex carbs around workouts for energy.",
                "Don't skip post-workout nutrition within 45 minutes.",
                "Focus on progressive overload alongside nutrition.",
            ],
        },
        "diabetes_management": {
            "calorie_adjustment": -200,
            "macro_split": {"protein": 0.30, "carbs": 0.35, "fat": 0.35},
            "tips": [
                "Space meals every 3-4 hours to maintain stable blood sugar.",
                "Pair carbs with protein or fiber to blunt glucose spikes.",
                "Choose whole grain options over refined carbohydrates.",
                "Monitor and log blood sugar alongside meals.",
            ],
        },
        "maintenance": {
            "calorie_adjustment": 0,
            "macro_split": {"protein": 0.25, "carbs": 0.45, "fat": 0.30},
            "tips": [
                "Maintain consistent meal timing for metabolic stability.",
                "Focus on micronutrient diversity with colorful vegetables.",
                "Include omega-3 rich foods 2-3 times per week.",
            ],
        },
        "heart_health": {
            "calorie_adjustment": -200,
            "macro_split": {"protein": 0.25, "carbs": 0.45, "fat": 0.30},
            "tips": [
                "Follow Mediterranean diet principles.",
                "Limit saturated fat to <10% of calories.",
                "Eat fatty fish (salmon, mackerel) 2x per week.",
                "Include soluble fiber from oats, legumes, and fruits.",
            ],
        },
    }

    def get_condition_rules(self, conditions: List[str]) -> dict:
        """Get combined rules for multiple health conditions."""
        combined = {"avoid": [], "prefer": [], "limits": {}, "messages": []}
        for condition in conditions:
            rules = self.CONDITION_RULES.get(condition, {})
            combined["avoid"].extend(rules.get("avoid", []))
            combined["prefer"].extend(rules.get("prefer", []))
            combined["limits"].update(rules.get("limits", {}))
            if "message" in rules:
                combined["messages"].append(rules["message"])

        # Deduplicate
        combined["avoid"] = list(set(combined["avoid"]))
        combined["prefer"] = list(set(combined["prefer"]))

        return combined

    def get_goal_rules(self, goal: str) -> dict:
        return self.GOAL_RULES.get(goal, self.GOAL_RULES["maintenance"])


class RecommendationEngine:
    """
    LightGBM + Rule-based personalized recommendation engine.
    Generates context-aware nutrition advice based on:
    - Recent nutrition data and trends
    - User health profile, goals, and conditions
    - Detected deficiencies
    - Time of day and meal type
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.rule_engine = RuleEngine()
        self._lgbm_model = None

    def _try_load_lgbm(self):
        """Attempt to load pre-trained LightGBM model."""
        try:
            import lightgbm as lgb
            model_path = Path("./ai_models/weights/recommendation_lgbm.txt")
            if model_path.exists():
                self._lgbm_model = lgb.Booster(model_file=str(model_path))
        except Exception:
            pass

    def _extract_features(
        self, snapshots: List[DailyNutritionSnapshot], profile: UserProfile
    ) -> np.ndarray:
        """Extract features for LightGBM model."""
        if not snapshots:
            return np.zeros(20)

        recent = snapshots[-7:] if len(snapshots) >= 7 else snapshots
        n = len(recent)

        avg_cal = sum(s.calories_actual for s in recent) / n
        avg_protein = sum(s.protein_g_actual for s in recent) / n
        avg_carbs = sum(s.carbs_g_actual for s in recent) / n
        avg_fat = sum(s.fat_g_actual for s in recent) / n
        avg_fiber = sum(s.fiber_g_actual for s in recent) / n
        avg_sugar = sum(s.sugar_g_actual for s in recent) / n
        consistency = n / 7

        features = [
            avg_cal,
            avg_protein,
            avg_carbs,
            avg_fat,
            avg_fiber,
            avg_sugar,
            consistency,
            profile.age or 30,
            profile.bmi or 22,
            profile.weight_kg or 70,
            1 if profile.gender and profile.gender.value == "male" else 0,
            # Activity level encoded
            {"sedentary": 1, "lightly_active": 2, "moderately_active": 3,
             "very_active": 4, "extremely_active": 5}.get(
                profile.activity_level.value if profile.activity_level else "", 2
            ),
            profile.daily_calorie_target or 2000,
            profile.daily_protein_target_g or 50,
            avg_cal / (profile.daily_calorie_target or 2000),  # cal goal ratio
            avg_protein / (profile.daily_protein_target_g or 50),  # protein ratio
            int(bool(profile.health_conditions)),
            len(profile.health_conditions or []),
            int(bool(profile.dietary_restrictions)),
            avg_sugar > 50,  # high sugar flag
        ]

        return np.array(features, dtype=np.float32)

    async def generate_recommendations(
        self, user: User, limit: int = 5
    ) -> List[Dict]:
        """Generate personalized recommendations."""
        profile = user.profile
        if not profile:
            return [{"type": "general", "message": "Complete your profile for personalized recommendations!", "priority": "high"}]

        # Get recent snapshots
        end_date = date.today()
        start_date = end_date - timedelta(days=14)

        result = await self.db.execute(
            select(DailyNutritionSnapshot).where(
                DailyNutritionSnapshot.user_id == user.id,
                DailyNutritionSnapshot.snapshot_date >= start_date,
            ).order_by(DailyNutritionSnapshot.snapshot_date)
        )
        snapshots = result.scalars().all()

        recommendations = []

        # 1. Rule-based condition-specific recommendations
        if profile.health_conditions:
            condition_rules = self.rule_engine.get_condition_rules(profile.health_conditions)
            for msg in condition_rules["messages"]:
                recommendations.append({
                    "type": "health_condition",
                    "message": msg,
                    "priority": "high",
                    "category": "medical_nutrition",
                })

        # 2. Goal-based recommendations
        if profile.primary_goal:
            goal_rules = self.rule_engine.get_goal_rules(profile.primary_goal.value)
            for tip in goal_rules["tips"][:2]:
                recommendations.append({
                    "type": "goal",
                    "message": tip,
                    "priority": "medium",
                    "category": "goal_nutrition",
                })

        # 3. Deficiency-based recommendations
        if snapshots:
            latest = snapshots[-1]
            if latest.deficiencies:
                for d in latest.deficiencies.get("deficient", [])[:2]:
                    recommendations.append({
                        "type": "deficiency",
                        "message": f"You're low on {d['nutrient']} ({d['pct']}% of daily target). "
                                   f"Increase intake through food or supplementation.",
                        "priority": "high",
                        "nutrient": d["nutrient"],
                        "category": "micronutrient",
                    })

        # 4. Calorie balance recommendation
        if snapshots:
            recent_avg_cal = sum(s.calories_actual for s in snapshots[-3:]) / min(3, len(snapshots))
            target = profile.daily_calorie_target or 2000

            if recent_avg_cal < target * 0.8:
                recommendations.append({
                    "type": "calorie_low",
                    "message": f"You've been eating {recent_avg_cal:.0f} kcal vs your {target:.0f} kcal target. "
                               "Undereating can slow metabolism and cause muscle loss.",
                    "priority": "medium",
                    "category": "calorie_balance",
                })
            elif recent_avg_cal > target * 1.2:
                recommendations.append({
                    "type": "calorie_high",
                    "message": f"Your average intake of {recent_avg_cal:.0f} kcal exceeds your target. "
                               "Review portion sizes and reduce calorie-dense snacks.",
                    "priority": "medium",
                    "category": "calorie_balance",
                })

        # 5. Streak/consistency motivation
        streak = profile.streak_days
        if streak == 0:
            recommendations.append({
                "type": "consistency",
                "message": "Start your nutrition tracking journey today! Even one logged meal builds awareness.",
                "priority": "low",
                "category": "motivation",
            })
        elif streak < 7:
            recommendations.append({
                "type": "consistency",
                "message": f"You're on a {streak}-day streak! Keep it up – consistency is the key to results.",
                "priority": "low",
                "category": "motivation",
            })

        # Sort by priority and limit
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 2))

        return recommendations[:limit]

    async def get_meal_suggestions(
        self, user: User, meal_type: str = "lunch"
    ) -> List[str]:
        """Generate meal type-specific food suggestions."""
        profile = user.profile
        conditions = profile.health_conditions if profile else []
        goal = profile.primary_goal.value if profile and profile.primary_goal else "maintenance"

        base_suggestions = {
            "breakfast": [
                "Oats with nuts and berries", "Moong dal cheela with mint chutney",
                "Greek yogurt with fruits", "Whole wheat upma with vegetables",
                "Eggs with whole grain toast",
            ],
            "lunch": [
                "Brown rice with dal and sabzi", "Quinoa pulao with raita",
                "Whole wheat roti with paneer sabzi", "Mixed vegetable soup with bread",
                "Grilled chicken with salad",
            ],
            "dinner": [
                "Moong dal soup with roti", "Grilled fish with stir-fried vegetables",
                "Tofu stir-fry with brown rice", "Vegetable daliya khichdi",
                "Chicken soup with vegetables",
            ],
            "snack": [
                "Handful of mixed nuts", "Apple with peanut butter",
                "Roasted chana (chickpeas)", "Hummus with cucumber slices",
                "Low-fat yogurt with flaxseeds",
            ],
        }

        suggestions = base_suggestions.get(meal_type, base_suggestions["lunch"])

        # Filter based on dietary restrictions
        restrictions = profile.dietary_restrictions if profile else []
        if "vegetarian" in restrictions or "vegan" in restrictions:
            suggestions = [s for s in suggestions if not any(
                meat in s.lower() for meat in ["chicken", "fish", "egg", "meat", "beef"]
            )]

        return suggestions[:5]
