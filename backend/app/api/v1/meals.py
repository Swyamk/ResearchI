"""
Meals API routes: upload, analyze, CRUD.
"""
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.dependencies import DB, CurrentUser, rate_limit
from app.models.meal import Meal, MealType
from app.schemas.meal import MealAnalysisResponse, MealCreate, MealListResponse, MealResponse, MealUpdate
from app.services.meal_service import MealService

router = APIRouter()


@router.post("/analyze", response_model=MealAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze_meal_image(
    current_user: CurrentUser,
    db: DB,
    image: UploadFile = File(..., description="Food image for AI analysis"),
    meal_type: MealType = Form(MealType.lunch),
    meal_time: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    _: None = Depends(rate_limit),
):
    """
    Upload a food image for AI-powered analysis.
    Uses YOLOv8 for detection, SAM2 for segmentation,
    EfficientNetV2 for classification, and MiDaS for portion estimation.
    """
    # Validate file type
    if image.content_type not in ["image/jpeg", "image/png", "image/webp", "image/heic"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image type: {image.content_type}",
        )

    # Validate file size
    content = await image.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image too large. Max size: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    service = MealService(db)
    start_time = time.time()

    result = await service.analyze_and_save_meal(
        user_id=current_user.id,
        image_content=content,
        image_filename=image.filename,
        meal_type=meal_type,
        meal_time=datetime.fromisoformat(meal_time) if meal_time else datetime.now(timezone.utc),
        notes=notes,
    )

    result["processing_time_ms"] = int((time.time() - start_time) * 1000)
    return result


@router.get("/", response_model=MealListResponse)
async def list_meals(
    current_user: CurrentUser,
    db: DB,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    meal_type: Optional[MealType] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    """List user's meal history with pagination and filtering."""
    service = MealService(db)
    return await service.list_meals(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        meal_type=meal_type,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/today", response_model=MealListResponse)
async def get_today_meals(current_user: CurrentUser, db: DB):
    """Get all meals logged today."""
    service = MealService(db)
    today = datetime.now(timezone.utc).date().isoformat()
    return await service.list_meals(
        user_id=current_user.id,
        date_from=today,
        date_to=today,
        page=1,
        page_size=50,
    )


@router.get("/{meal_id}", response_model=MealResponse)
async def get_meal(meal_id: uuid.UUID, current_user: CurrentUser, db: DB):
    """Get a specific meal by ID."""
    result = await db.execute(
        select(Meal)
        .where(Meal.id == meal_id, Meal.user_id == current_user.id)
        .options(selectinload(Meal.food_items))
    )
    meal = result.scalar_one_or_none()
    if not meal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found")
    return meal


@router.patch("/{meal_id}", response_model=MealResponse)
async def update_meal(
    meal_id: uuid.UUID,
    payload: MealUpdate,
    current_user: CurrentUser,
    db: DB,
):
    """Update meal metadata (type, name, notes, time)."""
    result = await db.execute(
        select(Meal)
        .where(Meal.id == meal_id, Meal.user_id == current_user.id)
        .options(selectinload(Meal.food_items))
    )
    meal = result.scalar_one_or_none()
    if not meal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(meal, field, value)

    await db.commit()
    await db.refresh(meal)
    return meal


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal(meal_id: uuid.UUID, current_user: CurrentUser, db: DB):
    """Delete a meal and all its food items."""
    result = await db.execute(
        select(Meal).where(Meal.id == meal_id, Meal.user_id == current_user.id)
    )
    meal = result.scalar_one_or_none()
    if not meal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found")

    await db.delete(meal)
    await db.commit()
