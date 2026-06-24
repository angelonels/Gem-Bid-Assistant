"""CLI entry point for live collection."""

import logging
from pathlib import Path

from procurement.modules.data_pipeline.gem_client import GemClient
from procurement.modules.data_pipeline.repository import (
    save_dataset,
)
from procurement.shared.config import get_settings


def main() -> None:
    """Collect a live GeM dataset."""

    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    with GemClient(timeout_seconds=settings.request_timeout_seconds) as client:
        dataset = client.collect_dataset(
            settings.search_keyword,
            max_tenders=settings.max_tenders,
            max_awards=settings.max_awards,
            cache_root=Path("data/cache"),
        )
    save_dataset(dataset, settings.cache_path)
    print(
        "Collected "
        f"{len(dataset.active_tenders)} tenders and "
        f"{len(dataset.historical_awards)} award samples at {settings.cache_path}"
    )
