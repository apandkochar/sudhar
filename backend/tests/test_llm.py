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

def test_cache_fallback_served_on_invalid_api_key(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "live")
    context_packet = {
        "task": "explain_and_propose",
        "language": "mr",
        "moment": "MANDATE_FAILED",
        "persona_id": "rohit",
        "facts": {
            "persona_id": "rohit",
            "loan_details": {"loan_amount": 50000, "emi_amount": 4650},
            "bank_accounts": [
                {"bank_name": "HDFC", "account_last4": "9012"},
                {"bank_name": "SBI", "account_last4": "4521"}
            ]
        },
        "cause": "Balance insufficient",
        "allowed_actions": ["retry_mandate"]
    }
    
    draft, trace_attempts, source_mode, val_details = draft_explanation_with_validator(
        context_packet=context_packet,
        facts=context_packet["facts"],
        allowed_actions=["retry_mandate"],
        language="mr",
        action_params={"account_last4": "4521"},
        api_key="INVALID_MOCK_API_KEY_12345"
    )

    assert draft is not None
    assert source_mode == "gemini"
    assert val_details["source"] == "gemini_cache"
    # Must include cached trace row
    cached_trace = next((t for t in trace_attempts if t["summary"] == "Cached Gemini draft · validated earlier"), None)
    assert cached_trace is not None
    assert cached_trace["is_ai"] is True
    assert "9012" in draft["explanation"] or "4521" in draft["explanation"]

def test_cache_persistence_and_retrieval(tmp_path, monkeypatch):
    from src import cache
    cache_path = tmp_path / "test_cache.json"
    monkeypatch.setattr(cache, "CACHE_FILE", cache_path)
    
    test_payload = {
        "explanation": "Test explanation text",
        "proposed_action": "test_action",
        "action_label": "Test",
        "confidence": 0.99
    }
    cache.save_cached_llm_response("test_persona", "en", test_payload)
    fetched = cache.get_cached_llm_response("test_persona", "en")
    assert fetched is not None
    assert fetched["explanation"] == "Test explanation text"

