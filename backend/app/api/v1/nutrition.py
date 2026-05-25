"""Nutrition API routes – search USDA, OpenFoodFacts, Indian FCD."""
from typing import Optional

from fastapi import APIRouter, Query

from app.core.dependencies import DB, CurrentUser
from app.services.nutrition_service import NutritionService

router = APIRouter()


@router.get("/search")
async def search_food(
    query: str = Query(..., min_length=2, description="Food name to search"),
    source: Optional[str] = Query(None, description="usda | openfoodfacts | indian | all"),
    current_user: CurrentUser = None,
):
    """Search nutrition databases for a food item."""
    service = NutritionService()
    if source == "usda":
        results = await service.search_usda(query)
        return {"source": "usda", "results": results}
    elif source == "openfoodfacts":
        results = await service.search_openfoodfacts(query)
        return {"source": "openfoodfacts", "results": results}
    elif source == "indian":
        results = service.search_indian_fcd(query)
        return {"source": "indian_fcd", "results": results}
    else:
        return await service.search_all(query)


@router.get("/food/{fdc_id}")
async def get_food_detail(fdc_id: str, current_user: CurrentUser):
    """Get detailed nutrition info for a USDA food item by FDC ID."""
    service = NutritionService()
    result = await service.get_usda_food(fdc_id)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Food not found in USDA database")
    return result


@router.get("/calculate")
async def calculate_nutrition(
    food_name: str = Query(...),
    portion_g: float = Query(100.0, gt=0, le=5000),
    current_user: CurrentUser = None,
):
    """Calculate nutrition for a specific food at a given portion size."""
    service = NutritionService()
    result = await service.get_nutrition_for_food(food_name, portion_g)
    if not result:
        return {"message": "Food not found", "food_name": food_name}
    return result
