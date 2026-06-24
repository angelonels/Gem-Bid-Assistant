"""Dataset persistence."""

from pathlib import Path

from procurement.modules.data_pipeline.sample_data import (
    build_sample_dataset,
    ensure_sample_text,
)
from procurement.modules.data_pipeline.schemas import (
    ProcurementDataset,
)


def load_dataset(path: Path) -> ProcurementDataset:
    """Load cached live data or return the offline sample dataset."""

    if path.exists():
        return ProcurementDataset.model_validate_json(path.read_text(encoding="utf-8"))
    ensure_sample_text()
    return build_sample_dataset()


def save_dataset(dataset: ProcurementDataset, path: Path) -> None:
    """Persist a normalized dataset."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dataset.model_dump_json(indent=2), encoding="utf-8")
