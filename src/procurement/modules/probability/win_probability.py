"""Calculate win probability with deterministic rules."""

import math

from pydantic import BaseModel, Field

from procurement.modules.compliance.schemas import ComplianceResult, VendorProfile
from procurement.modules.pricing.pricing_model import PricingPrediction

PRICE_SENSITIVITY = 6
COMPETITOR_PENALTY = 0.08


class WinProbability(BaseModel):
    """Win probability and the price used in the calculation."""

    percent: float = Field(ge=0, le=100)
    effective_price: float = Field(ge=0)
    preference_percent: float = Field(ge=0, le=5)


def calculate_win_probability(
    vendor: VendorProfile,
    bid_price: float,
    pricing: PricingPrediction,
    compliance: ComplianceResult,
    competitor_count: float,
) -> WinProbability:
    """Return a smooth score that falls whenever the bid price rises."""

    if compliance.status == "ineligible":
        return WinProbability(
            percent=0,
            effective_price=bid_price,
            preference_percent=0,
        )

    preference = get_preference_percent(vendor)
    effective_price = bid_price * (1 - preference / 100)
    price_ratio = effective_price / pricing.predicted_l1_price

    score = PRICE_SENSITIVITY * (price_ratio - 1) + COMPETITOR_PENALTY * max(
        competitor_count - 1, 0
    )
    probability = 100 / (1 + math.exp(min(score, 700)))

    return WinProbability(
        percent=probability,
        effective_price=effective_price,
        preference_percent=preference,
    )


def get_preference_percent(vendor: VendorProfile) -> float:
    """Return the small demo preference used for MSE and MII vendors."""

    preference = 0.0
    if vendor.is_mse:
        preference += 3
    if vendor.is_mii:
        preference += 2
    return preference
