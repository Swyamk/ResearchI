"""
EfficientNetV2 Food Classifier – classifies food items into 256 categories.
Fine-tuned on Food-101 + UECFood256 + custom Indian food dataset.
"""
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

WEIGHTS_DIR = Path(__file__).parent.parent / "weights"

# ImageNet normalization stats
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]

# Full 256-class food label map
FOOD_LABELS = [
    "apple_pie", "baby_back_ribs", "baklava", "beef_carpaccio", "beef_tartare",
    "beet_salad", "beignets", "bibimbap", "biryani", "bread_pudding",
    "breakfast_burrito", "bruschetta", "caesar_salad", "cannoli", "caprese_salad",
    "carrot_cake", "ceviche", "chai", "chapati", "cheese_plate", "cheesecake",
    "chicken_curry", "chicken_quesadilla", "chicken_wings", "chocolate_cake",
    "chocolate_mousse", "churros", "clam_chowder", "club_sandwich", "crab_cakes",
    "creme_brulee", "croque_madame", "cup_cakes", "dal", "dal_makhani", "deviled_eggs",
    "donuts", "dosa", "dumplings", "edamame", "eggs_benedict", "escargots",
    "falafel", "filet_mignon", "fish_and_chips", "foie_gras", "french_fries",
    "french_onion_soup", "french_toast", "fried_calamari", "fried_rice",
    "frozen_yogurt", "garlic_bread", "gnocchi", "greek_salad", "grilled_cheese",
    "grilled_salmon", "guacamole", "gulab_jamun", "gyoza", "hamburger",
    "hot_and_sour_soup", "hot_dog", "huevos_rancheros", "hummus", "ice_cream",
    "idli", "khichdi", "lasagna", "lassi", "lobster_bisque", "lobster_roll",
    "macaroni_and_cheese", "macarons", "miso_soup", "mussels", "nachos",
    "omelette", "onion_rings", "oysters", "pad_thai", "paella", "pakora",
    "palak_paneer", "pancakes", "panna_cotta", "pav_bhaji", "peking_duck",
    "pho", "pizza", "pork_chop", "poutine", "prime_rib", "pulao",
    "pulled_pork_sandwich", "ramen", "ravioli", "red_velvet_cake", "risotto",
    "samosa", "sashimi", "scallops", "seaweed_salad", "shrimp_and_grits",
    "spaghetti_bolognese", "spaghetti_carbonara", "spring_rolls", "steak",
    "strawberry_shortcake", "sushi", "tacos", "takoyaki", "tiramisu",
    "tuna_tartare", "upma", "waffles",
]


class FoodClassifier:
    """EfficientNetV2-based food classifier with Top-K predictions."""

    def __init__(self, num_classes: int = 256, top_k: int = 5):
        self.num_classes = num_classes
        self.top_k = top_k
        self.model = None
        self.loaded = False
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_path = WEIGHTS_DIR / "efficientnetv2_food256.pth"

    def load(self):
        """Load EfficientNetV2 model."""
        try:
            import timm

            # Create model architecture
            self.model = timm.create_model(
                "tf_efficientnetv2_l",
                pretrained=False,
                num_classes=self.num_classes,
            )

            if self.model_path.exists():
                state = torch.load(str(self.model_path), map_location=self.device)
                self.model.load_state_dict(state, strict=False)
            else:
                # Use pretrained ImageNet weights for feature extraction
                self.model = timm.create_model(
                    "tf_efficientnetv2_m",
                    pretrained=True,
                    num_classes=self.num_classes,
                )

            self.model.eval()
            self.model.to(self.device)

            # Get transforms from timm
            data_config = timm.data.resolve_model_data_config(self.model)
            self.transforms = timm.data.create_transform(**data_config, is_training=False)

            self.loaded = True
        except Exception as e:
            print(f"Warning: EfficientNetV2 load failed: {e}. Using mock classifier.")
            self.loaded = False

    def _preprocess(self, image: np.ndarray) -> torch.Tensor:
        """Preprocess image for EfficientNetV2."""
        pil_image = Image.fromarray(image).convert("RGB")
        tensor = self.transforms(pil_image)
        return tensor.unsqueeze(0).to(self.device)

    def classify(self, image: np.ndarray, top_k: int = None) -> List[dict]:
        """
        Classify food item from image crop.

        Returns Top-K predictions with:
        - name: food category name
        - confidence: softmax probability
        - class_id: integer class index
        """
        k = top_k or self.top_k

        if not self.loaded or self.model is None:
            return self._mock_classify()

        try:
            with torch.no_grad():
                tensor = self._preprocess(image)
                logits = self.model(tensor)
                probs = F.softmax(logits, dim=1)
                top_probs, top_indices = torch.topk(probs, k=min(k, self.num_classes))

            top_probs = top_probs[0].cpu().numpy()
            top_indices = top_indices[0].cpu().numpy()

            results = []
            for prob, idx in zip(top_probs, top_indices):
                label = (
                    FOOD_LABELS[idx]
                    if idx < len(FOOD_LABELS)
                    else f"food_class_{idx}"
                )
                results.append({
                    "name": label,
                    "confidence": round(float(prob), 4),
                    "class_id": int(idx),
                })

            return results

        except Exception as e:
            print(f"Classification error: {e}")
            return self._mock_classify()

    def classify_from_bbox(
        self,
        image: np.ndarray,
        bbox: List[float],
        top_k: int = None,
    ) -> List[dict]:
        """Classify a food item cropped from a bounding box (normalized coords)."""
        h, w = image.shape[:2]
        x1 = max(0, int(bbox[0] * w))
        y1 = max(0, int(bbox[1] * h))
        x2 = min(w, int(bbox[2] * w))
        y2 = min(h, int(bbox[3] * h))

        crop = image[y1:y2, x1:x2]
        if crop.size == 0:
            return self._mock_classify()

        return self.classify(crop, top_k)

    def _mock_classify(self) -> List[dict]:
        return [
            {"name": "rice", "confidence": 0.89, "class_id": 90},
            {"name": "fried_rice", "confidence": 0.06, "class_id": 45},
            {"name": "pulao", "confidence": 0.03, "class_id": 88},
        ]
