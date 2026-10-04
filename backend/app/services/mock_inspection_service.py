from __future__ import annotations

import re
from datetime import datetime, timezone

from app.models import CheckResult, DetectionItem, InspectionResult, ProductConfiguration


class MockInspectionService:
    """Mock AI service used during Phase 1 to simulate inspection results."""

    @staticmethod
    def _normalize_tokens(value: str) -> set[str]:
        return {token for token in re.sub(r"[^a-z0-9]+", " ", value.lower()).split() if token}

    @staticmethod
    def _requirement_satisfied(requirement_name: str, detections: list[DetectionItem]) -> bool:
        tokens = MockInspectionService._normalize_tokens(requirement_name)
        detection_labels = {label.lower() for label in (detection.label for detection in detections)}

        if "product" in tokens and "detected" in tokens:
            return "product-body" in detection_labels or "product" in detection_labels
        if "label" in tokens:
            return "label" in detection_labels
        if "cap" in tokens:
            return "cap" in detection_labels
        if "logo" in tokens:
            return "logo" in detection_labels
        if "damage" in tokens or "defect" in tokens:
            return "damage" not in detection_labels and "defect" not in detection_labels
        if "sticker" in tokens:
            return "sticker" in detection_labels
        if "decal" in tokens:
            return "decal" in detection_labels

        return False

    def run(self, product: ProductConfiguration) -> InspectionResult:
        detections = [
            DetectionItem(
                id="det-1",
                label="product-body",
                confidence=0.96,
                category="object",
            ),
            DetectionItem(
                id="det-2",
                label="label",
                confidence=0.91,
                category="label",
            ),
            DetectionItem(
                id="det-3",
                label="cap",
                confidence=0.89,
                category="packaging",
            ),
            DetectionItem(
                id="det-4",
                label="logo",
                confidence=0.87,
                category="region",
            ),
        ]

        checks: list[CheckResult] = []
        required_failed = False

        for requirement in product.requirements:
            passed = self._requirement_satisfied(requirement.name, detections)
            if requirement.required and not passed:
                required_failed = True

            checks.append(
                CheckResult(
                    id=requirement.id,
                    name=requirement.name,
                    passed=passed,
                    explanation=(
                        "Requirement satisfied by simulated product features and packaging markers."
                        if passed
                        else "The required element was not clearly visible in the simulated inspection output."
                    ),
                    confidence=0.9 if passed else 0.68,
                )
            )

        overall_passed = not required_failed
        summary = (
            "Simulated inspection passed: all required checks were satisfied in the mock validation run."
            if overall_passed
            else "Simulated inspection failed: one or more required checks were not satisfied in the mock validation run."
        )

        return InspectionResult(
            product_name=product.name,
            category=product.category,
            inspection_mode="mock",
            passed=overall_passed,
            overall_confidence=sum(check.confidence for check in checks) / max(len(checks), 1),
            summary=summary,
            detections=detections,
            checks=checks,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
