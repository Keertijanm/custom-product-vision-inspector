from __future__ import annotations

import argparse
import base64
import mimetypes
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models import ProductConfiguration
from app.services.yolo_inspection_service import YoloInspectionService

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WEIGHTS = (
    REPOSITORY_ROOT
    / "backend"
    / "models"
    / "label-detector"
    / "yolov8-label-regions-grouped"
    / "weights"
    / "best.pt"
)
DEFAULT_IMAGES = REPOSITORY_ROOT / "krough" / "labels.v6i.yolov8" / "valid" / "images"


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test OCR on local label images.")
    parser.add_argument("--weights", type=Path, default=DEFAULT_WEIGHTS)
    parser.add_argument("--images", type=Path, default=DEFAULT_IMAGES)
    parser.add_argument("--languages", nargs="+", default=["en"])
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()
    if not args.weights.is_file():
        parser.error(f"Detector weights not found: {args.weights}")
    if not args.images.is_dir() or args.limit < 1:
        parser.error("--images must be a directory and --limit must be positive.")

    image_paths = sorted(
        path
        for path in args.images.iterdir()
        if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    )[: args.limit]
    if not image_paths:
        parser.error(f"No supported images found in {args.images}.")

    service = YoloInspectionService(str(args.weights), ocr_languages=args.languages)
    for image_path in image_paths:
        mime_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
        encoded_image = base64.b64encode(image_path.read_bytes()).decode("ascii")
        product = ProductConfiguration(
            name=image_path.stem,
            category="label-ocr-smoke-test",
            image_url=f"data:{mime_type};base64,{encoded_image}",
        )
        result = service.run(product)
        print(image_path.name)
        for detection in result.detections:
            text = " | ".join(
                f"{item.text} ({item.confidence:.2f})" for item in detection.recognized_text
            ) or "<no text recognized>"
            print(f"  label confidence={detection.confidence:.3f}; OCR={text}")
            if detection.data_completion is not None:
                completion = detection.data_completion
                print(f"  data status={completion.status}; catalog={completion.catalog_match}")
                for field in completion.fields:
                    review = "; review required" if field.requires_review else ""
                    print(
                        f"    {field.field}={field.value} "
                        f"(source={field.source}, confidence={field.confidence:.2f}{review})"
                    )
                if completion.missing_fields:
                    print(f"    missing={', '.join(completion.missing_fields)}")
                if completion.conflicts:
                    print(f"    conflicts={', '.join(completion.conflicts)}")


if __name__ == "__main__":
    main()