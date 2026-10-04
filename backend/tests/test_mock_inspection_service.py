from app.models import InspectionRequirement, ProductConfiguration
from app.services.mock_inspection_service import MockInspectionService


def build_product(*requirements: InspectionRequirement) -> ProductConfiguration:
    return ProductConfiguration(
        name="Beverage Bottle",
        category="Packaging",
        image_url="https://example.com/product.jpg",
        requirements=list(requirements),
    )


def test_default_configuration_passes() -> None:
    product = build_product(
        InspectionRequirement(id="prod", name="Product detected", description="Main product is visible", required=True),
        InspectionRequirement(id="label", name="Label present", description="Label is visible", required=True),
        InspectionRequirement(id="cap", name="Cap present", description="Cap is visible", required=True),
        InspectionRequirement(id="logo", name="Logo visible", description="Logo is visible", required=True),
        InspectionRequirement(id="damage", name="Packaging damage", description="No visible damage", required=True),
    )

    result = MockInspectionService().run(product)

    assert result.passed is True
    checks = {check.name: check for check in result.checks}
    assert checks["Product detected"].passed is True
    assert checks["Label present"].passed is True
    assert checks["Cap present"].passed is True
    assert checks["Logo visible"].passed is True
    assert checks["Packaging damage"].passed is True


def test_failing_required_requirement_is_reported() -> None:
    product = build_product(
        InspectionRequirement(id="prod", name="Product detected", description="Main product is visible", required=True),
        InspectionRequirement(id="missing", name="Sticker present", description="Sticker should be visible", required=True),
    )

    result = MockInspectionService().run(product)

    assert result.passed is False
    checks = {check.name: check for check in result.checks}
    assert checks["Sticker present"].passed is False


def test_optional_requirements_do_not_fail_overall() -> None:
    product = build_product(
        InspectionRequirement(id="prod", name="Product detected", description="Main product is visible", required=True),
        InspectionRequirement(id="optional", name="Optional decal present", description="Nice to have", required=False),
    )

    result = MockInspectionService().run(product)

    assert result.passed is True
    checks = {check.name: check for check in result.checks}
    assert checks["Optional decal present"].passed is False
