"""Compliance domain schemas."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TenderThresholds(BaseModel):
    """Structured requirements extracted from unstructured tender text."""

    min_turnover_lakhs: float | None = Field(default=None, ge=0)
    mse_exemption_allowed: bool = False
    required_certifications: list[str] = Field(default_factory=list)
    required_registrations: list[str] = Field(default_factory=list)
    local_content_min_percent: float | None = Field(default=None, ge=0, le=100)
    experience_years_min: float | None = Field(default=None, ge=0)
    oem_authorization_required: bool = False
    source: Literal["llm", "regex_fallback"] = "llm"

    @field_validator("required_certifications", "required_registrations", mode="after")
    @classmethod
    def dedupe_values(cls, values: list[str]) -> list[str]:
        """Normalize repeated requirement labels."""

        seen: set[str] = set()
        normalized: list[str] = []
        for value in values:
            label = " ".join(value.strip().split())
            key = label.lower()
            if label and key not in seen:
                seen.add(key)
                normalized.append(label)
        return normalized


class VendorProfile(BaseModel):
    """Dummy vendor profile used by the dashboard."""

    name: str
    annual_turnover_lakhs: float = Field(ge=0)
    is_mse: bool = False
    is_mii: bool = False
    local_content_percent: float = Field(default=0, ge=0, le=100)
    experience_years: float = Field(default=0, ge=0)
    certifications: list[str] = Field(default_factory=list)
    registrations: list[str] = Field(default_factory=list)


class ComplianceCheck(BaseModel):
    """Single deterministic compliance result."""

    rule: str
    passed: bool
    message: str


class ComplianceResult(BaseModel):
    """Full vendor eligibility result."""

    vendor_name: str
    status: Literal["eligible", "ineligible"]
    checks: list[ComplianceCheck]
    extracted_thresholds: TenderThresholds
