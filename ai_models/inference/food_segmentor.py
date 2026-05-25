"""
SAM2 Food Segmentor – precise pixel-level food segmentation.
Uses Meta's Segment Anything Model 2 for food region extraction.
"""
from pathlib import Path
from typing import List, Optional

import numpy as np

WEIGHTS_DIR = Path(__file__).parent.parent / "weights"


class FoodSegmentor:
    """SAM2-based food segmentation model."""

    def __init__(self):
        self.predictor = None
        self.loaded = False
        self.model_path = WEIGHTS_DIR / "sam2_hiera_large.pt"
        self.model_cfg = "sam2_hiera_l.yaml"

    def load(self):
        """Load SAM2 model."""
        try:
            from sam2.build_sam import build_sam2
            from sam2.sam2_image_predictor import SAM2ImagePredictor

            if self.model_path.exists():
                sam2_model = build_sam2(self.model_cfg, str(self.model_path))
                self.predictor = SAM2ImagePredictor(sam2_model)
                self.loaded = True
            else:
                print("SAM2 weights not found. Using mock segmentor.")
                self.loaded = False
        except Exception as e:
            print(f"Warning: SAM2 load failed: {e}. Using mock segmentor.")
            self.loaded = False

    def segment_from_bbox(
        self,
        image: np.ndarray,
        bbox_pixels: List[float],
    ) -> dict:
        """
        Segment a food item using bounding box prompt.

        Args:
            image: RGB numpy array (H, W, 3)
            bbox_pixels: [x1, y1, x2, y2] in pixel coords

        Returns:
            mask: binary mask (H, W)
            area_pixels: number of pixels in mask
            area_ratio: fraction of image
            score: SAM2 confidence score
        """
        if not self.loaded or self.predictor is None:
            return self._mock_segment(image, bbox_pixels)

        try:
            import torch
            self.predictor.set_image(image)

            box = np.array(bbox_pixels)
            masks, scores, _ = self.predictor.predict(
                box=box,
                multimask_output=False,
            )

            mask = masks[0]
            score = float(scores[0])
            area_pixels = int(mask.sum())
            h, w = image.shape[:2]
            area_ratio = area_pixels / (h * w)

            return {
                "mask": mask.tolist(),
                "area_pixels": area_pixels,
                "area_ratio": round(area_ratio, 4),
                "score": round(score, 4),
            }
        except Exception as e:
            print(f"Segmentation error: {e}")
            return self._mock_segment(image, bbox_pixels)

    def segment_all_foods(
        self,
        image: np.ndarray,
        detections: List[dict],
    ) -> List[dict]:
        """Segment all detected food items."""
        results = []
        for det in detections:
            bbox = det.get("bbox_pixels", [0, 0, 100, 100])
            seg = self.segment_from_bbox(image, bbox)
            results.append({**det, "segmentation": seg})
        return results

    def estimate_volume_from_mask(
        self,
        mask: np.ndarray,
        depth_map: np.ndarray,
        pixel_size_cm: float = 0.1,
    ) -> float:
        """Estimate food volume (cm³) from segmentation mask + depth map."""
        try:
            food_depths = depth_map[mask > 0]
            if len(food_depths) == 0:
                return 0.0
            avg_depth_cm = float(np.mean(food_depths)) * 10  # normalized → cm
            area_cm2 = mask.sum() * (pixel_size_cm ** 2)
            volume_cm3 = area_cm2 * avg_depth_cm
            return round(volume_cm3, 2)
        except Exception:
            return 0.0

    def _mock_segment(self, image: np.ndarray, bbox: List[float]) -> dict:
        h, w = image.shape[:2] if hasattr(image, 'shape') else (500, 500)
        return {
            "mask": None,
            "area_pixels": int(h * w * 0.15),
            "area_ratio": 0.15,
            "score": 0.88,
        }
