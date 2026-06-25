from procurement.modules.data_pipeline.schemas import AwardRecord
from procurement.modules.pricing.pricing_model import predict_l1_price


def make_award(index: int, quantity: int, total_price: float) -> AwardRecord:
    return AwardRecord(
        bid_id=str(index),
        bid_number=f"GEM/2026/B/{index}",
        category_name="laptop",
        quantity=quantity,
        total_price=total_price,
        unit_price=total_price / quantity,
        seller_count=5,
        result_url=f"https://example.com/{index}",
    )


def test_pricing_model_filters_large_outlier() -> None:
    awards = [
        make_award(1, 10, 450_000),
        make_award(2, 10, 470_000),
        make_award(3, 10, 460_000),
        make_award(4, 10, 455_000),
        make_award(5, 10, 4_500_000),
    ]

    prediction = predict_l1_price(awards, target_quantity=10)

    assert prediction.removed_outliers == 1
    assert 450_000 <= prediction.predicted_l1_price <= 470_000
