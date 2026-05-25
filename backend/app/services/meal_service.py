"""
Meal Service – AI analysis pipeline orchestration and meal CRUD.
"""
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.meal import FoodItem, Meal, MealType
from app.services.nutrition_service import NutritionService


class MealService:
    """Handles meal image analysis and CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.nutrition_service = NutritionService()

    async def _save_image(self, content: bytes, filename: str, user_id: uuid.UUID) -> str:
        """Save uploaded image and return URL."""
        upload_dir = Path(settings.UPLOAD_DIR) / str(user_id)
        upload_dir.mkdir(parents=True, exist_ok=True)

        ext = Path(filename).suffix.lower() or ".jpg"
        new_filename = f"{uuid.uuid4()}{ext}"
        filepath = upload_dir / new_filename

        with open(filepath, "wb") as f:
            f.write(content)

        return f"/uploads/{user_id}/{new_filename}"

    async def _call_ai_inference(self, image_url: str) -> Dict[str, Any]:
        """
        Call the AI inference service (YOLOv8 + SAM2 + EfficientNetV2 + MiDaS).
        Returns detected food items with classification and portion estimates.
        """
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{settings.AI_MODELS_URL}/analyze",
                    json={"image_url": image_url},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            # Return mock data if AI service is unavailable (dev fallback)
            return {
                "detected_items": [
                    {
                        "name": "rice",
                        "confidence": 0.92,
                        "portion_g": 150,
                        "bbox": [0.1, 0.1, 0.5, 0.5],
                    }
                ],
                "error": str(e),
                "fallback": True,
            }

    async def analyze_and_save_meal(
        self,
        user_id: uuid.UUID,
        image_content: bytes,
        image_filename: str,
        meal_type: MealType,
        meal_time: datetime,
        notes: Optional[str],
    ) -> Dict[str, Any]:
        """Full meal analysis pipeline: save → detect → classify → nutrition lookup."""

        # 1. Save image
        image_url = await self._save_image(image_content, image_filename, user_id)

        # 2. Create meal record
        meal = Meal(
            user_id=user_id,
            meal_type=meal_type,
            meal_time=meal_time,
            notes=notes,
            image_url=image_url,
            analysis_status="processing",
        )
        self.db.add(meal)
        await self.db.flush()

        # 3. Call AI inference pipeline
        ai_result = await self._call_ai_inference(image_url)
        detected_items = ai_result.get("detected_items", [])

        # 4. Enrich with nutrition data
        food_items = []
        total_calories = total_protein = total_carbs = total_fat = 0
        total_fiber = total_sugar = total_sodium = 0
        confidence_sum = 0

        for item in detected_items:
            food_name = item.get("name", "unknown food")
            portion_g = item.get("portion_g", 100.0)
            confidence = item.get("confidence", 0.0)
            confidence_sum += confidence

            # Get nutrition data
            nutrition = await self.nutrition_service.get_nutrition_for_food(food_name, portion_g)

            bbox = item.get("bbox", [0, 0, 0, 0])

            food_item = FoodItem(
                meal_id=meal.id,
                name=food_name,
                classification_confidence=confidence,
                classification_model="efficientnetv2",
                portion_size_g=portion_g,
                bbox_x=bbox[0] if len(bbox) > 0 else None,
                bbox_y=bbox[1] if len(bbox) > 1 else None,
                bbox_width=bbox[2] if len(bbox) > 2 else None,
                bbox_height=bbox[3] if len(bbox) > 3 else None,
                # Nutrition
                calories=nutrition.get("calories", 0) if nutrition else 0,
                protein_g=nutrition.get("protein_g", 0) if nutrition else 0,
                carbs_g=nutrition.get("carbs_g", 0) if nutrition else 0,
                fat_g=nutrition.get("fat_g", 0) if nutrition else 0,
                fiber_g=nutrition.get("fiber_g", 0) if nutrition else 0,
                sugar_g=nutrition.get("sugar_g", 0) if nutrition else 0,
                sodium_mg=nutrition.get("sodium_mg", 0) if nutrition else 0,
                vitamin_c_mg=nutrition.get("vitamin_c_mg", 0) if nutrition else 0,
                vitamin_d_mcg=nutrition.get("vitamin_d_mcg", 0) if nutrition else 0,
                calcium_mg=nutrition.get("calcium_mg", 0) if nutrition else 0,
                iron_mg=nutrition.get("iron_mg", 0) if nutrition else 0,
                omega3_g=nutrition.get("omega3_g", 0) if nutrition else 0,
                nutrition_source=nutrition.get("source", "estimated") if nutrition else "estimated",
            )
            self.db.add(food_item)
            food_items.append(food_item)

            total_calories += food_item.calories or 0
            total_protein += food_item.protein_g or 0
            total_carbs += food_item.carbs_g or 0
            total_fat += food_item.fat_g or 0
            total_fiber += food_item.fiber_g or 0
            total_sugar += food_item.sugar_g or 0
            total_sodium += food_item.sodium_mg or 0

        # 5. Update meal totals
        meal.total_calories = round(total_calories, 1)
        meal.total_protein_g = round(total_protein, 1)
        meal.total_carbs_g = round(total_carbs, 1)
        meal.total_fat_g = round(total_fat, 1)
        meal.total_fiber_g = round(total_fiber, 1)
        meal.total_sugar_g = round(total_sugar, 1)
        meal.total_sodium_mg = round(total_sodium, 1)
        meal.analysis_status = "completed"
        meal.detection_results = ai_result

        await self.db.commit()

        # 6. Trigger analytics update (async)
        await self._update_daily_analytics(user_id)

        n = len(detected_items)
        return {
            "meal_id": meal.id,
            "status": "completed",
            "detected_items": [
                {
                    "name": fi.name,
                    "portion_g": fi.portion_size_g,
                    "confidence": fi.classification_confidence,
                    "calories": fi.calories,
                    "protein_g": fi.protein_g,
                    "carbs_g": fi.carbs_g,
                    "fat_g": fi.fat_g,
                }
                for fi in food_items
            ],
            "total_calories": meal.total_calories,
            "total_protein_g": meal.total_protein_g,
            "total_carbs_g": meal.total_carbs_g,
            "total_fat_g": meal.total_fat_g,
            "total_fiber_g": meal.total_fiber_g,
            "total_sugar_g": meal.total_sugar_g,
            "total_sodium_mg": meal.total_sodium_mg,
            "confidence_avg": round(confidence_sum / n, 3) if n > 0 else 0,
            "suggestions": self._generate_meal_suggestions(meal),
        }

    def _generate_meal_suggestions(self, meal: Meal) -> List[str]:
        """Generate quick meal improvement suggestions."""
        suggestions = []
        if (meal.total_protein_g or 0) < 20:
            suggestions.append("Consider adding a protein source like dal, paneer, or eggs.")
        if (meal.total_fiber_g or 0) < 5:
            suggestions.append("Add more fiber with vegetables or whole grains.")
        if (meal.total_sodium_mg or 0) > 1000:
            suggestions.append("This meal is high in sodium. Balance with low-sodium meals today.")
        return suggestions

    async def _update_daily_analytics(self, user_id: uuid.UUID):
        """Trigger analytics recalculation for today."""
        try:
            from app.services.analytics_service import AnalyticsService
            analytics = AnalyticsService(self.db)
            from sqlalchemy import select as sa_select
            from app.models.user import User
            result = await self.db.execute(sa_select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                await analytics.sync_daily_snapshot(user)
        except Exception:
            pass  # Non-critical

    async def list_meals(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 10,
        meal_type: Optional[MealType] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> dict:
        """List meals with pagination and filtering."""
        query = (
            select(Meal)
            .where(Meal.user_id == user_id)
            .options(selectinload(Meal.food_items))
            .order_by(desc(Meal.meal_time))
        )

        if meal_type:
            query = query.where(Meal.meal_type == meal_type)
        if date_from:
            query = query.where(func.date(Meal.meal_time) >= date_from)
        if date_to:
            query = query.where(func.date(Meal.meal_time) <= date_to)

        # Count total
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        meals = result.scalars().all()

        return {
            "meals": meals,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_next": (page * page_size) < total,
        }
