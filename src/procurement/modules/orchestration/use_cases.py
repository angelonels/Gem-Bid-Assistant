"""Run the four assignment steps for one bid."""

from pathlib import Path

from pydantic import BaseModel

from procurement.modules.compliance.llm_parser import TenderThresholdExtractor
from procurement.modules.compliance.rule_engine import check_compliance
from procurement.modules.compliance.schemas import ComplianceResult, VendorProfile
from procurement.modules.data_pipeline.schemas import AwardRecord, TenderRecord
from procurement.modules.pricing.pricing_model import (
    PricingPrediction,
    predict_l1_price,
)
from procurement.modules.probability.win_probability import (
    WinProbability,
    calculate_win_probability,
)


class TenderEvaluation(BaseModel):
    """All results shown by the Streamlit app."""

    compliance: ComplianceResult
    pricing: PricingPrediction
    win_probability: WinProbability


def evaluate_bid(
    tender: TenderRecord,
    vendor: VendorProfile,
    bid_price: float,
    awards: list[AwardRecord],
    extractor: TenderThresholdExtractor,
) -> TenderEvaluation:
    """Parse requirements, check compliance, and calculate both predictions."""

    tender_text = read_tender_text(tender)
    requirements = extractor.extract(tender_text)
    compliance = check_compliance(vendor, requirements)
    pricing = predict_l1_price(awards, tender.quantity)

    if awards:
        competitor_count = sum(item.seller_count for item in awards) / len(awards)
    else:
        competitor_count = 4

    probability = calculate_win_probability(
        vendor,
        bid_price,
        pricing,
        compliance,
        competitor_count,
    )
    return TenderEvaluation(
        compliance=compliance,
        pricing=pricing,
        win_probability=probability,
    )


def read_tender_text(tender: TenderRecord) -> str:
    """Read downloaded tender text or use its basic details."""

    if tender.text_path and Path(tender.text_path).exists():
        return Path(tender.text_path).read_text(encoding="utf-8", errors="ignore")
    return (
        f"Bid number: {tender.bid_number}\n"
        f"Category: {tender.category_name}\n"
        f"Quantity: {tender.quantity}"
    )
