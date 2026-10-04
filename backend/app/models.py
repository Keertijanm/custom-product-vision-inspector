from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class InspectionRequirement(BaseModel):
    id: str
    name: str
    description: str
    required: bool = True
    severity: Literal["critical", "warning"] = "critical"


class ProductConfiguration(BaseModel):
    name: str
    category: str
    image_url: str | None = None
    requirements: list[InspectionRequirement] = Field(default_factory=list)


class DetectionItem(BaseModel):
    id: str
    label: str
    confidence: float
    category: Literal["object", "region", "packaging", "defect", "label"]
    bounding_box: tuple[float, float, float, float] | None = None


class CheckResult(BaseModel):
    id: str
    name: str
    passed: bool
    explanation: str
    confidence: float


class InspectionResult(BaseModel):
    product_name: str
    category: str
    inspection_mode: Literal["mock", "yolo"]
    passed: bool
    overall_confidence: float
    summary: str
    detections: list[DetectionItem] = Field(default_factory=list)
    checks: list[CheckResult] = Field(default_factory=list)
    generated_at: str
