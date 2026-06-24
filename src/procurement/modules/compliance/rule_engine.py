"""Check a vendor against extracted tender requirements."""

from procurement.modules.compliance.schemas import (
    ComplianceCheck,
    ComplianceResult,
    TenderThresholds,
    VendorProfile,
)


def check_compliance(
    vendor: VendorProfile,
    requirements: TenderThresholds,
) -> ComplianceResult:
    """Run every compliance rule with normal Python code."""

    checks = [
        check_turnover(vendor, requirements),
        check_local_content(vendor, requirements),
        check_experience(vendor, requirements),
        check_oem_authorization(vendor, requirements),
    ]

    for name in requirements.required_certifications:
        checks.append(
            ComplianceCheck(
                rule=f"Certification: {name}",
                passed=has_value(vendor.certifications, name),
                message=f"Required certification: {name}.",
            )
        )

    for name in requirements.required_registrations:
        has_registration = has_value(vendor.registrations, name)
        if name.lower() == "udyam":
            has_registration = has_registration and vendor.is_mse
        checks.append(
            ComplianceCheck(
                rule=f"Registration: {name}",
                passed=has_registration,
                message=f"Required registration: {name}.",
            )
        )

    status = "eligible" if all(check.passed for check in checks) else "ineligible"
    return ComplianceResult(
        vendor_name=vendor.name,
        status=status,
        checks=checks,
        extracted_thresholds=requirements,
    )


def check_turnover(
    vendor: VendorProfile,
    requirements: TenderThresholds,
) -> ComplianceCheck:
    """Check turnover, including the tender's MSE exemption."""

    required = requirements.min_turnover_lakhs
    if required is None:
        return passed_check("Turnover", "No turnover requirement found.")
    if vendor.annual_turnover_lakhs >= required:
        return passed_check("Turnover", "Vendor meets the turnover requirement.")
    if vendor.is_mse and requirements.mse_exemption_allowed:
        return passed_check("Turnover", "MSE turnover exemption applies.")
    return failed_check("Turnover", f"Requires {required:g} lakhs turnover.")


def check_local_content(
    vendor: VendorProfile,
    requirements: TenderThresholds,
) -> ComplianceCheck:
    """Check the vendor's local-content percentage."""

    required = requirements.local_content_min_percent
    if required is None:
        return passed_check("Local content", "No local-content requirement found.")
    passed = vendor.local_content_percent >= required
    message = (
        f"Vendor has {vendor.local_content_percent:g}% local content; "
        f"{required:g}% is required."
    )
    return ComplianceCheck(rule="Local content", passed=passed, message=message)


def check_experience(
    vendor: VendorProfile,
    requirements: TenderThresholds,
) -> ComplianceCheck:
    """Check the vendor's years of experience."""

    required = requirements.experience_years_min
    if required is None:
        return passed_check("Experience", "No experience requirement found.")
    passed = vendor.experience_years >= required
    message = (
        f"Vendor has {vendor.experience_years:g} years of experience; "
        f"{required:g} years are required."
    )
    return ComplianceCheck(rule="Experience", passed=passed, message=message)


def check_oem_authorization(
    vendor: VendorProfile,
    requirements: TenderThresholds,
) -> ComplianceCheck:
    """Check OEM authorization when the tender requires it."""

    if not requirements.oem_authorization_required:
        return passed_check("OEM authorization", "Not required.")
    passed = has_value(vendor.certifications, "OEM Authorization")
    return ComplianceCheck(
        rule="OEM authorization",
        passed=passed,
        message="OEM authorization is required.",
    )


def has_value(values: list[str], required: str) -> bool:
    """Compare labels without caring about letter case."""

    required = required.lower()
    return any(required in value.lower() for value in values)


def passed_check(rule: str, message: str) -> ComplianceCheck:
    return ComplianceCheck(rule=rule, passed=True, message=message)


def failed_check(rule: str, message: str) -> ComplianceCheck:
    return ComplianceCheck(rule=rule, passed=False, message=message)
