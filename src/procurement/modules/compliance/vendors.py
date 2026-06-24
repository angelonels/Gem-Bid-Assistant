"""Dummy vendor profiles for the assignment demo."""

from procurement.modules.compliance.schemas import VendorProfile

DEFAULT_VENDORS = [
    VendorProfile(
        name="Vendor A - Strong MSE Laptop Supplier",
        annual_turnover_lakhs=100,
        is_mse=True,
        is_mii=True,
        local_content_percent=62,
        experience_years=6,
        certifications=["ISO 9001", "BIS", "OEM Authorization"],
        registrations=["Udyam", "GST"],
    ),
    VendorProfile(
        name="Vendor B - Small Non-MSE Trader",
        annual_turnover_lakhs=30,
        is_mse=False,
        is_mii=False,
        local_content_percent=28,
        experience_years=1,
        certifications=["GST"],
        registrations=["GST"],
    ),
    VendorProfile(
        name="Vendor C - Mid-Market Integrator",
        annual_turnover_lakhs=75,
        is_mse=False,
        is_mii=True,
        local_content_percent=55,
        experience_years=4,
        certifications=["ISO 9001", "OEM Authorization"],
        registrations=["GST"],
    ),
]
