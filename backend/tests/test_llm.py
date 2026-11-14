import pytest
from src.llm import draft_explanation_with_validator

def test_offline_mode_returns_template_fallback():
    # In offline mode (default DEMO_MODE=offline), draft_explanation_with_validator
    # must cleanly return source_mode="template" with is_ai=False
    context_packet = {
        "task": "explain_and_propose",
        "language": "mr",
        "moment": "MANDATE_FAILED",
        "facts": {},
        "cause": "Balance insufficient",
        "allowed_actions": ["retry_mandate"]
    }
    
    draft, details, source_mode, summary = draft_explanation_with_validator(
        context_packet=context_packet,
        facts={},
        allowed_actions=["retry_mandate"],
        language="mr"
    )
    
    assert draft is None
    assert source_mode == "template"
    assert "Offline mode" in details["reason"]

def test_validator_retry_fallback_when_mock_fails():
    # Test validator with mock invalid output
    from src.validator import validate_llm_output
    
    facts = {"emi": 4650}
    invalid_draft = {
        "explanation": "Your loan has guaranteed approval for ₹88888",
        "proposed_action": "disallowed_action"
    }
    
    val = validate_llm_output(invalid_draft, facts, ["retry_mandate"], "en")
    assert val.passed is False
    assert len(val.errors) >= 2 # Banned phrase + ungrounded number + disallowed action
