from procurement.modules.compliance.schemas import (
    ComplianceResult,
    TenderThresholds,
    VendorProfile,
)
from procurement.modules.pricing.pricing_model import (
    PricingPrediction,
)
from procurement.modules.probability.win_probability import (
    calculate_win_probability,
)


def test_win_probability_strictly_decreases_as_price_increases() -> None:
    vendor = VendorProfile(
        name="Eligible MSE",
        annual_turnover_lakhs=100,
        is_mse=True,
        is_mii=True,
    )
    compliance = ComplianceResult(
        vendor_name=vendor.name,
        status="eligible",
        checks=[],
        extracted_thresholds=TenderThresholds(),
    )
    pricing = PricingPrediction(
        predicted_l1_price=1_000_000,
        low_estimate=900_000,
        high_estimate=1_100_000,
        samples_used=8,
        removed_outliers=1,
    )
    prices = [700_000, 850_000, 1_000_000, 1_150_000, 1_300_000]

    probabilities = [
        calculate_win_probability(
            vendor, price, pricing, compliance, competitor_count=8
        ).percent
        for price in prices
    ]

    assert all(
        earlier > later
        for earlier, later in zip(
            probabilities[:-1],
            probabilities[1:],
            strict=True,
        )
    )
    assert all(0 <= probability <= 100 for probability in probabilities)


def test_ineligible_vendor_has_zero_probability() -> None:
    vendor = VendorProfile(name="Ineligible", annual_turnover_lakhs=10)
    compliance = ComplianceResult(
        vendor_name=vendor.name,
        status="ineligible",
        checks=[],
        extracted_thresholds=TenderThresholds(),
    )
    pricing = PricingPrediction(
        predicted_l1_price=1_000_000,
        low_estimate=900_000,
        high_estimate=1_100_000,
        samples_used=8,
        removed_outliers=0,
    )

    result = calculate_win_probability(
        vendor,
        800_000,
        pricing,
        compliance,
        competitor_count=6,
    )

    assert result.percent == 0
