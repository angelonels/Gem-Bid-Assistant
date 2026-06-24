"""Deterministic fallback parser for common tender clauses."""

import re

from procurement.modules.compliance.schemas import TenderThresholds


def _turnover_to_lakhs(amount: float, unit: str | None) -> float:
    unit_normalized = (unit or "lakh").lower()
    if unit_normalized in {"crore", "cr"}:
        return amount * 100
    return amount


class RegexThresholdParser:
    """Extract conservative threshold hints without an LLM."""

    certification_patterns = {
        "ISO 9001": r"\biso\s*9001\b",
        "ISO 27001": r"\biso\s*27001\b",
        "BIS": r"\bbis\b",
        "CE": r"\bce\s+cert",
    }

    def parse(self, tender_text: str) -> TenderThresholds:
        """Parse a tender into the strict threshold schema."""

        text = " ".join(tender_text.split())
        lowered = text.lower()
        turnover = self._find_turnover_lakhs(text)
        local_content = self._find_local_content(text)
        experience = self._find_experience_years(text)
        certifications = [
            label
            for label, pattern in self.certification_patterns.items()
            if re.search(pattern, text, flags=re.IGNORECASE)
        ]
        registrations: list[str] = []
        if re.search(r"\budyam\b|\bmse\b|\bmsme\b", text, flags=re.IGNORECASE):
            registrations.append("Udyam")
        if re.search(r"\bgst(?:in)?\b", text, flags=re.IGNORECASE):
            registrations.append("GST")
        return TenderThresholds(
            min_turnover_lakhs=turnover,
            mse_exemption_allowed="mse" in lowered and "exempt" in lowered,
            required_certifications=certifications,
            required_registrations=registrations,
            local_content_min_percent=local_content,
            experience_years_min=experience,
            oem_authorization_required=bool(
                re.search(r"\boem\s+authori[sz]ation\b", text, flags=re.IGNORECASE)
            ),
            source="regex_fallback",
        )

    @staticmethod
    def _find_turnover_lakhs(text: str) -> float | None:
        pattern = (
            r"(?:turnover|annual turnover|average annual turnover)"
            r".{0,80}?([0-9]+(?:\.[0-9]+)?)\s*(crore|cr|lakh|lakhs)?"
        )
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match is None:
            return None
        return _turnover_to_lakhs(float(match.group(1)), match.group(2))

    @staticmethod
    def _find_local_content(text: str) -> float | None:
        pattern = r"(?:local content|class-i).{0,80}?([0-9]+(?:\.[0-9]+)?)\s*%"
        match = re.search(pattern, text, flags=re.IGNORECASE)
        return float(match.group(1)) if match else None

    @staticmethod
    def _find_experience_years(text: str) -> float | None:
        pattern = (
            r"(?:experience|similar supplies).{0,80}?([0-9]+(?:\.[0-9]+)?)\s*years?"
        )
        match = re.search(pattern, text, flags=re.IGNORECASE)
        return float(match.group(1)) if match else None
