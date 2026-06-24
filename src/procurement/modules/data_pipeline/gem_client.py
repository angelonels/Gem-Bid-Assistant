"""Live GeM data client."""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from playwright.sync_api import APIRequestContext, Playwright, sync_playwright

from procurement.modules.data_pipeline.document_text import (
    write_extracted_text,
)
from procurement.modules.data_pipeline.schemas import (
    AwardRecord,
    ProcurementDataset,
    TenderRecord,
)
from procurement.shared.money import parse_indian_money

LOGGER = logging.getLogger(__name__)


def _first(value: Any, default: Any = None) -> Any:
    if isinstance(value, list):
        return value[0] if value else default
    return value if value is not None else default


class GemClient:
    """Client for public GeM bid listing, PDF, and result pages."""

    base_url = "https://bidplus.gem.gov.in"

    def __init__(self, timeout_seconds: int = 30) -> None:
        self.timeout_millis = timeout_seconds * 1000
        self._playwright: Playwright = sync_playwright().start()
        self.request_context: APIRequestContext = self._playwright.request.new_context(
            base_url=self.base_url,
            extra_http_headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 Chrome/126 Safari/537.36"
                )
            },
        )
        self._csrf_token: str | None = None

    def close(self) -> None:
        """Release Playwright resources."""

        self.request_context.dispose()
        self._playwright.stop()

    def __enter__(self) -> GemClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def search_bids(
        self,
        keyword: str,
        *,
        page: int = 1,
        status_type: str = "ongoing_bids",
        status_filter: str = "all",
    ) -> list[dict[str, Any]]:
        """Search GeM listings through the endpoint used by the public page."""

        payload = {
            "page": page,
            "param": {"searchBid": keyword, "searchType": "fullText"},
            "filter": {
                "bidStatusType": status_type,
                "byType": "all",
                "highBidValue": "",
                "byEndDate": {"from": "", "to": ""},
                "byStatus": status_filter,
                "sort": "Bid-End-Date-Latest",
            },
        }
        response = self.request_context.post(
            "/all-bids-data",
            form={
                "payload": json.dumps(payload),
                "csrf_bd_gem_nk": self._csrf_token_from_listing_page(),
            },
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{self.base_url}/all-bids",
            },
            timeout=self.timeout_millis,
        )
        _raise_for_status(response.status, response.status_text, "/all-bids-data")
        body = response.json()
        if body.get("code") != 200:
            raise RuntimeError(f"GeM search failed: {body.get('message')}")
        return body["response"]["response"].get("docs", [])

    def normalize_tender(self, raw_bid: dict[str, Any]) -> TenderRecord:
        """Convert GeM search JSON into a stable schema."""

        bid_id = str(_first(raw_bid.get("b_id"), raw_bid.get("id")))
        return TenderRecord(
            bid_id=bid_id,
            bid_number=str(_first(raw_bid.get("b_bid_number"), "")),
            category_name=str(_first(raw_bid.get("b_category_name"), "")),
            quantity=int(_first(raw_bid.get("b_total_quantity"), 1) or 1),
            document_url=f"{self.base_url}/showbidDocument/{bid_id}",
        )

    def download_tender_document(
        self,
        tender: TenderRecord,
        output_dir: Path,
    ) -> TenderRecord:
        """Download the official tender PDF and write extracted text."""

        output_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = output_dir / f"{tender.bid_id}.pdf"
        text_path = output_dir / f"{tender.bid_id}.txt"

        response = self.request_context.get(
            str(tender.document_url),
            headers={"Referer": f"{self.base_url}/all-bids"},
            timeout=self.timeout_millis,
        )
        _raise_for_status(
            response.status,
            response.status_text,
            str(tender.document_url),
        )
        content_type = response.headers.get("content-type", "")
        if "pdf" not in content_type.lower():
            raise RuntimeError(f"Bid {tender.bid_id} did not return a PDF.")

        pdf_path.write_bytes(response.body())
        write_extracted_text(pdf_path, text_path)
        return tender.model_copy(update={"text_path": str(text_path)})

    def fetch_result_html(self, raw_bid: dict[str, Any]) -> tuple[str, str]:
        """Fetch the most likely result page for an awarded bid."""

        bid_id = str(_first(raw_bid.get("b_id"), raw_bid.get("id")))
        single_packet = int(_first(raw_bid.get("ba_is_single_packet"), 0) or 0)
        eval_type = int(_first(raw_bid.get("b_eval_type"), 0) or 0)
        if eval_type > 0:
            path = f"/bidding/bid/getBidResultViewSchedule/{bid_id}"
        elif single_packet == 1:
            path = f"/bidding/bid/getSinglePacketResultView/{bid_id}"
        else:
            path = f"/bidding/bid/getBidResultView/{bid_id}"

        url = f"{self.base_url}{path}"
        response = self.request_context.get(url, timeout=self.timeout_millis)
        _raise_for_status(response.status, response.status_text, url)
        return url, response.text()

    def parse_award_record(
        self,
        raw_bid: dict[str, Any],
        result_url: str,
        result_html: str,
    ) -> AwardRecord | None:
        """Extract an awarded L1 total price from public result HTML."""

        candidate_prices = _extract_l1_prices(result_html)
        if not candidate_prices:
            return None

        quantity = int(_first(raw_bid.get("b_total_quantity"), 1) or 1)
        total_price = float(min(candidate_prices))
        bid_id = str(_first(raw_bid.get("b_id"), raw_bid.get("id")))
        return AwardRecord(
            bid_id=bid_id,
            bid_number=str(_first(raw_bid.get("b_bid_number"), "")),
            category_name=str(_first(raw_bid.get("b_category_name"), "")),
            quantity=quantity,
            total_price=total_price,
            unit_price=total_price / quantity,
            seller_count=_count_result_prices(result_html),
            result_url=result_url,
        )

    def collect_dataset(
        self,
        keyword: str,
        *,
        max_tenders: int,
        max_awards: int,
        cache_root: Path,
    ) -> ProcurementDataset:
        """Collect active tenders, official PDFs, and historical award prices."""

        active_tenders: list[TenderRecord] = []
        for raw_bid in self.search_bids(keyword, status_type="ongoing_bids")[
            :max_tenders
        ]:
            tender = self.normalize_tender(raw_bid)
            try:
                active_tenders.append(
                    self.download_tender_document(tender, cache_root / "tenders")
                )
            except Exception as exc:
                LOGGER.warning("Could not download tender %s: %s", tender.bid_id, exc)
                active_tenders.append(tender)

        historical_awards: list[AwardRecord] = []
        awarded_bids = self.search_bids(
            keyword,
            status_type="bidrastatus",
            status_filter="bid_awarded",
        )
        for raw_bid in awarded_bids[: max_awards * 2]:
            if len(historical_awards) >= max_awards:
                break
            try:
                result_url, result_html = self.fetch_result_html(raw_bid)
                award = self.parse_award_record(raw_bid, result_url, result_html)
                if award:
                    historical_awards.append(award)
            except Exception as exc:
                LOGGER.info("Skipping award sample because parsing failed: %s", exc)

        return ProcurementDataset(
            keyword=keyword,
            collected_at=datetime.now(tz=UTC),
            active_tenders=active_tenders,
            historical_awards=historical_awards,
        )

    def _csrf_token_from_listing_page(self) -> str:
        if self._csrf_token:
            return self._csrf_token

        response = self.request_context.get("/all-bids", timeout=self.timeout_millis)
        _raise_for_status(response.status, response.status_text, "/all-bids")
        match = re.search(
            r"csrf_bd_gem_nk'\s*:\s*'([a-f0-9]+)'",
            response.text(),
            flags=re.IGNORECASE,
        )
        if match is None:
            raise RuntimeError("Could not find GeM CSRF token on all-bids page.")
        self._csrf_token = match.group(1)
        return self._csrf_token


