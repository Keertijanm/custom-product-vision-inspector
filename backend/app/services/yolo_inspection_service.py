from __future__ import annotations

import base64
import binascii
import re
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from statistics import mean
from typing import TYPE_CHECKING

from app.models import CheckResult, DetectionItem, InspectionResult, ProductConfiguration, RecognizedText
from app.services.label_data_enricher import LabelDataEnricher

if TYPE_CHECKING:
    from PIL import Image

_IMAGE_DATA_URL = re.compile(r"^data:image/[a-zA-Z0-9.+-]+;base64,(.+)$", re.DOTALL)
_MAX_IMAGE_BYTES = 15 * 1024 * 1024


class YoloInspectionService:
    """Runs a configured YOLO model and validates only label-related requirements."""

    def __init__(
        self,
        model_path: str,
        confidence_threshold: float = 0.25,
        ocr_languages: list[str] | None = None,
        catalog_path: str | None = None,
    ) -> None:
        if not 0 <= confidence_threshold <= 1:
            raise ValueError("Confidence threshold must be between 0 and 1.")
        weights = Path(model_path)
        if not weights.is_file():
            raise FileNotFoundError(f"YOLO model weights were not found: {weights}")

        try:
            from ultralytics import YOLO
        except ImportError as error:
            raise RuntimeError(
                "YOLO inspection requires the optional vision dependencies. "
                "Install them with `pip install -r requirements-vision.txt`."
            ) from error

        self.model = YOLO(str(weights))
        self.confidence_threshold = confidence_threshold
        self.ocr_reader = None
        self.data_enricher = (
            LabelDataEnricher.from_json_file(catalog_path)
            if catalog_path
            else LabelDataEnricher()
        )
        if ocr_languages:
            try:
                import easyocr
            except ImportError as error:
                raise RuntimeError(
                    "Label OCR requires EasyOCR. Install it with `pip install -r requirements-vision.txt`."
                ) from error
            self.ocr_reader = easyocr.Reader(ocr_languages, gpu=False)

    def _read_label_text(self, image: Image.Image, coordinates: list[float]) -> list[RecognizedText]:
        reader = getattr(self, "ocr_reader", None)
        if reader is None:
            return []

        import numpy as np

        width, height = image.size
        x1, y1, x2, y2 = coordinates
        left = max(0, min(width, int(x1)))
        top = max(0, min(height, int(y1)))
        right = max(left, min(width, int(x2)))
        bottom = max(top, min(height, int(y2)))
        if left == right or top == bottom:
            return []

        crop = image.crop((left, top, right, bottom))
        results = reader.readtext(np.asarray(crop), detail=1, paragraph=False, mag_ratio=2.0)
        return [
            RecognizedText(text=text.strip(), confidence=float(confidence))
            for _, text, confidence in results
            if text.strip()
        ]

    @staticmethod
    def _decode_image(image_url: str | None) -> Image.Image:
        if not image_url:
            raise ValueError("A product image is required for YOLO inspection.")
        match = _IMAGE_DATA_URL.fullmatch(image_url)
        if match is None:
            raise ValueError("YOLO inspection accepts uploaded images as base64 data URLs only.")

        encoded_image = match.group(1)
        if len(encoded_image) > ((_MAX_IMAGE_BYTES + 2) // 3) * 4:
            raise ValueError("The uploaded image must be 15 MB or smaller.")
        try:
            image_bytes = base64.b64decode(encoded_image, validate=True)
        except (binascii.Error, ValueError) as error:
            raise ValueError("The uploaded image data is not valid base64.") from error
        if len(image_bytes) > _MAX_IMAGE_BYTES:
            raise ValueError("The uploaded image must be 15 MB or smaller.")

        from PIL import Image, ImageOps, UnidentifiedImageError

        try:
            with Image.open(BytesIO(image_bytes)) as image:
                image.verify()
            with Image.open(BytesIO(image_bytes)) as image:
                return ImageOps.exif_transpose(image).convert("RGB")
        except (Image.DecompressionBombError, UnidentifiedImageError, OSError) as error:
            raise ValueError("The uploaded data URL does not contain a valid image.") from error

    def _detect(self, image: Image.Image) -> list[DetectionItem]:
        result = self.model.predict(image, conf=self.confidence_threshold, verbose=False)[0]
        width, height = image.size
        names = result.names
        detections: list[DetectionItem] = []

        if result.boxes is None:
            return detections

        for index, (class_id, confidence, coordinates) in enumerate(
            zip(result.boxes.cls.tolist(), result.boxes.conf.tolist(), result.boxes.xyxy.tolist())
        ):
            class_index = int(class_id)
            label = names[class_index] if isinstance(names, (list, tuple)) else names[class_index]
            x1, y1, x2, y2 = coordinates
            recognized_text = self._read_label_text(image, coordinates)
            detections.append(
                DetectionItem(
                    id=f"det-{index + 1}",
                    label=str(label),
                    confidence=float(confidence),
                    category="label",
                    bounding_box=(
                        max(0.0, min(1.0, x1 / width)),
                        max(0.0, min(1.0, y1 / height)),
                        max(0.0, min(1.0, x2 / width)),
                        max(0.0, min(1.0, y2 / height)),
                    ),
                    recognized_text=recognized_text,
                    data_completion=(
                        self.data_enricher.enrich(recognized_text)
                        if self.ocr_reader is not None
                        else None
                    ),
                )
            )
        return detections

    @staticmethod
    def _check_requirement(requirement_name: str, detections: list[DetectionItem]) -> tuple[bool, float, str]:
        tokens = set(re.findall(r"[a-z0-9]+", requirement_name.lower()))
        class_tokens = {token for token in tokens if token.isdigit()}
        if class_tokens:
            matched = [detection for detection in detections if detection.label.lower() in class_tokens]
        elif "label" in tokens:
            matched = detections
        else:
            matched = [detection for detection in detections if detection.label.lower() in tokens]

        if matched:
            confidence = max(detection.confidence for detection in matched)
            explanation = (
                "The configured YOLO label detector found a matching label region."
                if "label" in tokens
                else "The configured YOLO label detector found the requested label class."
            )
            return True, confidence, explanation

        if "label" in tokens or class_tokens:
            return False, 0.0, "No matching label region was detected by the configured YOLO model."
        return (
            False,
            0.0,
            "This label-only model cannot verify this requirement; use a suitable model for this check.",
        )

    def run(self, product: ProductConfiguration) -> InspectionResult:
        image = self._decode_image(product.image_url)
        detections = self._detect(image)
        checks: list[CheckResult] = []
        required_failed = False

        for requirement in product.requirements:
            passed, confidence, explanation = self._check_requirement(requirement.name, detections)
            if requirement.required and not passed:
                required_failed = True
            checks.append(
                CheckResult(
                    id=requirement.id,
                    name=requirement.name,
                    passed=passed,
                    explanation=explanation,
                    confidence=confidence,
                )
            )

        overall_confidence = mean(check.confidence for check in checks) if checks else (
            mean(detection.confidence for detection in detections) if detections else 0.0
        )
        summary = (
            f"YOLO label inspection passed with {len(detections)} label region(s) detected."
            if not required_failed
            else (
                f"YOLO label inspection failed: one or more required checks were not verified. "
                f"{len(detections)} label region(s) detected."
            )
        )
        return InspectionResult(
            product_name=product.name,
            category=product.category,
            inspection_mode="yolo",
            passed=not required_failed,
            overall_confidence=overall_confidence,
            summary=summary,
            detections=detections,
            checks=checks,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
