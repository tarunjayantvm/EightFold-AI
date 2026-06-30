import sys
sys.path.append(".")

from agents.agent_10_validation import validate


def test_validate_handles_none_collections():
    profile = {
        "full_name": "Test User",
        "emails": None,
        "phones": None,
        "education": None,
        "location": None,
        "overall_confidence": 0.89,
    }

    result = validate(profile)

    assert result["_validation"]["passed"] is True
    assert result["_validation"]["errors"] == []
    assert result["_validation"]["warnings"] == []


def test_validate_accepts_multilabel_email_domains():
    profile = {
        "full_name": "Tarun Jayant V M",
        "emails": ["tarunjayant.2301250@srec.ac.in"],
        "phones": ["+916385582585"],
        "education": [],
        "location": {},
        "overall_confidence": 0.89,
    }

    result = validate(profile)

    assert result["_validation"]["passed"] is True
    assert result["_validation"]["errors"] == []
