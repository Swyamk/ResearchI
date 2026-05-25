"""
Preprocess Nutrition5K dataset.
Nutrition5K provides RGB + depth images with ground-truth nutrition labels.
Used to train portion estimation and validate calorie predictions.
"""
import csv
import json
from pathlib import Path

N5K_DIR = Path(__file__).parent / "nutrition5k"
OUTPUT_DIR = Path(__file__).parent / "nutrition5k_processed"


def load_nutrition_metadata():
    """Load per-dish nutrition ground truth."""
    metadata_file = N5K_DIR / "metadata" / "dish_metadata_cafe1.csv"
    if not metadata_file.exists():
        metadata_file = N5K_DIR / "dish_metadata.csv"
    if not metadata_file.exists():
        print("❌ Nutrition5K metadata not found.")
        return []

    dishes = []
    with open(metadata_file, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dishes.append({
                "dish_id": row.get("dish_id", ""),
                "calories": float(row.get("total_calories", 0) or 0),
                "protein_g": float(row.get("total_protein", 0) or 0),
                "fat_g": float(row.get("total_fat", 0) or 0),
                "carbs_g": float(row.get("total_carbs", 0) or 0),
                "weight_g": float(row.get("total_mass", 0) or 0),
            })
    return dishes


def preprocess():
    print("Preprocessing Nutrition5K dataset...")
    OUTPUT_DIR.mkdir(exist_ok=True)

    dishes = load_nutrition_metadata()
    if not dishes:
        return

    # Save as JSON for easy loading during training
    output_file = OUTPUT_DIR / "nutrition_ground_truth.json"
    with open(output_file, "w") as f:
        json.dump(dishes, f, indent=2)

    print(f"✅ Nutrition5K: {len(dishes)} dishes processed")
    print(f"   Ground truth saved to {output_file}")


if __name__ == "__main__":
    preprocess()
