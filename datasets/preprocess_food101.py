"""
Preprocess Food-101 dataset for YOLO + classification training.
Splits into train/val/test (75/15/10) and creates YOLO annotation format.
"""
import json
import random
import shutil
from pathlib import Path

FOOD101_DIR = Path(__file__).parent / "food-101"
OUTPUT_DIR = Path(__file__).parent / "food_classification"
YOLO_DIR = Path(__file__).parent / "food_yolo"
SEED = 42

SPLITS = {"train": 0.75, "val": 0.15, "test": 0.10}


def load_food101_metadata():
    meta_dir = FOOD101_DIR / "meta"
    with open(meta_dir / "classes.txt") as f:
        classes = [l.strip() for l in f]
    with open(meta_dir / "train.txt") as f:
        train_files = [l.strip() for l in f]
    with open(meta_dir / "test.txt") as f:
        test_files = [l.strip() for l in f]
    return classes, train_files, test_files


def prepare_classification():
    """Create class-based folder structure for EfficientNetV2 training."""
    print("Preparing Food-101 for classification training...")
    classes, train_files, test_files = load_food101_metadata()

    for split in ["train", "val", "test"]:
        for cls in classes:
            (OUTPUT_DIR / split / cls).mkdir(parents=True, exist_ok=True)

    random.seed(SEED)
    for file_path in train_files:
        cls = file_path.split("/")[0]
        src = FOOD101_DIR / "images" / f"{file_path}.jpg"
        if not src.exists():
            continue
        # Split train into train/val
        r = random.random()
        if r < 0.85:
            dst = OUTPUT_DIR / "train" / cls / src.name
        else:
            dst = OUTPUT_DIR / "val" / cls / src.name
        shutil.copy2(src, dst)

    for file_path in test_files:
        cls = file_path.split("/")[0]
        src = FOOD101_DIR / "images" / f"{file_path}.jpg"
        if src.exists():
            dst = OUTPUT_DIR / "test" / cls / src.name
            shutil.copy2(src, dst)

    # Count
    for split in ["train", "val", "test"]:
        n = sum(1 for _ in (OUTPUT_DIR / split).rglob("*.jpg"))
        print(f"  {split}: {n} images")

    print(f"✅ Classification dataset ready at {OUTPUT_DIR}")


def create_yolo_data_yaml(classes):
    """Create YOLO data configuration."""
    YOLO_DIR.mkdir(exist_ok=True)
    yaml = f"path: {YOLO_DIR}\ntrain: images/train\nval: images/val\nnc: {len(classes)}\nnames: {classes}\n"
    (YOLO_DIR / "data.yaml").write_text(yaml)
    print(f"✅ YOLO data.yaml created at {YOLO_DIR / 'data.yaml'}")


if __name__ == "__main__":
    if not FOOD101_DIR.exists():
        print("❌ Food-101 not found. Run: bash download_datasets.sh food101")
        exit(1)

    classes, train_files, test_files = load_food101_metadata()
    print(f"Food-101: {len(classes)} classes, {len(train_files)} train, {len(test_files)} test images")

    prepare_classification()
    create_yolo_data_yaml(classes)
    print("\nDone! Next: python3 ../ai_models/training/train_classifier.py")
