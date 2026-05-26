"""
Groq Vision – food detection and portion estimation via Llama 4 Scout.
Uses Groq's OpenAI-compatible API for ultra-fast inference.
"""
import base64
import json
import os
import re
from io import BytesIO
from typing import Any, Dict, List

from openai import AsyncOpenAI
from PIL import Image

_client: AsyncOpenAI = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=os.environ["GROQ_API_KEY"],
            base_url="https://api.groq.com/openai/v1",
        )
    return _client


def _encode_image(image: Image.Image) -> str:
    buf = BytesIO()
    image.save(buf, format="JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode()


_SYSTEM_PROMPT = """\
You are a food recognition and nutrition expert. Analyze the food image and return a JSON object.

Rules:
- Identify every distinct food item visible.
- Use clear English names (e.g. "french toast", "butter", "maple syrup").
- Estimate realistic portion weight in grams based on visual cues (plate size, typical serving).
- Confidence should reflect how certain you are (0.0–1.0).
- bbox should be normalized [x1, y1, x2, y2] coordinates (0.0–1.0) of where the item appears.
- Return ONLY valid JSON, no markdown, no explanation.

Response format:
{
  "items": [
    {
      "name": "french toast",
      "confidence": 0.97,
      "portion_g": 180,
      "portion_description": "2 slices",
      "bbox": [0.1, 0.05, 0.9, 0.95]
    }
  ]
}
"""


async def analyze_image(image: Image.Image, max_items: int = 10) -> List[Dict[str, Any]]:
    """
    Send image to Groq Llama 4 Scout and return structured food item list.
    Each item: name, confidence, portion_g, portion_description, bbox
    """
    model = os.environ.get("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
    b64 = _encode_image(image)

    response = await get_client().chat.completions.create(
        model=model,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    },
                    {
                        "type": "text",
                        "text": f"Identify all food items (max {max_items}). Return JSON only.",
                    },
                ],
            },
        ],
        temperature=0.1,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        data = json.loads(raw)
        items = data.get("items", [])
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            items = json.loads(match.group()).get("items", [])
        else:
            items = []

    result = []
    for item in items[:max_items]:
        name = str(item.get("name", "unknown food")).strip().lower().replace(" ", "_")
        bbox = item.get("bbox", [0.0, 0.0, 1.0, 1.0])
        if len(bbox) != 4:
            bbox = [0.0, 0.0, 1.0, 1.0]
        bbox = [max(0.0, min(1.0, float(v))) for v in bbox]

        result.append({
            "name": name,
            "confidence": round(float(item.get("confidence", 0.9)), 4),
            "portion_g": max(1, int(item.get("portion_g", 100))),
            "portion_description": str(item.get("portion_description", "")),
            "bbox": bbox,
        })

    return result
