import json

import pytest

from src.data.report_processor import AIResearcher


def test_parse_structured_response_valid_json():
    ai = AIResearcher()
    raw = json.dumps({
        "core_business_audit": [
            {"id": 1, "title": "GPM", "status": "PASS", "description": "Strong margin"}
        ],
        "management_integrity": [
            {"title": "CEO Pay", "severity": "Pass", "description": "Reasonable compensation"}
        ],
        "valuation_impact": {
            "stage_1_growth_offset": 0.02,
            "stage_2_growth_offset": 0.01,
            "discount_rate_offset": -0.005,
        },
    })
    result = ai.parse_structured_response(raw)
    assert result["core_business_audit"][0]["status"] == "PASS"
    assert result["valuation_impact"]["stage_1_growth_offset"] == 0.02
    assert result["valuation_impact"]["stage_2_growth_offset"] == 0.01
    assert result["valuation_impact"]["discount_rate_offset"] == -0.005


def test_parse_structured_response_strips_markdown_fences():
    ai = AIResearcher()
    raw = """```json
    {
        "core_business_audit": [],
        "management_integrity": [],
        "valuation_impact": {
            "stage_1_growth_offset": 0.03,
            "stage_2_growth_offset": 0.005,
            "discount_rate_offset": -0.0025
        }
    }
    ```"""
    result = ai.parse_structured_response(raw)
    assert result["valuation_impact"]["stage_1_growth_offset"] == 0.03
    assert result["valuation_impact"]["stage_2_growth_offset"] == 0.005
    assert result["valuation_impact"]["discount_rate_offset"] == -0.0025


def test_empty_response_defaults():
    result = AIResearcher.empty_response()
    assert result["core_business_audit"] == []
    assert result["management_integrity"] == []
    assert result["valuation_impact"]["stage_1_growth_offset"] == 0.0
    assert result["valuation_impact"]["stage_2_growth_offset"] == 0.0
    assert result["valuation_impact"]["discount_rate_offset"] == 0.0


@pytest.mark.parametrize("unsafe_value", [float("nan"), float("inf"), 0.5, -0.5])
def test_parse_structured_response_rejects_unsafe_offsets(unsafe_value):
    ai = AIResearcher()
    raw = json.dumps({
        "core_business_audit": [],
        "management_integrity": [],
        "valuation_impact": {
            "stage_1_growth_offset": unsafe_value,
            "stage_2_growth_offset": 0.0,
            "discount_rate_offset": 0.0,
        },
    })

    with pytest.raises(ValueError, match="outside safe bounds"):
        ai.parse_structured_response(raw)


def test_parse_structured_response_rejects_non_array_audit_fields():
    ai = AIResearcher()
    raw = json.dumps({
        "core_business_audit": {"unexpected": "object"},
        "management_integrity": [],
        "valuation_impact": {},
    })

    with pytest.raises(ValueError, match="must be arrays"):
        ai.parse_structured_response(raw)
