from __future__ import annotations

from datetime import datetime, timezone

from app.models import CheckResult, DetectionItem, InspectionResult, ProductConfiguration


class MockInspectionService:
    """Mock AI service used during Phase 1 to simulate inspection results."""

    def run(self, product: ProductConfiguration) -> InspectionResult:
        requirement_names = {requirement.name.lower() for requirement in product.requirements}

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
        for requirement in product.requirements:
            name = requirement.name.lower()
            matched = name in requirement_names
            passed = bool(
                requirement.required
                and (
                    ("label" in name and "label" in requirement_names)
                    or ("cap" in name and "cap" in requirement_names)
                    or ("logo" in name and "logo" in requirement_names)
                    or ("damage" in name and "damage" not in requirement_names)
                    or ("correct" in name and "correct" in requirement_names)
                    or ("product" in name)
                )
            )
            if not requirement.required:
                passed = True
            if name == "product detected":
                passed = True
            if name == "packaging damage":
                passed = True

            checks.append(
                CheckResult(
                    id=requirement.id,
                    name=requirement.name,
                    passed=passed,
                    explanation=(
                        "Requirement satisfied by detected product features and packaging markers."
                        if passed
                        else "The required element was not clearly visible in the uploaded image."
                    ),
                    confidence=0.9 if passed else 0.68,
                )
            )

        required_checks = [check for check in checks if check.name.lower() != "product detected" or True]
        failed_checks = [check for check in checks if not check.passed]
        passed_checks = [check for check in checks if check.passed]
        overall_passed = len(failed_checks) == 0

        summary = (
            "Inspection passed: all configured requirements were validated against the product image."
            if overall_passed
            else "Inspection failed: one or more required product checks were not confirmed by inspection."
        )

        return InspectionResult(
            product_name=product.name,
            category=product.category,
            passed=overall_passed,
            overall_confidence=sum(check.confidence for check in checks) / max(len(checks), 1),
            summary=summary,
            detections=detections,
            checks=checks,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
