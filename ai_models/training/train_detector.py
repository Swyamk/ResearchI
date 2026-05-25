"""
Training script for YOLOv8 food detector.
Fine-tunes YOLOv8 on Food-101 + UECFood256 datasets.
"""
import argparse
import os
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Train YOLOv8 Food Detector")
    parser.add_argument("--data", default="datasets/food_yolo/data.yaml")
    parser.add_argument("--model", default="yolov8x.pt")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--device", default="0")
    parser.add_argument("--project", default="runs/detect")
    parser.add_argument("--name", default="nutrimind_food256")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def create_data_yaml(dataset_root: Path, class_names: list, output_path: Path):
    """Create YOLO data.yaml configuration."""
    yaml_content = f"""
path: {dataset_root}
train: images/train
val: images/val
test: images/test

nc: {len(class_names)}
names: {class_names}
"""
    output_path.write_text(yaml_content)
    print(f"Created data.yaml at {output_path}")


def train(args):
    from ultralytics import YOLO

    # Load base model
    model = YOLO(args.model)

    # Train
    results = model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        workers=args.workers,
        device=args.device,
        project=args.project,
        name=args.name,
        resume=args.resume,
        # Augmentation
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=10.0,
        translate=0.1,
        scale=0.5,
        flipud=0.0,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,
        # Training params
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3.0,
        # Logging
        plots=True,
        save=True,
        save_period=10,
        val=True,
        verbose=True,
    )

    # Export best model
    best_path = Path(args.project) / args.name / "weights" / "best.pt"
    output_path = Path("../weights/yolov8_food.pt")
    if best_path.exists():
        import shutil
        shutil.copy(best_path, output_path)
        print(f"✅ Best model saved to {output_path}")

    return results


if __name__ == "__main__":
    args = parse_args()
    train(args)
