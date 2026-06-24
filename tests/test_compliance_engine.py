from procurement.modules.compliance.rule_engine import check_compliance
from procurement.modules.compliance.schemas import (
    TenderThresholds,
    VendorProfile,
)


def test_mse_turnover_exemption_allows_small_mse_vendor() -> None:
    thresholds = TenderThresholds(
        min_turnover_lakhs=100,
        mse_exemption_allowed=True,
        required_registrations=["Udyam"],
    )
    vendor = VendorProfile(
        name="Small MSE",
        annual_turnover_lakhs=20,
        is_mse=True,
        registrations=["Udyam"],
    )

    result = check_compliance(vendor, thresholds)

    assert result.status == "eligible"
    assert all(check.passed for check in result.checks)


def test_missing_required_certificate_fails() -> None:
    thresholds = TenderThresholds(required_certifications=["ISO 9001"])
    vendor = VendorProfile(name="Trader", annual_turnover_lakhs=200)

    result = check_compliance(vendor, thresholds)

    assert result.status == "ineligible"
    assert any(check.rule == "Certification: ISO 9001" for check in result.checks)


def test_vendor_fails_when_experience_is_below_requirement() -> None:
    thresholds = TenderThresholds(experience_years_min=3)
    vendor = VendorProfile(
        name="New supplier",
        annual_turnover_lakhs=100,
        experience_years=1,
    )

    result = check_compliance(vendor, thresholds)

    experience_check = next(
        check for check in result.checks if check.rule == "Experience"
    )
    assert result.status == "ineligible"
    assert experience_check.passed is False
