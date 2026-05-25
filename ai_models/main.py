"""
NutriMind AI Models Service – FastAPI entry point.
Hosts the full inference pipeline: YOLOv8 → SAM2 → EfficientNetV2 → MiDaS
"""
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from inference.pipeline import InferencePipeline

logger = structlog.get_logger()
pipeline: InferencePipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline
    logger.info("🤖 Loading AI models...")
    pipeline = InferencePipeline()
    await pipeline.load_models()
    logger.info("✅ All models loaded and ready")
    yield
    logger.info("👋 AI models service shutting down")


app = FastAPI(
    title="NutriMind AI Service",
    description="Computer vision inference pipeline for food detection and nutrition analysis",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    image_url: str
    confidence_threshold: float = 0.45
    max_detections: int = 10


class AnalyzeResponse(BaseModel):
    detected_items: list
    detection_count: int
    processing_time_ms: float
    model_versions: dict


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "models_loaded": pipeline is not None and pipeline.models_loaded,
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_food_image(request: AnalyzeRequest):
    """
    Full food image analysis pipeline:
    1. YOLOv8 – detect food items
    2. SAM2 – segment each detected item
    3. EfficientNetV2 – classify each segment
    4. MiDaS – estimate depth/volume for portion size
    """
    if not pipeline or not pipeline.models_loaded:
        raise HTTPException(status_code=503, detail="Models not loaded yet")

    result = await pipeline.analyze(
        image_url=request.image_url,
        confidence_threshold=request.confidence_threshold,
        max_detections=request.max_detections,
    )
    return result


@app.post("/detect")
async def detect_only(request: AnalyzeRequest):
    """YOLOv8 detection only (fast, no classification)."""
    if not pipeline:
        raise HTTPException(status_code=503, detail="Models not loaded")
    return await pipeline.detect_only(request.image_url, request.confidence_threshold)


@app.post("/classify")
async def classify_only(image_url: str):
    """EfficientNetV2 classification only."""
    if not pipeline:
        raise HTTPException(status_code=503, detail="Models not loaded")
    return await pipeline.classify_only(image_url)
