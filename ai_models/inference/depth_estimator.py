"""
MiDaS Depth Estimator – monocular depth estimation for portion size calculation.
Uses MiDaS v3.1 Large for accurate depth maps from single food images.
"""
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

WEIGHTS_DIR = Path(__file__).parent.parent / "weights"

# Average food densities (g/cm³) for volume-to-weight conversion
FOOD_DENSITIES = {
    "rice": 0.85, "dal": 0.90, "bread": 0.35, "chicken": 1.05,
    "vegetable": 0.70, "fruit": 0.85, "salad": 0.40, "soup": 1.00,
    "default": 0.80,
}

# Typical portion weight ranges (grams) for sanity check
PORTION_RANGES = {
    "rice": (100, 400), "dal": (150, 350), "chapati": (30, 60),
    "roti": (30, 60), "dosa": (80, 150), "idli": (40, 80),
    "chicken": (80, 250), "fish": (80, 200), "egg": (50, 70),
    "salad": (50, 200), "soup": (150, 400),
    "default": (50, 300),
}


class DepthEstimator:
    """MiDaS-based depth estimator for 3D portion size calculation."""

    def __init__(self):
        self.model = None
        self.transform = None
        self.loaded = False
        self.device = None

    def load(self):
        """Load MiDaS model via torch.hub."""
        try:
            import torch
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

            # Load MiDaS large from torch hub
            self.model = torch.hub.load(
                "intel-isl/MiDaS", "MiDaS_small",
                trust_repo=True,
            )
            midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
            self.transform = midas_transforms.small_transform

            self.model.to(self.device)
            self.model.eval()
            self.loaded = True
        except Exception as e:
            print(f"Warning: MiDaS load failed: {e}. Using mock depth estimator.")
            self.loaded = False

    def estimate_depth(self, image: np.ndarray) -> np.ndarray:
        """
        Estimate depth map from RGB image.

        Returns normalized depth map (H, W) in range [0, 1].
        Higher values = closer to camera.
        """
        if not self.loaded or self.model is None:
            return self._mock_depth(image)

        try:
            import torch
            input_batch = self.transform(image).to(self.device)

            with torch.no_grad():
                prediction = self.model(input_batch)
                prediction = torch.nn.functional.interpolate(
                    prediction.unsqueeze(1),
                    size=image.shape[:2],
                    mode="bicubic",
                    align_corners=False,
                ).squeeze()

            depth_map = prediction.cpu().numpy()

            # Normalize to [0, 1]
            d_min, d_max = depth_map.min(), depth_map.max()
            if d_max > d_min:
                depth_map = (depth_map - d_min) / (d_max - d_min)

            return depth_map

        except Exception as e:
            print(f"Depth estimation error: {e}")
            return self._mock_depth(image)

    def estimate_portion_weight(
        self,
        food_name: str,
        area_ratio: float,
        depth_map: Optional[np.ndarray] = None,
        mask: Optional[np.ndarray] = None,
        image_area_cm2: float = 900.0,  # Assume 30x30cm field of view
    ) -> Tuple[float, str]:
        """
        Estimate portion weight in grams.

        Uses segmentation area + depth map for 3D volume estimation,
        then converts to weight using food density.

        Returns: (weight_g, description)
        """
        # Estimate area of food item (cm²)
        food_area_cm2 = area_ratio * image_area_cm2

        # Estimate depth/height from depth map
        if depth_map is not None and mask is not None:
            try:
                mask_arr = np.array(mask) if not isinstance(mask, np.ndarray) else mask
                food_depths = depth_map[mask_arr > 0]
                avg_depth_normalized = float(np.mean(food_depths)) if len(food_depths) > 0 else 0.3
            except Exception:
                avg_depth_normalized = 0.3
        else:
            avg_depth_normalized = 0.3  # Default ~3cm height

        # Convert normalized depth to approximate height (cm)
        height_cm = avg_depth_normalized * 10  # 0-1 → 0-10cm
        height_cm = max(0.5, min(height_cm, 8.0))  # Clamp to realistic range

        # Volume estimation (cm³)
        volume_cm3 = food_area_cm2 * height_cm

        # Get density for food type
        food_lower = food_name.lower()
        density = FOOD_DENSITIES.get(food_lower, FOOD_DENSITIES["default"])
        for key in FOOD_DENSITIES:
            if key in food_lower:
                density = FOOD_DENSITIES[key]
                break

        # Calculate weight
        weight_g = volume_cm3 * density

        # Sanity check against known portion ranges
        food_range_key = "default"
        for key in PORTION_RANGES:
            if key in food_lower:
                food_range_key = key
                break

        min_g, max_g = PORTION_RANGES[food_range_key]
        weight_g = max(min_g, min(weight_g, max_g))

        # Human-readable description
        if weight_g < 100:
            desc = f"small portion (~{weight_g:.0f}g)"
        elif weight_g < 200:
            desc = f"medium portion (~{weight_g:.0f}g)"
        else:
            desc = f"large portion (~{weight_g:.0f}g)"

        return round(weight_g, 1), desc

    def _mock_depth(self, image: np.ndarray) -> np.ndarray:
        """Return a synthetic depth map for testing."""
        h, w = image.shape[:2] if hasattr(image, 'shape') else (480, 640)
        # Create a simple depth gradient with a peak in center (food is closer)
        y, x = np.mgrid[0:h, 0:w]
        depth = np.exp(-((x - w // 2) ** 2 + (y - h // 2) ** 2) / (2 * (min(h, w) // 3) ** 2))
        return depth.astype(np.float32)
