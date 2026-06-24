from procurement.modules.compliance.regex_parser import (
    RegexThresholdParser,
)


def test_regex_parser_extracts_common_tender_thresholds() -> None:
    text = """
    Minimum Average Annual Turnover of bidder should be Rs 1 Crore.
    MSEs are exempted from turnover criteria with Udyam registration.
    ISO 9001 and OEM authorization are mandatory.
    Local content should be minimum 50%.
    """

    thresholds = RegexThresholdParser().parse(text)

    assert thresholds.min_turnover_lakhs == 100
    assert thresholds.mse_exemption_allowed is True
    assert "ISO 9001" in thresholds.required_certifications
    assert thresholds.oem_authorization_required is True
    assert thresholds.local_content_min_percent == 50
