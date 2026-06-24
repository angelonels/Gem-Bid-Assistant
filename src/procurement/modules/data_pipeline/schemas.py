"""Data pipeline schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class TenderRecord(BaseModel):
    """Normalized active GeM tender metadata."""

    bid_id: str
    bid_number: str
    category_name: str
    quantity: int = Field(ge=1)
    document_url: HttpUrl | str
    text_path: str | None = None


class AwardRecord(BaseModel):
    """Historical award/L1 price sample."""

    bid_id: str
    bid_number: str
    category_name: str
    quantity: int = Field(ge=1)
    total_price: float = Field(gt=0)
    unit_price: float = Field(gt=0)
    seller_count: int = Field(default=1, ge=1)
    result_url: HttpUrl | str


class ProcurementDataset(BaseModel):
    """Local cache consumed by the UI and tests."""

    keyword: str
    collected_at: datetime
    active_tenders: list[TenderRecord]
    historical_awards: list[AwardRecord]
