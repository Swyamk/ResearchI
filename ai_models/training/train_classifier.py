"""
Training script for EfficientNetV2 Food Classifier.
Fine-tunes EfficientNetV2-L on Food-101 + UECFood256 + Indian Food dataset.
"""
import argparse
import json
import os
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.cuda.amp import GradScaler, autocast
from torch.utils.data import DataLoader, Dataset


def parse_args():
    parser = argparse.ArgumentParser(description="Train EfficientNetV2 Food Classifier")
    parser.add_argument("--data_dir", default="./datasets/food_classification")
    parser.add_argument("--num_classes", type=int, default=256)
    parser.add_argument("--model", default="tf_efficientnetv2_l")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--output", default="../weights/efficientnetv2_food256.pth")
    parser.add_argument("--resume", default=None)
    parser.add_argument("--label_smoothing", type=float, default=0.1)
    parser.add_argument("--mixup_alpha", type=float, default=0.2)
    return parser.parse_args()


class FoodDataset(Dataset):
    def __init__(self, data_dir: str, split: str = "train", transform=None):
        self.data_dir = Path(data_dir) / split
        self.transform = transform
        self.samples = []
        self.class_to_idx = {}

        self._load_samples()

    def _load_samples(self):
        classes = sorted([d.name for d in self.data_dir.iterdir() if d.is_dir()])
        self.class_to_idx = {c: i for i, c in enumerate(classes)}

        for class_name, idx in self.class_to_idx.items():
            class_dir = self.data_dir / class_name
            for img_path in class_dir.glob("*.jpg"):
                self.samples.append((img_path, idx))
            for img_path in class_dir.glob("*.png"):
                self.samples.append((img_path, idx))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        from PIL import Image
        img_path, label = self.samples[idx]
        img = Image.open(img_path).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, label


def train_epoch(model, loader, optimizer, criterion, scaler, device):
    model.train()
    total_loss = 0
    correct = 0
    total = 0

    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()

        with autocast():
            outputs = model(images)
            loss = criterion(outputs, labels)

        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()

        total_loss += loss.item()
        _, predicted = outputs.max(1)
        correct += predicted.eq(labels).sum().item()
        total += labels.size(0)

    return total_loss / len(loader), 100.0 * correct / total


def validate(model, loader, criterion, device):
    model.eval()
    total_loss = 0
    correct = top5_correct = total = 0

    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)

            total_loss += loss.item()
            _, predicted = outputs.max(1)
            correct += predicted.eq(labels).sum().item()

            # Top-5 accuracy
            _, top5 = outputs.topk(5, 1, True, True)
            top5 = top5.t()
            top5_correct += top5.eq(labels.view(1, -1).expand_as(top5)).any(0).sum().item()
            total += labels.size(0)

    return total_loss / len(loader), 100.0 * correct / total, 100.0 * top5_correct / total


def main():
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on: {device}")

    import timm
    # Create model
    model = timm.create_model(
        args.model,
        pretrained=True,
        num_classes=args.num_classes,
        drop_rate=0.3,
        drop_path_rate=0.2,
    )
    model = model.to(device)

    if args.resume:
        state = torch.load(args.resume, map_location=device)
        model.load_state_dict(state)
        print(f"Resumed from {args.resume}")

    # Transforms
    data_config = timm.data.resolve_model_data_config(model)
    train_transform = timm.data.create_transform(**data_config, is_training=True)
    val_transform = timm.data.create_transform(**data_config, is_training=False)

    train_dataset = FoodDataset(args.data_dir, "train", train_transform)
    val_dataset = FoodDataset(args.data_dir, "val", val_transform)

    train_loader = DataLoader(train_dataset, args.batch_size, shuffle=True,
                              num_workers=args.workers, pin_memory=True)
    val_loader = DataLoader(val_dataset, args.batch_size * 2, shuffle=False,
                            num_workers=args.workers, pin_memory=True)

    criterion = nn.CrossEntropyLoss(label_smoothing=args.label_smoothing)
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, args.epochs)
    scaler = GradScaler()

    best_acc = 0
    for epoch in range(args.epochs):
        train_loss, train_acc = train_epoch(model, train_loader, optimizer, criterion, scaler, device)
        val_loss, val_acc, val_top5 = validate(model, val_loader, criterion, device)
        scheduler.step()

        print(f"Epoch {epoch+1}/{args.epochs} | "
              f"Train Loss: {train_loss:.4f} Acc: {train_acc:.2f}% | "
              f"Val Loss: {val_loss:.4f} Top1: {val_acc:.2f}% Top5: {val_top5:.2f}%")

        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(model.state_dict(), args.output)
            print(f"  ✅ Best model saved ({best_acc:.2f}%)")

    print(f"\nTraining complete. Best Top-1: {best_acc:.2f}%")


if __name__ == "__main__":
    main()
