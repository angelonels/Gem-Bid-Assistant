"""Streamlit page for checking one proposed GeM bid."""

from pathlib import Path

import pandas as pd
import streamlit as st

from procurement.modules.compliance.llm_parser import TenderThresholdExtractor
from procurement.modules.compliance.vendors import DEFAULT_VENDORS
from procurement.modules.data_pipeline.repository import load_dataset
from procurement.modules.orchestration.use_cases import TenderEvaluation, evaluate_bid
from procurement.modules.pricing.pricing_model import predict_l1_price
from procurement.shared.config import get_settings
from procurement.shared.money import format_rupees

st.set_page_config(page_title="GemEdge Bid Check", layout="centered")


@st.cache_data
def get_dataset(cache_path: str):
    """Load the saved GeM data once."""

    return load_dataset(Path(cache_path))


def main() -> None:
    settings = get_settings()
    dataset = get_dataset(str(settings.cache_path))
    extractor = TenderThresholdExtractor(settings)

    st.title("GemEdge Bid Check")
    st.write("Choose a tender and vendor, then enter your planned bid.")

    with st.form("bid_form"):
        tender = st.selectbox(
            "Tender",
            dataset.active_tenders,
            format_func=lambda item: f"{item.bid_number} - {item.category_name}",
        )
        vendor = st.selectbox(
            "Vendor",
            DEFAULT_VENDORS,
            format_func=lambda item: item.name,
        )
        suggested_price = predict_l1_price(
            dataset.historical_awards,
            tender.quantity,
        ).predicted_l1_price
        bid_price = st.number_input(
            "Bid amount",
            min_value=1_000.0,
            value=float(round(suggested_price)),
            step=5_000.0,
        )
        submitted = st.form_submit_button("Predict", type="primary")

    if submitted:
        result = evaluate_bid(
            tender,
            vendor,
            bid_price,
            dataset.historical_awards,
            extractor,
        )
        show_result(result)


def show_result(result: TenderEvaluation) -> None:
    """Display the three main results and the compliance checks."""

    st.subheader("Result")
    can_bid = "Yes" if result.compliance.status == "eligible" else "No"

    eligibility_column, price_column, chance_column = st.columns(3)
    eligibility_column.metric("Can bid?", can_bid)
    price_column.metric(
        "Estimated L1",
        format_rupees(result.pricing.predicted_l1_price),
    )
    chance_column.metric(
        "Win chance",
        f"{result.win_probability.percent:.1f}%",
    )

    rows = [
        {
            "Check": check.rule,
            "Passed": "Yes" if check.passed else "No",
            "Details": check.message,
        }
        for check in result.compliance.checks
    ]
    st.subheader("Compliance checks")
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

    st.caption(
        f"Expected price range: {format_rupees(result.pricing.low_estimate)} to "
        f"{format_rupees(result.pricing.high_estimate)}. "
        f"{result.pricing.removed_outliers} price outliers were removed."
    )


if __name__ == "__main__":
    main()
