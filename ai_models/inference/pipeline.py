"""
Full AI Inference Pipeline:
YOLOv8 (detect) → SAM2 (segment) → EfficientNetV2 (classify) → MiDaS (depth/portion)
"""
import asyncio
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import numpy as np
from PIL import Image

from inference.food_detector import FoodDetector
from inference.food_segmentor import FoodSegmentor
from inference.food_classifier import FoodClassifier
from inference.depth_estimator import DepthEstimator


class InferencePipeline:
    """
    Orchestrates all 4 AI models for complete food analysis.

    Pipeline:
    1. Load image from URL
    2. YOLOv8: detect all food items with bounding boxes
    3. SAM2: segment each detected food region
    4. EfficientNetV2: classify each cropped food region (Top-5)
    5. MiDaS: estimate depth map → portion size → weight
    6. Return structured results with nutrition hints
    """

    def __init__(self):
        self.detector = FoodDetector()
        self.segmentor = FoodSegmentor()
        self.classifier = FoodClassifier(top_k=5)
        self.depth_estimator = DepthEstimator()
        self.models_loaded = False

    async def load_models(self):
        """Load all models asynchronously (runs in thread pool)."""
        loop = asyncio.get_event_loop()

        await loop.run_in_executor(None, self.detector.load)
        await loop.run_in_executor(None, self.segmentor.load)
        await loop.run_in_executor(None, self.classifier.load)
        await loop.run_in_executor(None, self.depth_estimator.load)

        self.models_loaded = True

    async def _load_image(self, image_url: str) -> np.ndarray:
        """Load image from URL or local path into numpy array."""
        if image_url.startswith(("http://", "https://")):
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(image_url)
                resp.raise_for_status()
                from io import BytesIO
                img = Image.open(BytesIO(resp.content)).convert("RGB")
        else:
            # Local file path
            local_path = Path(image_url.lstrip("/"))
            if not local_path.exists():
                # Try with /app prefix
                local_path = Path("/app") / image_url.lstrip("/")
            img = Image.open(local_path).convert("RGB")

        # Resize if too large (max 1024px on longest side)
        max_size = 1024
        w, h = img.size
        if max(w, h) > max_size:
            scale = max_size / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        return np.array(img)

    async def analyze(
        self,
        image_url: str,
        confidence_threshold: float = 0.45,
        max_detections: int = 10,
    ) -> Dict[str, Any]:
        """Run full 4-stage inference pipeline."""
        start_time = time.time()

        # 1. Load image
        try:
            image = await self._load_image(image_url)
        except Exception as e:
            return {
                "detected_items": [],
                "detection_count": 0,
                "processing_time_ms": 0,
                "error": f"Failed to load image: {str(e)}",
                "model_versions": self._get_model_versions(),
            }

        loop = asyncio.get_event_loop()

        # 2. YOLOv8 Detection
        detections = await loop.run_in_executor(
            None, lambda: self.detector.detect(image, confidence_threshold, max_detections)
        )

        # 3. MiDaS Depth Estimation (run once for whole image)
        depth_map = await loop.run_in_executor(
            None, lambda: self.depth_estimator.estimate_depth(image)
        )

        # 4. Per-item: SAM2 + EfficientNetV2 + Portion Estimation
        enriched_items = []
        for det in detections:
            # SAM2 segmentation
            seg_result = await loop.run_in_executor(
                None,
                lambda d=det: self.segmentor.segment_from_bbox(image, d.get("bbox_pixels", [0, 0, 100, 100]))
            )

            # EfficientNetV2 classification (refines YOLO's class)
            classifications = await loop.run_in_executor(
                None,
                lambda d=det: self.classifier.classify_from_bbox(image, d["bbox"])
            )

            # Use classifier's top prediction (more accurate than YOLO class)
            best_class = classifications[0] if classifications else {"name": det["name"], "confidence": det["confidence"]}
            food_name = best_class["name"]

            # Portion weight estimation from depth + segmentation
            area_ratio = seg_result.get("area_ratio", det.get("area_ratio", 0.1))
            weight_g, portion_desc = await loop.run_in_executor(
                None,
                lambda fn=food_name, ar=area_ratio: self.depth_estimator.estimate_portion_weight(
                    fn, ar, depth_map, None
                )
            )

            enriched_items.append({
                "name": food_name,
                "name_yolo": det["name"],
                "confidence": best_class["confidence"],
                "yolo_confidence": det["confidence"],
                "bbox": det["bbox"],
                "bbox_pixels": det.get("bbox_pixels", []),
                "area_ratio": area_ratio,
                "segmentation_score": seg_result.get("score", 0),
                "portion_g": weight_g,
                "portion_description": portion_desc,
                "top_classifications": classifications[:3],
            })

        processing_time_ms = round((time.time() - start_time) * 1000, 1)

        return {
            "detected_items": enriched_items,
            "detection_count": len(enriched_items),
            "processing_time_ms": processing_time_ms,
            "image_size": list(image.shape[:2]),
            "model_versions": self._get_model_versions(),
        }

    async def detect_only(
        self, image_url: str, confidence_threshold: float = 0.45
    ) -> Dict[str, Any]:
        """Fast detection-only pipeline (YOLOv8 only)."""
        image = await self._load_image(image_url)
        loop = asyncio.get_event_loop()
        detections = await loop.run_in_executor(
            None, lambda: self.detector.detect(image, confidence_threshold)
        )
        return {"detections": detections, "count": len(detections)}

    async def classify_only(self, image_url: str) -> Dict[str, Any]:
        """Classification-only pipeline (EfficientNetV2 on whole image)."""
        image = await self._load_image(image_url)
        loop = asyncio.get_event_loop()
        classifications = await loop.run_in_executor(
            None, lambda: self.classifier.classify(image, top_k=10)
        )
        return {"classifications": classifications}

    def _get_model_versions(self) -> dict:
        return {
            "detector": "YOLOv8x-food256",
            "segmentor": "SAM2-hiera-large",
            "classifier": "EfficientNetV2-L-food256",
            "depth": "MiDaS-v3.1-small",
        }