def _raise_for_status(status: int, status_text: str, url: str) -> None:
    if 200 <= status < 300:
        return
    raise RuntimeError(f"GeM request failed for {url}: {status} {status_text}")


def _extract_l1_prices(result_html: str) -> list[float]:
    """Read L1 prices from result-page price fields or an L1 table row."""

    prices: list[float] = []
    price_blocks = re.findall(
        r'<span class=["\']bid_price["\'][^>]*>(.*?)</span>',
        result_html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    for block in price_blocks:
        parsed = parse_indian_money(_strip_tags(block))
        if parsed and parsed > 1_000:
            prices.append(parsed)
    if prices:
        return prices[:1]

    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", result_html, flags=re.DOTALL)
    for row_html in rows:
        row_text = _strip_tags(row_html)
        if "L1" not in row_text.upper():
            continue
        for number in re.findall(r"[0-9][0-9,]+(?:\.[0-9]+)?", row_text):
            parsed = parse_indian_money(number)
            if parsed and parsed > 1_000:
                prices.append(parsed)
    return [price for price in prices if price > 1_000]


def _count_result_prices(result_html: str) -> int:
    price_count = len(
        re.findall(r'class=["\'][^"\']*bid_price', result_html, flags=re.IGNORECASE)
    )
    return max(1, price_count)


def _strip_tags(html: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", html).split())
