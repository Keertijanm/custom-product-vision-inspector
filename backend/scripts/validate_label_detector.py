from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from train_label_detector import DEFAULT_ARCHIVE, REPOSITORY_ROOT, extract_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a trained vial-label detector.")
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--split", choices=("valid", "test"), default="valid")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--single-class", action="store_true")
    parser.add_argument("--group-captures", action="store_true")
    args = parser.parse_args()
    if not args.weights.is_file():
        parser.error(f"Model weights not found: {args.weights}")

    from ultralytics import YOLO

    with tempfile.TemporaryDirectory(prefix="product-vision-validation-") as temporary_directory:
        data_yaml = extract_dataset(
            DEFAULT_ARCHIVE,
            Path(temporary_directory),
            single_class=args.single_class,
            group_captures=args.group_captures,
        )
        metrics = YOLO(str(args.weights)).val(
            data=str(data_yaml),
            split="val" if args.split == "valid" else "test",
            imgsz=args.imgsz,
            device=args.device,
            plots=True,
            project=str(REPOSITORY_ROOT / "runs" / "label-detector-evaluation"),
            name=f"{args.weights.parent.parent.name}-{args.split}",
            exist_ok=True,
        )
        print("Evaluation metrics:", metrics.results_dict)
        print("Per-class mAP:", metrics.box.maps)
        print("Evaluation artifacts:", metrics.save_dir)


if __name__ == "__main__":
    main()