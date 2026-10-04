import json
from pathlib import Path

import pytest

from app.models import RecognizedText
from app.services.label_data_enricher import LabelDataEnricher


def test_enricher_extracts_observed_strength_lot_and_expiry_without_identity() -> None:
    enricher = LabelDataEnricher()

    result = enricher.enrich(
        [
            RecognizedText(text="20 mg/ml concentrate for solution", confidence=0.91),
            RecognizedText(text="LOT: AB123 EXP 11/2026", confidence=0.88),
        ]
    )

    values = {field.field: field.value for field in result.fields}
    assert values == {"strength": "20 mg/ml", "lot": "AB123", "expiry": "11/2026"}
    assert result.catalog_match == "unavailable"
    assert result.missing_fields == ["product_name", "sku"]
    assert result.status == "incomplete"


def test_enricher_suggests_catalog_identity_but_requires_review(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(
        json.dumps(
            {
                "products": [
                    {
                        "sku": "SKU-001",
                        "product_name": "Example Medicine",
                        "aliases": ["ExampleMed"],
                        "strength": "20 mg/ml",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    enricher = LabelDataEnricher.from_json_file(catalog_path)

    result = enricher.enrich(
        [
            RecognizedText(text="Example Medicine 20 mg/ml", confidence=0.93),
            RecognizedText(text="LOT AB123", confidence=0.91),
            RecognizedText(text="unrelated high confidence text", confidence=0.99),
        ]
    )

    values = {field.field: field for field in result.fields}
    assert values["product_name"].value == "Example Medicine"
    assert values["sku"].value == "SKU-001"
    assert values["sku"].source == "catalog"
    assert values["sku"].confidence == 0.93
    assert values["sku"].requires_review is True
    assert values["strength"].source == "ocr"
    assert result.missing_fields == []
    assert result.status == "review"


def test_enricher_does_not_fill_ambiguous_catalog_matches() -> None:
    enricher = LabelDataEnricher(
        [
            {"sku": "SKU-A", "product_name": "Example Medicine", "aliases": ["ExampleMed"]},
            {"sku": "SKU-B", "product_name": "Example Medicine Plus", "aliases": ["ExampleMed"]},
        ]
    )

    result = enricher.enrich([RecognizedText(text="ExampleMed", confidence=0.96)])

    assert result.catalog_match == "ambiguous"
    assert "sku" not in [field.field for field in result.fields]
    assert result.missing_fields == ["product_name", "sku", "strength"]
    assert result.status == "incomplete"


def test_enricher_surfaces_catalog_conflict_without_overwriting_ocr() -> None:
    enricher = LabelDataEnricher(
        [
            {
                "sku": "SKU-001",
                "product_name": "Example Medicine",
                "aliases": ["ExampleMed"],
                "strength": "30 mg/ml",
            }
        ]
    )

    result = enricher.enrich(
        [
            RecognizedText(text="Example Medicine 20 mg/ml", confidence=0.93),
        ]
    )

    strength = next(field for field in result.fields if field.field == "strength")
    assert strength.value == "20 mg/ml"
    assert strength.source == "ocr"
    assert result.conflicts == ["strength"]
    assert result.status == "review"


def test_enricher_rejects_invalid_catalog_shape(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text('{"products": "not-a-list"}', encoding="utf-8")

    with pytest.raises(RuntimeError, match="products array"):
        LabelDataEnricher.from_json_file(catalog_path)