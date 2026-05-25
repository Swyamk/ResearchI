"""Preprocess UECFood256 for classification training."""
import shutil
from pathlib import Path

UECFOOD_DIR = Path(__file__).parent / "UECFood256"
OUTPUT_DIR = Path(__file__).parent / "food_classification"


def preprocess():
    print("Preprocessing UECFood256...")
    categories = {}
    cat_file = UECFOOD_DIR / "category.txt"

    if not cat_file.exists():
        print("❌ UECFood256 not found.")
        return

    with open(cat_file) as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) >= 2:
                categories[parts[0]] = parts[1].replace(" ", "_").lower()

    processed = 0
    for class_id, class_name in categories.items():
        src_dir = UECFOOD_DIR / class_id
        if not src_dir.exists():
            continue
        for split in ["train", "val"]:
            (OUTPUT_DIR / split / class_name).mkdir(parents=True, exist_ok=True)

        images = list(src_dir.glob("*.jpg"))
        split_idx = int(len(images) * 0.85)
        for i, img in enumerate(images):
            split = "train" if i < split_idx else "val"
            dst = OUTPUT_DIR / split / class_name / img.name
            shutil.copy2(img, dst)
            processed += 1

    print(f"✅ UECFood256 preprocessed: {processed} images, {len(categories)} classes")


if __name__ == "__main__":
    preprocess()
