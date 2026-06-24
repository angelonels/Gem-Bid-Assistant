"""Small currency parsing helpers."""

import re

RUPEE_MULTIPLIERS = {
    "crore": 10_000_000,
    "cr": 10_000_000,
    "lakh": 100_000,
    "lac": 100_000,
    "lakhs": 100_000,
}


def parse_indian_money(text: str) -> float | None:
    """Parse common Indian money snippets into rupees."""

    cleaned = text.replace(",", "").replace("`", "").replace("₹", " Rs ")
    match = re.search(
        r"(?:rs\.?|inr)?\s*([0-9]+(?:\.[0-9]+)?)\s*(crore|cr|lakh|lac|lakhs)?",
        cleaned,
        flags=re.IGNORECASE,
    )
    if match is None:
        return None
    amount = float(match.group(1))
    unit = (match.group(2) or "").lower()
    return amount * RUPEE_MULTIPLIERS.get(unit, 1)


def format_rupees(value: float) -> str:
    """Format rupees for display without depending on locale settings."""

    return f"Rs {value:,.0f}"
