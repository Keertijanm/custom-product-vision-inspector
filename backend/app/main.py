from __future__ import annotations

import os
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import ProductConfiguration
from app.services.mock_inspection_service import MockInspectionService

if TYPE_CHECKING:
    from app.services.yolo_inspection_service import YoloInspectionService

app = FastAPI(title="Custom Product Vision Inspector API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_inspection_service() -> MockInspectionService | YoloInspectionService:
    engine = os.getenv("INSPECTION_ENGINE", "mock").lower()
    if engine == "mock":
        return MockInspectionService()
    if engine == "yolo":
        from app.services.yolo_inspection_service import YoloInspectionService

        model_path = os.getenv("YOLO_MODEL_PATH")
        if not model_path:
            raise RuntimeError("YOLO_MODEL_PATH must be set when INSPECTION_ENGINE=yolo.")
        try:
            confidence_threshold = float(os.getenv("YOLO_CONFIDENCE_THRESHOLD", "0.25"))
        except ValueError as error:
            raise RuntimeError("YOLO_CONFIDENCE_THRESHOLD must be a number between 0 and 1.") from error
        if not 0 <= confidence_threshold <= 1:
            raise RuntimeError("YOLO_CONFIDENCE_THRESHOLD must be a number between 0 and 1.")
        ocr_languages = [
            language.strip()
            for language in os.getenv("YOLO_OCR_LANGUAGES", "").split(",")
            if language.strip()
        ]
        catalog_path = os.getenv("PRODUCT_CATALOG_PATH")
        return YoloInspectionService(model_path, confidence_threshold, ocr_languages or None, catalog_path)
    raise RuntimeError("INSPECTION_ENGINE must be either 'mock' or 'yolo'.")


inspection_service = create_inspection_service()


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "custom-product-vision-inspector"}


@app.post("/api/inspection")
def run_inspection(product: ProductConfiguration):
    try:
        return inspection_service.run(product).model_dump()
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
