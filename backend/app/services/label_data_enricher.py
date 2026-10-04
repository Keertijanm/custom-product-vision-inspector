from __future__ import annotations

import json
import re
from pathlib import Path

from app.models import DataCompletion, ProductFieldSuggestion, RecognizedText

_STRENGTH = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:mcg|ug|mg|g)"
    r"(?:\s*/\s*(?:\d+(?:[.,]\d+)?\s*)?(?:ml|l))?\b",
    re.IGNORECASE,
)
_VOLUME = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:ml|l)\b", re.IGNORECASE)
_LOT = re.compile(r"\b(?:lot|batch)\s*(?:no\.?|#|:|-)?\s*([a-z0-9][a-z0-9-]{2,})\b", re.IGNORECASE)
_EXPIRY = re.compile(
    r"\b(?:exp(?:iry)?|use\s+by)\s*[:#-]?\s*"
    r"((?:0?[1-9]|1[0-2])[/.-](?:\d{2}|\d{4})|\d{4}-\d{2})\b",
    re.IGNORECASE,
)
_REQUIRED_FIELDS = ("product_name", "sku", "strength")


def _normalize(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


class LabelDataEnricher:
    """Extract visible facts and suggest catalog values without inventing identity."""

    def __init__(self, catalog: list[dict[str, object]] | None = None) -> None:
        self.catalog = catalog or []

    @classmethod
    def from_json_file(cls, catalog_path: str | Path) -> LabelDataEnricher:
        path = Path(catalog_path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(f"Could not load product catalog at {path}: {error}") from error
        entries = data.get("products") if isinstance(data, dict) else data
        if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
            raise RuntimeError("The product catalog must be a JSON array or an object with a products array.")
        return cls(entries)

    @staticmethod
    def _observed_fields(recognized_text: list[RecognizedText]) -> list[ProductFieldSuggestion]:
        fields: dict[str, ProductFieldSuggestion] = {}
        patterns = (
            ("strength", _STRENGTH),
            ("volume", _VOLUME),
            ("lot", _LOT),
            ("expiry", _EXPIRY),
        )
        for item in recognized_text:
            if not item.text.strip():
                continue
            for field, pattern in patterns:
                match = pattern.search(item.text)
                if match is None:
                    continue
                value = match.group(1) if field in {"lot", "expiry"} else match.group(0)
                previous = fields.get(field)
                if previous is None or item.confidence > previous.confidence:
                    fields[field] = ProductFieldSuggestion(
                        field=field,
                        value=value.strip(),
                        confidence=item.confidence,
                        source="ocr",
                        requires_review=item.confidence < 0.8,
                    )
        return list(fields.values())

    def _catalog_match(self, recognized_text: list[RecognizedText]) -> tuple[str, dict[str, object] | None, float]:
        if not self.catalog:
            return "unavailable", None, 0.0

        normalized_text = _normalize(" ".join(item.text for item in recognized_text if item.confidence >= 0.35))
        if not normalized_text:
            return "none", None, 0.0

        matches: list[tuple[dict[str, object], float]] = []
        for entry in self.catalog:
            aliases = [entry.get("product_name")]
            entry_aliases = entry.get("aliases", [])
            if isinstance(entry_aliases, list):
                aliases.extend(entry_aliases)
            aliases.append(entry.get("sku"))
            alias_confidences = [
                item.confidence
                for item in recognized_text
                if item.confidence >= 0.35
                and any(
                    isinstance(alias, str)
                    and len(_normalize(alias)) >= 5
                    and _normalize(alias) in _normalize(item.text)
                    for alias in aliases
                )
            ]
            if alias_confidences:
                matches.append((entry, max(alias_confidences)))
        if len(matches) == 1:
            entry, confidence = matches[0]
            return "matched", entry, confidence
        return ("ambiguous" if matches else "none"), None, 0.0

    def enrich(self, recognized_text: list[RecognizedText]) -> DataCompletion:
        fields = self._observed_fields(recognized_text)
        field_values = {field.field: field.value for field in fields}
        catalog_match, entry, catalog_confidence = self._catalog_match(recognized_text)
        conflicts = []

        if entry is not None:
            for field, raw_value in entry.items():
                if field in {"aliases", "sku", "product_name"} or not isinstance(raw_value, str) or not raw_value.strip():
                    continue
                if field in field_values:
                    if _normalize(field_values[field]) != _normalize(raw_value):
                        conflicts.append(field)
                    continue
                fields.append(
                    ProductFieldSuggestion(
                        field=field,
                        value=raw_value.strip(),
                        confidence=catalog_confidence,
                        source="catalog",
                        requires_review=True,
                    )
                )

            for field in ("product_name", "sku"):
                raw_value = entry.get(field)
                if isinstance(raw_value, str) and raw_value.strip():
                    fields.append(
                        ProductFieldSuggestion(
                            field=field,
                            value=raw_value.strip(),
                            confidence=catalog_confidence,
                            source="catalog",
                            requires_review=True,
                        )
                    )
                    field_values[field] = raw_value.strip()

        present_fields = {field.field for field in fields}
        missing_fields = [field for field in _REQUIRED_FIELDS if field not in present_fields]
        if conflicts or any(field.source == "catalog" for field in fields):
            status = "review"
        elif missing_fields:
            status = "incomplete"
        else:
            status = "complete"
        return DataCompletion(
            status=status,
            catalog_match=catalog_match,
            fields=fields,
            missing_fields=missing_fields,
            conflicts=sorted(set(conflicts)),
        )