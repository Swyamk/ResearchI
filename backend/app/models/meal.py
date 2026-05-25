"""
Meal and FoodItem SQLAlchemy models.
"""
import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MealType(str, enum.Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snack = "snack"
    pre_workout = "pre_workout"
    post_workout = "post_workout"


class Meal(Base):
    """Meal log entry with image and detected food items."""
    __tablename__ = "meals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    # Meal metadata
    meal_type: Mapped[MealType] = mapped_column(Enum(MealType), default=MealType.lunch)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meal_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Image analysis
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    image_thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    analysis_status: Mapped[str] = mapped_column(String(50), default="pending")
    # "pending" | "processing" | "completed" | "failed"

    # AI Detection results (raw YOLO + SAM2 output)
    detection_results: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    segmentation_results: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    depth_estimation_results: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Aggregated nutrition totals for the meal
    total_calories: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_protein_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_carbs_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_fat_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_fiber_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_sugar_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_sodium_mg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Micronutrients (stored as JSON for flexibility)
    micronutrients: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="meals")
    food_items: Mapped[List["FoodItem"]] = relationship(
        "FoodItem", back_populates="meal", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Meal {self.meal_type} @ {self.meal_time}>"


class FoodItem(Base):
    """Individual food item detected within a meal."""
    __tablename__ = "food_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meals.id", ondelete="CASCADE"), index=True
    )

    # Food identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_local: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    food_id_usda: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    food_id_off: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    food_id_indian: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # AI Classification confidence
    classification_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    classification_model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Portion estimation
    portion_size_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    portion_volume_ml: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    portion_description: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # e.g., "1 cup", "1 medium bowl", "2 pieces"

    # Bounding box (for meal image annotation)
    bbox_x: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_width: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_height: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Macronutrients (per detected portion)
    calories: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    protein_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    carbs_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fat_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fiber_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sugar_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sodium_mg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cholesterol_mg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Micronutrients
    vitamin_a_mcg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vitamin_b12_mcg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vitamin_c_mg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vitamin_d_mcg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vitamin_e_mg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vitamin_k_mcg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    calcium_mg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    iron_mg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    magnesium_mg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    potassium_mg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    zinc_mg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    folate_mcg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    omega3_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Data source
    nutrition_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # "usda" | "openfoodfacts" | "indian_fcd" | "estimated"

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    meal: Mapped["Meal"] = relationship("Meal", back_populates="food_items")

    def __repr__(self) -> str:
        return f"<FoodItem {self.name} ({self.portion_size_g}g)>"
