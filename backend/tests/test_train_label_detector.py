import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from scripts.train_label_detector import extract_dataset


def create_dataset_archive(path: Path) -> None:
    with ZipFile(path, "w") as archive:
        archive.writestr("data.yaml", "names: ['label-a', 'label-b']\nnc: 2\n")
        for split in ("train", "valid", "test"):
            archive.writestr(f"{split}/images/example.jpg", b"image")
            class_id = 0 if split == "train" else 1
            archive.writestr(f"{split}/labels/example.txt", f"{class_id} 0.5 0.5 0.2 0.2\n")


def test_extract_dataset_writes_local_yolo_paths_and_class_metadata(tmp_path: Path) -> None:
    archive_path = tmp_path / "dataset.zip"
    create_dataset_archive(archive_path)

    data_yaml = extract_dataset(archive_path, tmp_path / "extracted")
    config = json.loads(data_yaml.read_text(encoding="utf-8"))

    assert config["train"] == str(tmp_path / "extracted" / "train" / "images")
    assert config["val"] == str(tmp_path / "extracted" / "valid" / "images")
    assert config["test"] == str(tmp_path / "extracted" / "test" / "images")
    assert config["nc"] == 2
    assert config["names"] == ["label-a", "label-b"]
    assert (tmp_path / "extracted" / "valid" / "labels" / "example.txt").read_text() == "1 0.5 0.5 0.2 0.2\n"


def test_extract_dataset_can_remap_all_classes_to_label_regions(tmp_path: Path) -> None:
    archive_path = tmp_path / "dataset.zip"
    create_dataset_archive(archive_path)

    data_yaml = extract_dataset(archive_path, tmp_path / "single-class", single_class=True)
    config = json.loads(data_yaml.read_text(encoding="utf-8"))

    assert config["nc"] == 1
    assert config["names"] == ["label"]
    for split in ("train", "valid", "test"):
        annotation = (tmp_path / "single-class" / split / "labels" / "example.txt").read_text(encoding="utf-8")
        assert annotation == "0 0.5 0.5 0.2 0.2\n"


def test_extract_dataset_keeps_capture_bursts_in_one_split(tmp_path: Path) -> None:
    archive_path = tmp_path / "capture-groups.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("data.yaml", "names: ['label-a', 'label-b']\nnc: 2\n")
        original_splits = ("train", "valid", "test")
        for burst_index in range(6):
            for frame_index in range(2):
                split = original_splits[(burst_index + frame_index) % len(original_splits)]
                timestamp = f"12_00_{burst_index * 10:02d}_{frame_index * 200:03d}"
                image_name = f"C03_19_06_2022_{timestamp}_png.jpg"
                archive.writestr(f"{split}/images/{image_name}", b"image")
                archive.writestr(
                    f"{split}/labels/{Path(image_name).stem}.txt",
                    f"{burst_index % 2} 0.5 0.5 0.2 0.2\n",
                )

    data_yaml = extract_dataset(
        archive_path,
        tmp_path / "grouped",
        single_class=True,
        group_captures=True,
    )
    config = json.loads(data_yaml.read_text(encoding="utf-8"))
    group_splits = {}
    for split, images_path in (("train", config["train"]), ("valid", config["val"]), ("test", config["test"])):
        for image_path in Path(images_path).glob("*.jpg"):
            capture_second = image_path.name.split("_")[-3]
            group_splits.setdefault(capture_second, set()).add(split)
            annotation = (image_path.parents[1] / "labels" / f"{image_path.stem}.txt").read_text(encoding="utf-8")
            assert annotation.split()[0] == "0"

    assert len(group_splits) == 6
    assert all(len(splits) == 1 for splits in group_splits.values())


def test_extract_dataset_rejects_archive_path_traversal(tmp_path: Path) -> None:
    archive_path = tmp_path / "unsafe.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("../outside.txt", "not safe")

    with pytest.raises(ValueError, match="Unsafe path"):
        extract_dataset(archive_path, tmp_path / "extracted")
    assert not (tmp_path / "outside.txt").exists()
