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
            archive.writestr(f"{split}/labels/example.txt", "0 0.5 0.5 0.2 0.2\n")


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


def test_extract_dataset_rejects_archive_path_traversal(tmp_path: Path) -> None:
    archive_path = tmp_path / "unsafe.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("../outside.txt", "not safe")

    with pytest.raises(ValueError, match="Unsafe path"):
        extract_dataset(archive_path, tmp_path / "extracted")
    assert not (tmp_path / "outside.txt").exists()
