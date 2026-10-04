from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import tempfile
from pathlib import Path, PurePosixPath, PureWindowsPath
from zipfile import ZipFile

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARCHIVE = REPOSITORY_ROOT / "kdata" / "labels.v6i.yolov8.zip"
DEFAULT_OUTPUT = REPOSITORY_ROOT / "backend" / "models" / "label-detector"
_CAPTURE_TIMESTAMP = re.compile(
    r"^(?P<session>.+?)_(?P<hour>\d{2})_(?P<minute>\d{2})_(?P<second>\d{2})_(?P<millisecond>\d{3})_png"
)


def _group_capture_bursts(destination: Path) -> dict[str, Path]:
    frames = []
    for split in ("train", "valid", "test"):
        for image_path in (destination / split / "images").iterdir():
            if not image_path.is_file():
                continue
            match = _CAPTURE_TIMESTAMP.match(image_path.name)
            if match is None:
                raise ValueError(f"Cannot group image without a capture timestamp: {image_path.name}")
            label_path = destination / split / "labels" / f"{image_path.stem}.txt"
            if not label_path.is_file():
                raise ValueError(f"Missing YOLO annotation for image: {image_path.name}")
            timestamp = (
                int(match["hour"]) * 3600
                + int(match["minute"]) * 60
                + int(match["second"])
                + int(match["millisecond"]) / 1000
            )
            frames.append((match["session"], timestamp, image_path, label_path))

    frames.sort(key=lambda frame: (frame[0], frame[1]))
    bursts = []
    for frame in frames:
        if (
            not bursts
            or frame[0] != bursts[-1][-1][0]
            or frame[1] - bursts[-1][-1][1] > 2
        ):
            bursts.append([frame])
        else:
            bursts[-1].append(frame)
    if len(bursts) < 3:
        raise ValueError("At least three timestamped capture bursts are required for grouped splits.")

    split_names = ("train", "valid", "test")
    total_images = len(frames)
    targets = {
        "train": total_images * 0.70,
        "valid": total_images * 0.15,
        "test": total_images * 0.15,
    }
    assigned = {split: 0 for split in split_names}
    random.Random(0).shuffle(bursts)
    bursts.sort(key=len, reverse=True)
    assignments: dict[str, list] = {split: [] for split in split_names}
    for burst in bursts:
        split = min(split_names, key=lambda name: assigned[name] / targets[name])
        assignments[split].append(burst)
        assigned[split] += len(burst)

    grouped_roots = {split: destination / "capture-grouped" / split for split in split_names}
    for split, split_bursts in assignments.items():
        image_directory = grouped_roots[split] / "images"
        label_directory = grouped_roots[split] / "labels"
        image_directory.mkdir(parents=True, exist_ok=True)
        label_directory.mkdir(parents=True, exist_ok=True)
        for burst in split_bursts:
            for _, _, image_path, label_path in burst:
                shutil.copy2(image_path, image_directory / image_path.name)
                shutil.copy2(label_path, label_directory / label_path.name)
    return grouped_roots


def extract_dataset(
    archive_path: Path,
    destination: Path,
    single_class: bool = False,
    group_captures: bool = False,
) -> Path:
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

    split_roots = {split: destination / split for split in required_splits}
    if group_captures:
        split_roots = _group_capture_bursts(destination)

    if single_class:
        for split_root in split_roots.values():
            for label_path in (split_root / "labels").glob("*.txt"):
                remapped_lines = []
                for line_number, line in enumerate(label_path.read_text(encoding="utf-8").splitlines(), start=1):
                    parts = line.split()
                    if not parts:
                        remapped_lines.append(line)
                        continue
                    try:
                        class_id = int(parts[0])
                    except ValueError as error:
                        raise ValueError(f"Invalid class ID in {label_path}:{line_number}.") from error
                    if not 0 <= class_id < len(class_names):
                        raise ValueError(f"Class ID {class_id} is out of range in {label_path}:{line_number}.")
                    parts[0] = "0"
                    remapped_lines.append(" ".join(parts))
                label_path.write_text("\n".join(remapped_lines) + "\n", encoding="utf-8")
        class_names = ["label"]

    dataset_yaml = destination / "training-data.yaml"
    dataset_yaml.write_text(
        json.dumps(
            {
                "train": str(split_roots["train"] / "images"),
                "val": str(split_roots["valid"] / "images"),
                "test": str(split_roots["test"] / "images"),
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
    parser.add_argument(
        "--single-class",
        action="store_true",
        help="Train a label-region detector by remapping every annotated class to label.",
    )
    parser.add_argument(
        "--group-captures",
        action="store_true",
        help="Rebuild dataset splits so timestamped capture bursts stay in one split.",
    )
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
        data_yaml = extract_dataset(
            args.archive,
            dataset_root,
            single_class=args.single_class,
            group_captures=args.group_captures,
        )
        model = YOLO(args.base_model)
        training_options = {
            "data": str(data_yaml),
            "epochs": args.epochs,
            "imgsz": args.imgsz,
            "project": str(args.output),
            "name": (
                "yolov8-label-regions-grouped"
                if args.single_class and args.group_captures
                else "yolov8-label-regions"
                if args.single_class
                else "yolov8-labels"
            ),
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
