"""
Nutrition Service – USDA FoodData Central, OpenFoodFacts, Indian FCD integration.
"""
import csv
import functools
from pathlib import Path
from typing import Dict, List, Optional

import httpx

from app.config import settings
from app.redis_client import redis_client

USDA_CACHE_TTL = 86400  # 24 hours


class NutritionService:
    """
    Unified nutrition data service that queries:
    1. USDA FoodData Central
    2. OpenFoodFacts
    3. Indian Food Composition Tables (IFCT 2017)
    """

    def __init__(self):
        self._indian_fcd: Optional[Dict[str, dict]] = None

    # ── USDA FoodData Central ──────────────────────────────────────────────────
    async def search_usda(self, query: str, page_size: int = 5) -> List[dict]:
        """Search USDA FoodData Central by food name."""
        cache_key = f"usda:search:{query.lower().strip()}"
        cached = await redis_client.get(cache_key)
        if cached:
            return cached

        if not settings.USDA_API_KEY:
            return []

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{settings.USDA_BASE_URL}/foods/search",
                    params={
                        "query": query,
                        "api_key": settings.USDA_API_KEY,
                        "pageSize": page_size,
                        "dataType": ["SR Legacy", "Foundation", "Survey (FNDDS)"],
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                foods = data.get("foods", [])
                results = [self._parse_usda_food(f) for f in foods]
                await redis_client.set(cache_key, results, USDA_CACHE_TTL)
                return results
        except Exception:
            return []

    async def get_usda_food(self, fdc_id: str) -> Optional[dict]:
        """Get detailed nutrition info for a specific USDA food item."""
        cache_key = f"usda:food:{fdc_id}"
        cached = await redis_client.get(cache_key)
        if cached:
            return cached

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{settings.USDA_BASE_URL}/food/{fdc_id}",
                    params={"api_key": settings.USDA_API_KEY},
                )
                resp.raise_for_status()
                food = resp.json()
                result = self._parse_usda_food(food)
                await redis_client.set(cache_key, result, USDA_CACHE_TTL)
                return result
        except Exception:
            return None

    def _parse_usda_food(self, food: dict) -> dict:
        """Parse USDA API response to standardized nutrition dict."""
        nutrients = {}
        for n in food.get("foodNutrients", []):
            name = n.get("nutrientName", n.get("name", ""))
            value = n.get("value", n.get("amount", 0)) or 0
            unit = n.get("unitName", n.get("unitAbbr", ""))
            nutrients[name] = {"value": value, "unit": unit}

        def get_nutrient(names: List[str], default=0.0) -> float:
            for name in names:
                for key, val in nutrients.items():
                    if name.lower() in key.lower():
                        return float(val["value"])
            return default

        return {
            "source": "usda",
            "fdc_id": str(food.get("fdcId", "")),
            "name": food.get("description", food.get("lowercaseDescription", "")),
            "category": food.get("foodCategory", food.get("foodCategoryLabel", "")),
            "calories": get_nutrient(["energy", "calories"]),
            "protein_g": get_nutrient(["protein"]),
            "carbs_g": get_nutrient(["carbohydrate", "carbs"]),
            "fat_g": get_nutrient(["total lipid", "fat"]),
            "fiber_g": get_nutrient(["fiber"]),
            "sugar_g": get_nutrient(["sugars"]),
            "sodium_mg": get_nutrient(["sodium"]),
            "cholesterol_mg": get_nutrient(["cholesterol"]),
            "vitamin_c_mg": get_nutrient(["vitamin c"]),
            "vitamin_d_mcg": get_nutrient(["vitamin d"]),
            "calcium_mg": get_nutrient(["calcium"]),
            "iron_mg": get_nutrient(["iron"]),
            "potassium_mg": get_nutrient(["potassium"]),
            "magnesium_mg": get_nutrient(["magnesium"]),
            "zinc_mg": get_nutrient(["zinc"]),
            "omega3_g": get_nutrient(["omega-3", "ala", "epa"]),
            "vitamin_a_mcg": get_nutrient(["vitamin a"]),
            "vitamin_b12_mcg": get_nutrient(["vitamin b-12", "cobalamin"]),
            "folate_mcg": get_nutrient(["folate", "folic"]),
        }

    # ── OpenFoodFacts ──────────────────────────────────────────────────────────
    async def search_openfoodfacts(self, query: str, page_size: int = 5) -> List[dict]:
        """Search OpenFoodFacts by product name."""
        cache_key = f"off:search:{query.lower().strip()}"
        cached = await redis_client.get(cache_key)
        if cached:
            return cached

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{settings.OPENFOODFACTS_BASE_URL}/search",
                    params={
                        "search_terms": query,
                        "page_size": page_size,
                        "fields": "product_name,nutriments,image_url,categories",
                    },
                    headers={"User-Agent": settings.OPENFOODFACTS_USER_AGENT},
                )
                resp.raise_for_status()
                data = resp.json()
                products = data.get("products", [])
                results = [self._parse_off_product(p) for p in products if p.get("product_name")]
                await redis_client.set(cache_key, results, USDA_CACHE_TTL)
                return results
        except Exception:
            return []

    def _parse_off_product(self, product: dict) -> dict:
        """Parse OpenFoodFacts product to standardized nutrition dict."""
        n = product.get("nutriments", {})

        def get_n(key: str, default=0.0) -> float:
            return float(n.get(f"{key}_100g", n.get(key, default)) or default)

        return {
            "source": "openfoodfacts",
            "off_id": product.get("_id", ""),
            "name": product.get("product_name", ""),
            "category": product.get("categories", "").split(",")[0].strip(),
            "image_url": product.get("image_url", ""),
            "calories": get_n("energy-kcal"),
            "protein_g": get_n("proteins"),
            "carbs_g": get_n("carbohydrates"),
            "fat_g": get_n("fat"),
            "fiber_g": get_n("fiber"),
            "sugar_g": get_n("sugars"),
            "sodium_mg": get_n("sodium") * 1000,  # g to mg
            "calcium_mg": get_n("calcium") * 1000,
            "iron_mg": get_n("iron") * 1000,
        }

    # ── Indian Food Composition ────────────────────────────────────────────────
    def _load_indian_fcd(self) -> Dict[str, dict]:
        """Load Indian Food Composition Tables (IFCT 2017) from CSV."""
        if self._indian_fcd is not None:
            return self._indian_fcd

        path = Path(settings.INDIAN_FCD_PATH)
        self._indian_fcd = {}

        if not path.exists():
            return self._indian_fcd

        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get("Food Name", "").strip().lower()
                    if name:
                        self._indian_fcd[name] = {
                            "source": "indian_fcd",
                            "name": row.get("Food Name", ""),
                            "category": row.get("Food Group", ""),
                            "calories": float(row.get("Energy (kcal)", 0) or 0),
                            "protein_g": float(row.get("Protein (g)", 0) or 0),
                            "carbs_g": float(row.get("Carbohydrate (g)", 0) or 0),
                            "fat_g": float(row.get("Fat (g)", 0) or 0),
                            "fiber_g": float(row.get("Fibre (g)", 0) or 0),
                            "calcium_mg": float(row.get("Calcium (mg)", 0) or 0),
                            "iron_mg": float(row.get("Iron (mg)", 0) or 0),
                            "vitamin_c_mg": float(row.get("Vitamin C (mg)", 0) or 0),
                        }
        except Exception:
            pass

        return self._indian_fcd

    def search_indian_fcd(self, query: str) -> List[dict]:
        """Search Indian Food Composition database."""
        db = self._load_indian_fcd()
        query_lower = query.lower()
        results = []

        for name, data in db.items():
            if query_lower in name or any(w in name for w in query_lower.split()):
                results.append(data)
                if len(results) >= 5:
                    break

        return results

    # ── Unified Search ─────────────────────────────────────────────────────────
    async def search_all(self, food_name: str) -> dict:
        """Search all nutrition databases and return best match."""
        # Priority: Indian FCD for Indian foods → USDA → OpenFoodFacts
        indian_results = self.search_indian_fcd(food_name)
        usda_results = await self.search_usda(food_name)
        off_results = await self.search_openfoodfacts(food_name)

        return {
            "query": food_name,
            "indian_fcd": indian_results[:3],
            "usda": usda_results[:3],
            "openfoodfacts": off_results[:2],
            "best_match": (
                indian_results[0] if indian_results else
                usda_results[0] if usda_results else
                off_results[0] if off_results else None
            ),
        }

    async def get_nutrition_for_food(
        self, food_name: str, portion_g: float = 100.0
    ) -> Optional[dict]:
        """
        Get nutrition data for a food item scaled to portion size.
        Returns nutrition per given portion weight (grams).
        """
        result = await self.search_all(food_name)
        best = result.get("best_match")

        if not best:
            return None

        # Scale from per-100g to actual portion
        scale = portion_g / 100.0

        return {
            **{
                k: round(v * scale, 2) if isinstance(v, (int, float)) else v
                for k, v in best.items()
            },
            "portion_g": portion_g,
        }
