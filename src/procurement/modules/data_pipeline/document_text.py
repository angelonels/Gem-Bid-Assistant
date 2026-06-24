"""Tender document text extraction."""

from pathlib import Path

from pypdf import PdfReader


def extract_pdf_text(pdf_path: Path, max_pages: int = 12) -> str:
    """Extract text from a GeM tender PDF."""

    reader = PdfReader(str(pdf_path))
    chunks: list[str] = []
    for page_number, page in enumerate(reader.pages[:max_pages], start=1):
        text = page.extract_text() or ""
        if text.strip():
            chunks.append(f"--- page {page_number} ---\n{text}")
    return "\n\n".join(chunks)


def write_extracted_text(pdf_path: Path, text_path: Path) -> str:
    """Extract PDF text and persist it next to the cached tender."""

    text = extract_pdf_text(pdf_path)
    text_path.parent.mkdir(parents=True, exist_ok=True)
    text_path.write_text(text, encoding="utf-8")
    return text
