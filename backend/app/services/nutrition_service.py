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

# Per-100g nutrition for common foods — used when all external APIs fail
_BUILTIN_NUTRITION: Dict[str, dict] = {
    "apple_pie":           {"calories": 237, "protein_g": 2.0, "carbs_g": 34.0, "fat_g": 11.0, "fiber_g": 1.5, "sugar_g": 16.0, "sodium_mg": 193},
    "baklava":             {"calories": 428, "protein_g": 5.6, "carbs_g": 52.0, "fat_g": 22.0, "fiber_g": 1.8, "sugar_g": 30.0, "sodium_mg": 170},
    "banana":              {"calories": 89,  "protein_g": 1.1, "carbs_g": 23.0, "fat_g": 0.3,  "fiber_g": 2.6, "sugar_g": 12.0, "sodium_mg": 1},
    "biryani":             {"calories": 200, "protein_g": 8.0, "carbs_g": 27.0, "fat_g": 6.0,  "fiber_g": 1.5, "sugar_g": 1.0,  "sodium_mg": 420},
    "blueberries":         {"calories": 57,  "protein_g": 0.7, "carbs_g": 14.5, "fat_g": 0.3,  "fiber_g": 2.4, "sugar_g": 10.0, "sodium_mg": 1},
    "bread":               {"calories": 265, "protein_g": 9.0, "carbs_g": 49.0, "fat_g": 3.2,  "fiber_g": 2.7, "sugar_g": 5.0,  "sodium_mg": 491},
    "butter":              {"calories": 717, "protein_g": 0.9, "carbs_g": 0.1,  "fat_g": 81.0, "fiber_g": 0.0, "sugar_g": 0.1,  "sodium_mg": 643},
    "caesar_salad":        {"calories": 158, "protein_g": 4.0, "carbs_g": 8.0,  "fat_g": 13.0, "fiber_g": 1.5, "sugar_g": 2.0,  "sodium_mg": 310},
    "carrot_cake":         {"calories": 415, "protein_g": 4.5, "carbs_g": 52.0, "fat_g": 21.0, "fiber_g": 1.5, "sugar_g": 35.0, "sodium_mg": 340},
    "ceviche":             {"calories": 130, "protein_g": 18.0,"carbs_g": 6.0,  "fat_g": 4.0,  "fiber_g": 1.0, "sugar_g": 2.0,  "sodium_mg": 500},
    "chapati":             {"calories": 297, "protein_g": 9.0, "carbs_g": 55.0, "fat_g": 5.0,  "fiber_g": 4.0, "sugar_g": 1.0,  "sodium_mg": 390},
    "cheesecake":          {"calories": 321, "protein_g": 5.5, "carbs_g": 25.0, "fat_g": 22.0, "fiber_g": 0.4, "sugar_g": 18.0, "sodium_mg": 260},
    "chicken_curry":       {"calories": 150, "protein_g": 12.0,"carbs_g": 8.0,  "fat_g": 8.0,  "fiber_g": 1.5, "sugar_g": 3.0,  "sodium_mg": 450},
    "chicken_wings":       {"calories": 290, "protein_g": 25.0,"carbs_g": 0.0,  "fat_g": 20.0, "fiber_g": 0.0, "sugar_g": 0.0,  "sodium_mg": 370},
    "chocolate_cake":      {"calories": 371, "protein_g": 5.0, "carbs_g": 50.0, "fat_g": 18.0, "fiber_g": 2.0, "sugar_g": 35.0, "sodium_mg": 299},
    "chocolate_mousse":    {"calories": 280, "protein_g": 5.0, "carbs_g": 24.0, "fat_g": 18.0, "fiber_g": 1.5, "sugar_g": 20.0, "sodium_mg": 80},
    "churros":             {"calories": 402, "protein_g": 5.0, "carbs_g": 45.0, "fat_g": 22.0, "fiber_g": 1.5, "sugar_g": 14.0, "sodium_mg": 390},
    "cup_cakes":           {"calories": 389, "protein_g": 4.0, "carbs_g": 56.0, "fat_g": 17.0, "fiber_g": 0.8, "sugar_g": 38.0, "sodium_mg": 330},
    "dal":                 {"calories": 116, "protein_g": 8.0, "carbs_g": 18.0, "fat_g": 1.5,  "fiber_g": 4.5, "sugar_g": 2.0,  "sodium_mg": 240},
    "dal_makhani":         {"calories": 145, "protein_g": 7.0, "carbs_g": 17.0, "fat_g": 5.0,  "fiber_g": 5.0, "sugar_g": 2.5,  "sodium_mg": 310},
    "donuts":              {"calories": 452, "protein_g": 5.0, "carbs_g": 51.0, "fat_g": 25.0, "fiber_g": 1.2, "sugar_g": 22.0, "sodium_mg": 380},
    "dosa":                {"calories": 133, "protein_g": 3.5, "carbs_g": 25.0, "fat_g": 2.5,  "fiber_g": 1.0, "sugar_g": 1.0,  "sodium_mg": 290},
    "eggs_benedict":       {"calories": 286, "protein_g": 14.0,"carbs_g": 18.0, "fat_g": 18.0, "fiber_g": 0.8, "sugar_g": 3.0,  "sodium_mg": 760},
    "falafel":             {"calories": 333, "protein_g": 13.0,"carbs_g": 32.0, "fat_g": 18.0, "fiber_g": 5.0, "sugar_g": 3.0,  "sodium_mg": 585},
    "french_fries":        {"calories": 312, "protein_g": 3.4, "carbs_g": 41.0, "fat_g": 15.0, "fiber_g": 3.8, "sugar_g": 0.3,  "sodium_mg": 210},
    "french_toast":        {"calories": 229, "protein_g": 7.5, "carbs_g": 26.0, "fat_g": 10.0, "fiber_g": 1.0, "sugar_g": 7.0,  "sodium_mg": 330},
    "fried_rice":          {"calories": 163, "protein_g": 4.0, "carbs_g": 28.0, "fat_g": 4.0,  "fiber_g": 1.0, "sugar_g": 1.5,  "sodium_mg": 450},
    "gulab_jamun":         {"calories": 387, "protein_g": 5.5, "carbs_g": 57.0, "fat_g": 15.0, "fiber_g": 0.5, "sugar_g": 42.0, "sodium_mg": 190},
    "hamburger":           {"calories": 295, "protein_g": 17.0,"carbs_g": 24.0, "fat_g": 14.0, "fiber_g": 1.5, "sugar_g": 5.0,  "sodium_mg": 480},
    "hot_dog":             {"calories": 290, "protein_g": 12.0,"carbs_g": 23.0, "fat_g": 16.0, "fiber_g": 1.0, "sugar_g": 5.0,  "sodium_mg": 700},
    "ice_cream":           {"calories": 207, "protein_g": 3.5, "carbs_g": 24.0, "fat_g": 11.0, "fiber_g": 0.5, "sugar_g": 21.0, "sodium_mg": 80},
    "idli":                {"calories": 58,  "protein_g": 2.0, "carbs_g": 12.0, "fat_g": 0.3,  "fiber_g": 0.5, "sugar_g": 0.5,  "sodium_mg": 240},
    "khichdi":             {"calories": 118, "protein_g": 5.0, "carbs_g": 21.0, "fat_g": 2.0,  "fiber_g": 2.0, "sugar_g": 1.0,  "sodium_mg": 310},
    "lasagna":             {"calories": 166, "protein_g": 10.0,"carbs_g": 17.0, "fat_g": 6.0,  "fiber_g": 1.5, "sugar_g": 4.0,  "sodium_mg": 390},
    "macaroni_and_cheese": {"calories": 164, "protein_g": 7.0, "carbs_g": 22.0, "fat_g": 5.0,  "fiber_g": 1.0, "sugar_g": 4.0,  "sodium_mg": 440},
    "maple_syrup":         {"calories": 260, "protein_g": 0.0, "carbs_g": 67.0, "fat_g": 0.1,  "fiber_g": 0.0, "sugar_g": 60.0, "sodium_mg": 9},
    "miso_soup":           {"calories": 40,  "protein_g": 3.0, "carbs_g": 5.0,  "fat_g": 1.0,  "fiber_g": 1.0, "sugar_g": 1.5,  "sodium_mg": 630},
    "nachos":              {"calories": 346, "protein_g": 7.0, "carbs_g": 36.0, "fat_g": 19.0, "fiber_g": 3.5, "sugar_g": 1.5,  "sodium_mg": 560},
    "omelette":            {"calories": 154, "protein_g": 11.0,"carbs_g": 1.0,  "fat_g": 12.0, "fiber_g": 0.0, "sugar_g": 1.0,  "sodium_mg": 340},
    "pad_thai":            {"calories": 193, "protein_g": 10.0,"carbs_g": 25.0, "fat_g": 6.0,  "fiber_g": 1.5, "sugar_g": 5.0,  "sodium_mg": 430},
    "pakora":              {"calories": 265, "protein_g": 7.0, "carbs_g": 28.0, "fat_g": 14.0, "fiber_g": 3.0, "sugar_g": 2.0,  "sodium_mg": 370},
    "palak_paneer":        {"calories": 183, "protein_g": 9.0, "carbs_g": 8.0,  "fat_g": 13.0, "fiber_g": 2.5, "sugar_g": 2.0,  "sodium_mg": 400},
    "pancakes":            {"calories": 227, "protein_g": 6.0, "carbs_g": 35.0, "fat_g": 7.0,  "fiber_g": 1.2, "sugar_g": 8.0,  "sodium_mg": 480},
    "pav_bhaji":           {"calories": 170, "protein_g": 5.0, "carbs_g": 28.0, "fat_g": 5.0,  "fiber_g": 3.5, "sugar_g": 5.0,  "sodium_mg": 460},
    "pizza":               {"calories": 266, "protein_g": 11.0,"carbs_g": 33.0, "fat_g": 10.0, "fiber_g": 2.3, "sugar_g": 3.6,  "sodium_mg": 598},
    "powdered_sugar":      {"calories": 389, "protein_g": 0.0, "carbs_g": 100.0,"fat_g": 0.0,  "fiber_g": 0.0, "sugar_g": 97.0, "sodium_mg": 2},
    "pulao":               {"calories": 155, "protein_g": 3.5, "carbs_g": 28.0, "fat_g": 3.5,  "fiber_g": 1.5, "sugar_g": 1.0,  "sodium_mg": 320},
    "ramen":               {"calories": 188, "protein_g": 8.0, "carbs_g": 26.0, "fat_g": 5.0,  "fiber_g": 1.0, "sugar_g": 2.0,  "sodium_mg": 860},
    "red_velvet_cake":     {"calories": 369, "protein_g": 4.5, "carbs_g": 48.0, "fat_g": 18.0, "fiber_g": 1.0, "sugar_g": 33.0, "sodium_mg": 330},
    "rice":                {"calories": 130, "protein_g": 2.7, "carbs_g": 28.0, "fat_g": 0.3,  "fiber_g": 0.4, "sugar_g": 0.0,  "sodium_mg": 1},
    "risotto":             {"calories": 166, "protein_g": 5.0, "carbs_g": 27.0, "fat_g": 4.5,  "fiber_g": 1.0, "sugar_g": 1.5,  "sodium_mg": 390},
    "samosa":              {"calories": 308, "protein_g": 6.0, "carbs_g": 32.0, "fat_g": 18.0, "fiber_g": 3.0, "sugar_g": 2.0,  "sodium_mg": 420},
    "spaghetti_bolognese": {"calories": 187, "protein_g": 11.0,"carbs_g": 22.0, "fat_g": 6.0,  "fiber_g": 2.0, "sugar_g": 4.0,  "sodium_mg": 350},
    "spring_rolls":        {"calories": 165, "protein_g": 4.5, "carbs_g": 22.0, "fat_g": 7.0,  "fiber_g": 2.0, "sugar_g": 2.0,  "sodium_mg": 310},
    "steak":               {"calories": 271, "protein_g": 26.0,"carbs_g": 0.0,  "fat_g": 18.0, "fiber_g": 0.0, "sugar_g": 0.0,  "sodium_mg": 59},
    "sushi":               {"calories": 150, "protein_g": 6.0, "carbs_g": 25.0, "fat_g": 2.5,  "fiber_g": 1.0, "sugar_g": 3.0,  "sodium_mg": 420},
    "syrup":               {"calories": 260, "protein_g": 0.0, "carbs_g": 67.0, "fat_g": 0.0,  "fiber_g": 0.0, "sugar_g": 55.0, "sodium_mg": 10},
    "tacos":               {"calories": 226, "protein_g": 10.0,"carbs_g": 23.0, "fat_g": 11.0, "fiber_g": 3.0, "sugar_g": 2.0,  "sodium_mg": 480},
    "tiramisu":            {"calories": 240, "protein_g": 5.0, "carbs_g": 26.0, "fat_g": 13.0, "fiber_g": 0.5, "sugar_g": 18.0, "sodium_mg": 130},
    "upma":                {"calories": 148, "protein_g": 4.0, "carbs_g": 22.0, "fat_g": 5.0,  "fiber_g": 2.0, "sugar_g": 1.5,  "sodium_mg": 340},
    "waffles":             {"calories": 291, "protein_g": 8.0, "carbs_g": 37.0, "fat_g": 13.0, "fiber_g": 1.5, "sugar_g": 10.0, "sodium_mg": 490},
}


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

    # ── Built-in Fallback ──────────────────────────────────────────────────────
    def search_builtin(self, food_name: str) -> Optional[dict]:
        """Exact or fuzzy match against the built-in nutrition table."""
        key = food_name.lower().strip().replace(" ", "_")
        if key in _BUILTIN_NUTRITION:
            return {"source": "builtin", "name": key, **_BUILTIN_NUTRITION[key]}
        # Fuzzy: check if any builtin key is a substring of the query or vice versa
        for builtin_key, data in _BUILTIN_NUTRITION.items():
            if builtin_key in key or key in builtin_key:
                return {"source": "builtin", "name": builtin_key, **data}
        return None

    # ── Unified Search ─────────────────────────────────────────────────────────
    async def search_all(self, food_name: str) -> dict:
        """Search all nutrition databases and return best match."""
        # Clean name: underscores → spaces for external API queries
        clean_name = food_name.replace("_", " ").strip()

        # Priority: Indian FCD → USDA → OpenFoodFacts → built-in table
        indian_results = self.search_indian_fcd(clean_name)
        usda_results = await self.search_usda(clean_name)
        off_results = await self.search_openfoodfacts(clean_name)
        builtin_match = self.search_builtin(food_name)

        return {
            "query": food_name,
            "indian_fcd": indian_results[:3],
            "usda": usda_results[:3],
            "openfoodfacts": off_results[:2],
            "best_match": (
                indian_results[0] if indian_results else
                usda_results[0] if usda_results else
                off_results[0] if off_results else
                builtin_match
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
