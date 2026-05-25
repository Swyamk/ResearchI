"""
Preprocess Recipe1M for ingredient parsing and nutrition lookup.
Extracts recipe-ingredient-nutrition mappings for training the recommendation engine.
"""
import json
from pathlib import Path

RECIPE1M_DIR = Path(__file__).parent / "recipe1M"
OUTPUT_DIR = Path(__file__).parent / "recipe1M_processed"


def preprocess_layer1(max_recipes: int = 100000):
    """Process layer1.json (recipe text data)."""
    layer1 = RECIPE1M_DIR / "layer1.json"
    if not layer1.exists():
        print("❌ Recipe1M layer1.json not found.")
        return []

    print(f"Loading Recipe1M layer1 (max {max_recipes} recipes)...")
    with open(layer1) as f:
        data = json.load(f)

    recipes = []
    for i, recipe in enumerate(data[:max_recipes]):
        ingredients = [
            ing.get("text", "").strip()
            for ing in recipe.get("ingredients", [])
        ]
        recipes.append({
            "id": recipe.get("id", ""),
            "title": recipe.get("title", ""),
            "ingredients": ingredients,
            "instructions_count": len(recipe.get("instructions", [])),
            "cuisine": recipe.get("cuisine", ""),
        })

    return recipes


def preprocess():
    print("Preprocessing Recipe1M dataset...")
    OUTPUT_DIR.mkdir(exist_ok=True)

    recipes = preprocess_layer1()
    if not recipes:
        return

    # Save processed recipes
    output_file = OUTPUT_DIR / "recipes_processed.json"
    with open(output_file, "w") as f:
        json.dump(recipes, f, indent=2)

    # Build ingredient frequency map
    ingredient_freq = {}
    for recipe in recipes:
        for ing in recipe["ingredients"]:
            word = ing.lower().split(",")[0].strip()
            ingredient_freq[word] = ingredient_freq.get(word, 0) + 1

    # Top 1000 ingredients
    top_ingredients = sorted(ingredient_freq.items(), key=lambda x: -x[1])[:1000]
    with open(OUTPUT_DIR / "top_ingredients.json", "w") as f:
        json.dump(dict(top_ingredients), f, indent=2)

    print(f"✅ Recipe1M processed: {len(recipes)} recipes, {len(ingredient_freq)} unique ingredients")


if __name__ == "__main__":
    preprocess()
