from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path, PurePosixPath, PureWindowsPath
from zipfile import ZipFile

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARCHIVE = REPOSITORY_ROOT / "kdata" / "labels.v6i.yolov8.zip"
DEFAULT_OUTPUT = REPOSITORY_ROOT / "backend" / "models" / "label-detector"


def extract_dataset(archive_path: Path, destination: Path) -> Path:
    with ZipFile(archive_path) as archive:
        files = [info for info in archive.infolist() if not info.is_dir()]
        if not files:
            raise ValueError("The dataset archive contains no files.")
        for info in files:
            normalized_name = info.filename.replace("\\", "/")
            posix_path = PurePosixPath(normalized_name)
            windows_path = PureWindowsPath(info.filename)
            if (
                posix_path.is_absolute()
                or ".." in posix_path.parts
                or windows_path.is_absolute()
                or windows_path.drive
                or ".." in windows_path.parts
            ):
                raise ValueError(f"Unsafe path in dataset archive: {info.filename}")

        archive.extractall(destination, members=files)

    image_root = destination / "train" / "images"
    required_splits = ("train", "valid", "test")
    for split in required_splits:
        if not any((destination / split / "images").glob("*")):
            raise ValueError(f"The dataset archive is missing images for the {split} split.")
        if not any((destination / split / "labels").glob("*.txt")):
            raise ValueError(f"The dataset archive is missing labels for the {split} split.")

    annotation_files = list((destination / "train" / "labels").glob("*.txt"))
    if not annotation_files or not image_root.is_dir():
        raise ValueError("The dataset archive does not have the expected YOLO directory structure.")

    class_names: list[str] | None = None
    for yaml_path in destination.rglob("data.yaml"):
        import yaml

        dataset_metadata = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        names = dataset_metadata.get("names") if isinstance(dataset_metadata, dict) else None
        if isinstance(names, list) and names:
            class_names = [str(name) for name in names]
            break
    if class_names is None:
        raise ValueError("The dataset archive does not contain a data.yaml with class names.")

    dataset_yaml = destination / "training-data.yaml"
    dataset_yaml.write_text(
        json.dumps(
            {
                "train": str(destination / "train" / "images"),
                "val": str(destination / "valid" / "images"),
                "test": str(destination / "test" / "images"),
                "nc": len(class_names),
                "names": class_names,
            }
        ),
        encoding="utf-8",
    )
    return dataset_yaml


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune YOLOv8 on the supplied vial-label dataset.")
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--base-model", default="yolov8n.pt")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", help="Optional Ultralytics device, for example cpu or 0.")
    args = parser.parse_args()

    if args.epochs < 1 or args.imgsz < 1:
        parser.error("--epochs and --imgsz must be positive integers.")
    if not args.archive.is_file():
        parser.error(f"Dataset archive not found: {args.archive}")

    try:
        from ultralytics import YOLO
    except ImportError as error:
        raise SystemExit("Install vision dependencies first: pip install -r requirements-vision.txt") from error

    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="product-vision-dataset-") as temporary_directory:
        dataset_root = Path(temporary_directory)
        data_yaml = extract_dataset(args.archive, dataset_root)
        model = YOLO(args.base_model)
        training_options = {
            "data": str(data_yaml),
            "epochs": args.epochs,
            "imgsz": args.imgsz,
            "project": str(args.output),
            "name": "yolov8-labels",
            "exist_ok": True,
        }
        if args.device:
            training_options["device"] = args.device
        model.train(**training_options)
        best_weights = Path(model.trainer.save_dir) / "weights" / "best.pt"
        print(f"Training complete. Set YOLO_MODEL_PATH={best_weights.resolve()}")
        print("Review validation metrics before relying on predictions in production.")


if __name__ == "__main__":
    main()
