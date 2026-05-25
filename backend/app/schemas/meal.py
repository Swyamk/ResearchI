"""
Pydantic schemas for Meal and FoodItem endpoints.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.meal import MealType


# ── Food Item Schemas ─────────────────────────────────────────────────────────
class FoodItemBase(BaseModel):
    name: str
    portion_size_g: Optional[float] = None
    portion_description: Optional[str] = None


class FoodItemResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    name_local: Optional[str]
    category: Optional[str]
    classification_confidence: Optional[float]
    portion_size_g: Optional[float]
    portion_volume_ml: Optional[float]
    portion_description: Optional[str]
    bbox_x: Optional[float]
    bbox_y: Optional[float]
    bbox_width: Optional[float]
    bbox_height: Optional[float]

    # Macros
    calories: Optional[float]
    protein_g: Optional[float]
    carbs_g: Optional[float]
    fat_g: Optional[float]
    fiber_g: Optional[float]
    sugar_g: Optional[float]
    sodium_mg: Optional[float]
    cholesterol_mg: Optional[float]

    # Key micronutrients
    vitamin_c_mg: Optional[float]
    vitamin_d_mcg: Optional[float]
    calcium_mg: Optional[float]
    iron_mg: Optional[float]
    omega3_g: Optional[float]

    nutrition_source: Optional[str]
    created_at: datetime


# ── Meal Schemas ──────────────────────────────────────────────────────────────
class MealCreate(BaseModel):
    meal_type: MealType = MealType.lunch
    name: Optional[str] = None
    notes: Optional[str] = None
    meal_time: Optional[datetime] = None


class MealUpdate(BaseModel):
    meal_type: Optional[MealType] = None
    name: Optional[str] = None
    notes: Optional[str] = None
    meal_time: Optional[datetime] = None


class MealAnalysisRequest(BaseModel):
    meal_type: MealType = MealType.lunch
    meal_time: Optional[datetime] = None
    notes: Optional[str] = None


class MealAnalysisResponse(BaseModel):
    """Response after AI meal image analysis."""
    meal_id: uuid.UUID
    status: str
    detected_items: List[dict]
    total_calories: Optional[float]
    total_protein_g: Optional[float]
    total_carbs_g: Optional[float]
    total_fat_g: Optional[float]
    total_fiber_g: Optional[float]
    total_sugar_g: Optional[float]
    total_sodium_mg: Optional[float]
    confidence_avg: Optional[float]
    processing_time_ms: Optional[int]
    suggestions: Optional[List[str]]


class MealResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    meal_type: MealType
    name: Optional[str]
    notes: Optional[str]
    meal_time: datetime
    image_url: Optional[str]
    image_thumbnail_url: Optional[str]
    analysis_status: str

    # Totals
    total_calories: Optional[float]
    total_protein_g: Optional[float]
    total_carbs_g: Optional[float]
    total_fat_g: Optional[float]
    total_fiber_g: Optional[float]
    total_sugar_g: Optional[float]
    total_sodium_mg: Optional[float]

    food_items: List[FoodItemResponse]
    created_at: datetime
    updated_at: datetime


class MealListResponse(BaseModel):
    meals: List[MealResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
