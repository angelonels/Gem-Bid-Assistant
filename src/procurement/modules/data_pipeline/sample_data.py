"""Deterministic fallback data for offline demos and tests."""

from datetime import UTC, datetime
from pathlib import Path

from procurement.modules.data_pipeline.schemas import (
    AwardRecord,
    ProcurementDataset,
    TenderRecord,
)

SAMPLE_TENDER_TEXT = """
Bid Number: GEM/2026/B/SAMPLE-LAPTOP
Item: Entry and Mid Level Laptop - Notebook
Quantity: 20
Minimum Average Annual Turnover of the bidder for 3 years should be Rs 50 Lakh.
MSEs are exempted from turnover criteria subject to valid Udyam registration.
The bidder must submit ISO 9001 certificate and OEM authorization.
Local content requirement: minimum 50 percent for Class-I local supplier.
Past experience of 2 years in similar supplies is preferred.
"""


def build_sample_dataset() -> ProcurementDataset:
    """Return a small GeM-like dataset when live collection is unavailable."""

    tenders = [
        TenderRecord(
            bid_id="sample-1",
            bid_number="GEM/2026/B/SAMPLE-LAPTOP",
            category_name="Entry and Mid Level Laptop - Notebook",
            quantity=20,
            document_url="https://bidplus.gem.gov.in/showbidDocument/sample-1",
            text_path="data/cache/tenders/sample-1.txt",
        ),
        TenderRecord(
            bid_id="sample-2",
            bid_number="GEM/2026/B/SAMPLE-PRINTER",
            category_name="Laptop, Printer and Networking Accessories",
            quantity=45,
            document_url="https://bidplus.gem.gov.in/showbidDocument/sample-2",
            text_path="data/cache/tenders/sample-2.txt",
        ),
        TenderRecord(
            bid_id="sample-3",
            bid_number="GEM/2026/B/SAMPLE-AIO",
            category_name="All in One PC and Laptop",
            quantity=12,
            document_url="https://bidplus.gem.gov.in/showbidDocument/sample-3",
            text_path="data/cache/tenders/sample-3.txt",
        ),
    ]
    totals = [
        (18, 795_000, 6),
        (25, 1_090_000, 8),
        (12, 540_000, 5),
        (30, 1_260_000, 9),
        (40, 1_820_000, 12),
        (22, 950_000, 7),
        (16, 700_000, 4),
        (35, 1_560_000, 10),
        (20, 2_400_000, 3),
    ]
    awards = [
        AwardRecord(
            bid_id=f"sample-award-{index}",
            bid_number=f"GEM/2026/B/AWARD-{index:03d}",
            category_name="laptop",
            quantity=quantity,
            total_price=total_price,
            unit_price=total_price / quantity,
            seller_count=seller_count,
            result_url=f"https://bidplus.gem.gov.in/bidding/bid/sample/{index}",
        )
        for index, (quantity, total_price, seller_count) in enumerate(totals, start=1)
    ]
    return ProcurementDataset(
        keyword="laptop",
        collected_at=datetime.now(tz=UTC),
        active_tenders=tenders,
        historical_awards=awards,
    )


def ensure_sample_text() -> None:
    """Write fallback tender text used by the Streamlit demo."""

    path = Path("data/cache/tenders/sample-1.txt")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(SAMPLE_TENDER_TEXT, encoding="utf-8")
    for sample_id in ("sample-2", "sample-3"):
        Path(f"data/cache/tenders/{sample_id}.txt").write_text(
            SAMPLE_TENDER_TEXT.replace("Quantity: 20", "Quantity: 45"),
            encoding="utf-8",
        )
