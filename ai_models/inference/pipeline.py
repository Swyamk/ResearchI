"""
NutriMind Inference Pipeline – GPT-4o Vision backend.
Replaces the YOLO → SAM2 → EfficientNetV2 → MiDaS stack with a single
OpenAI GPT-4o vision call for accurate food detection and portion estimation.
"""
import time
from io import BytesIO
from pathlib import Path
from typing import Any, Dict

import httpx
import numpy as np
from PIL import Image

from inference.openai_vision import analyze_image


class InferencePipeline:
    def __init__(self):
        self.models_loaded = False

    async def load_models(self):
        """No heavy model files to load — GPT-4o is called via API."""
        self.models_loaded = True

    async def _load_image(self, image_url: str) -> Image.Image:
        """Load image from URL or local path, return PIL Image."""
        if image_url.startswith(("http://", "https://")):
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(image_url)
                resp.raise_for_status()
                img = Image.open(BytesIO(resp.content)).convert("RGB")
        else:
            local_path = Path(image_url.lstrip("/"))
            if not local_path.exists():
                local_path = Path("/app") / image_url.lstrip("/")
            img = Image.open(local_path).convert("RGB")

        # Resize if too large (GPT-4o handles up to 2048px but 1024 is enough)
        max_size = 1024
        w, h = img.size
        if max(w, h) > max_size:
            scale = max_size / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        return img

    async def analyze(
        self,
        image_url: str,
        confidence_threshold: float = 0.45,
        max_detections: int = 10,
    ) -> Dict[str, Any]:
        """Analyze a food image using GPT-4o vision."""
        start = time.time()

        try:
            pil_image = await self._load_image(image_url)
        except Exception as e:
            return {
                "detected_items": [],
                "detection_count": 0,
                "processing_time_ms": 0,
                "error": f"Failed to load image: {e}",
                "model_versions": self._get_model_versions(),
            }

        try:
            items = await analyze_image(pil_image, max_items=max_detections)
        except Exception as e:
            return {
                "detected_items": [],
                "detection_count": 0,
                "processing_time_ms": round((time.time() - start) * 1000, 1),
                "error": f"OpenAI vision error: {e}",
                "model_versions": self._get_model_versions(),
            }

        # Filter by confidence threshold
        items = [i for i in items if i["confidence"] >= confidence_threshold]

        # Shape each item to match the format the backend expects
        enriched = []
        img_arr = np.array(pil_image)
        for item in items:
            enriched.append({
                "name": item["name"],
                "name_yolo": item["name"],
                "confidence": item["confidence"],
                "yolo_confidence": item["confidence"],
                "bbox": item["bbox"],
                "bbox_pixels": [],
                "area_ratio": 0.5,
                "segmentation_score": item["confidence"],
                "portion_g": item["portion_g"],
                "portion_description": item["portion_description"],
                "top_classifications": [
                    {"name": item["name"], "confidence": item["confidence"], "class_id": 0}
                ],
            })

        return {
            "detected_items": enriched,
            "detection_count": len(enriched),
            "processing_time_ms": round((time.time() - start) * 1000, 1),
            "image_size": list(img_arr.shape[:2]),
            "model_versions": self._get_model_versions(),
        }

    async def detect_only(self, image_url: str, confidence_threshold: float = 0.45) -> Dict[str, Any]:
        result = await self.analyze(image_url, confidence_threshold)
        return {"detections": result.get("detected_items", []), "count": result.get("detection_count", 0)}

    async def classify_only(self, image_url: str) -> Dict[str, Any]:
        result = await self.analyze(image_url)
        items = result.get("detected_items", [])
        return {"classifications": [{"name": i["name"], "confidence": i["confidence"]} for i in items]}

    def _get_model_versions(self) -> dict:
        return {
            "detector": "gpt-4o-vision",
            "segmentor": "gpt-4o-vision",
            "classifier": "gpt-4o-vision",
            "depth": "gpt-4o-vision",
        }
