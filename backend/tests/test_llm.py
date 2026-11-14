import pytest
from src.llm import draft_explanation_with_validator
from src.validator import validate_llm_output

def test_offline_mode_returns_template_fallback():
    context_packet = {
        "task": "explain_and_propose",
        "language": "mr",
        "moment": "MANDATE_FAILED",
        "facts": {},
        "cause": "Balance insufficient",
        "allowed_actions": ["retry_mandate"]
    }
    
    draft, trace_attempts, source_mode, val_details = draft_explanation_with_validator(
        context_packet=context_packet,
        facts={},
        allowed_actions=["retry_mandate"],
        language="mr"
    )
    
    assert draft is None
    assert source_mode == "template"
    assert trace_attempts[0]["stage"] == "TEMPLATE_FALLBACK"
    assert "Approved template used" in trace_attempts[0]["summary"]

def test_validator_retry_fallback_when_mock_fails():
    facts = {"emi": 4650}
    invalid_draft = {
        "explanation": "Your loan has guaranteed approval for ₹88888",
        "proposed_action": "disallowed_action"
    }
    
    val = validate_llm_output(invalid_draft, facts, ["retry_mandate"], "en")
    assert val.passed is False
    assert len(val.errors) >= 2 # Banned phrase + ungrounded number + disallowed action
