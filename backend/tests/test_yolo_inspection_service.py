import base64
import io
import struct
import zlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.models import InspectionRequirement, ProductConfiguration
from app.services.yolo_inspection_service import YoloInspectionService


class FakeTensor:
    def __init__(self, values: list) -> None:
        self.values = values

    def tolist(self) -> list:
        return self.values


class FakeModel:
    def __init__(self, names: dict[int, str], boxes: SimpleNamespace | None) -> None:
        self.names = names
        self.boxes = boxes

    def predict(self, image, conf: float, verbose: bool) -> list[SimpleNamespace]:
        assert image.size == (100, 80)
        assert conf == 0.25
        assert verbose is False
        return [SimpleNamespace(names=self.names, boxes=self.boxes)]


def make_service(tmp_path: Path, boxes: SimpleNamespace | None) -> YoloInspectionService:
    weights = tmp_path / "weights.pt"
    weights.touch()
    service = object.__new__(YoloInspectionService)
    service.model = FakeModel({0: "1001"}, boxes)
    service.confidence_threshold = 0.25
    return service


def make_product(image_url: str | None, *requirements: InspectionRequirement) -> ProductConfiguration:
    return ProductConfiguration(
        name="Vial",
        category="Pharmaceutical",
        image_url=image_url,
        requirements=list(requirements),
    )


def image_data_url() -> str:
    buffer = io.BytesIO()
    buffer.write(b"\x89PNG\r\n\x1a\n")

    def write_chunk(chunk_type: bytes, content: bytes) -> None:
        buffer.write(struct.pack(">I", len(content)))
        buffer.write(chunk_type + content)
        buffer.write(struct.pack(">I", zlib.crc32(chunk_type + content) & 0xFFFFFFFF))

    write_chunk(b"IHDR", struct.pack(">2I5B", 100, 80, 8, 2, 0, 0, 0))
    scanline = b"\x00" + b"\xff\xff\xff" * 100
    write_chunk(b"IDAT", zlib.compress(scanline * 80))
    write_chunk(b"IEND", b"")
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"


def test_yolo_inspection_returns_label_boxes_and_only_passes_supported_checks(tmp_path: Path) -> None:
    boxes = SimpleNamespace(
        cls=FakeTensor([0]),
        conf=FakeTensor([0.92]),
        xyxy=FakeTensor([[10, 8, 60, 48]]),
    )
    service = make_service(tmp_path, boxes)
    product = make_product(
        image_data_url(),
        InspectionRequirement(id="label", name="Label present", description="A label is visible"),
        InspectionRequirement(id="class", name="1001 label present", description="Expected class is 1001"),
        InspectionRequirement(
            id="other-class",
            name="1002 label present",
            description="Expected class is 1002",
            required=False,
        ),
        InspectionRequirement(id="damage", name="No damage", description="Packaging should not be damaged"),
    )

    result = service.run(product)

    assert result.inspection_mode == "yolo"
    assert result.passed is False
    assert result.detections[0].label == "1001"
    assert result.detections[0].category == "label"
    assert result.detections[0].bounding_box == (0.1, 0.1, 0.6, 0.6)
    assert [check.passed for check in result.checks] == [True, True, False, False]
    assert "No matching label" in result.checks[2].explanation
    assert "cannot verify" in result.checks[3].explanation


def test_yolo_inspection_rejects_non_data_url_images(tmp_path: Path) -> None:
    service = make_service(tmp_path, None)

    with pytest.raises(ValueError, match="base64 data URLs"):
        service.run(make_product("https://example.com/image.png"))


def test_yolo_inspection_rejects_missing_image(tmp_path: Path) -> None:
    service = make_service(tmp_path, None)

    with pytest.raises(ValueError, match="image is required"):
        service.run(make_product(None))
