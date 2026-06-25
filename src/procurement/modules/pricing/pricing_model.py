"""Estimate an L1 price after removing unusual historical prices."""

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from procurement.modules.data_pipeline.schemas import AwardRecord

DEFAULT_UNIT_PRICE = 45_000


class PricingPrediction(BaseModel):
    """L1 estimate and details about the historical data used."""

    predicted_l1_price: float = Field(gt=0)
    low_estimate: float = Field(gt=0)
    high_estimate: float = Field(gt=0)
    samples_used: int = Field(ge=0)
    removed_outliers: int = Field(ge=0)


def predict_l1_price(
    awards: list[AwardRecord],
    target_quantity: int,
) -> PricingPrediction:
    """Predict total L1 price from historical unit prices."""

    prices = pd.Series([award.unit_price for award in awards], dtype=float)
    clean_prices, removed_count = remove_outliers(prices)

    if clean_prices.empty:
        predicted_price = DEFAULT_UNIT_PRICE * target_quantity
        return PricingPrediction(
            predicted_l1_price=predicted_price,
            low_estimate=predicted_price * 0.9,
            high_estimate=predicted_price * 1.1,
            samples_used=0,
            removed_outliers=removed_count,
        )

    return PricingPrediction(
        predicted_l1_price=float(clean_prices.median()) * target_quantity,
        low_estimate=float(clean_prices.quantile(0.25)) * target_quantity,
        high_estimate=float(clean_prices.quantile(0.75)) * target_quantity,
        samples_used=len(clean_prices),
        removed_outliers=removed_count,
    )


def remove_outliers(prices: pd.Series) -> tuple[pd.Series, int]:
    """Remove invalid values and IQR outliers from a price series."""

    clean = prices.replace([np.inf, -np.inf], np.nan).dropna()
    clean = clean[clean > 0]
    if len(clean) < 4:
        return clean, 0

    first_quartile = clean.quantile(0.25)
    third_quartile = clean.quantile(0.75)
    iqr = third_quartile - first_quartile
    lower_limit = max(0, first_quartile - 1.5 * iqr)
    upper_limit = third_quartile + 1.5 * iqr
    filtered = clean[clean.between(lower_limit, upper_limit)]

    return filtered, len(clean) - len(filtered)
