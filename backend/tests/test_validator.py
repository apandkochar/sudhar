import pytest
from src.validator import validate_llm_output, extract_numbers_from_text

def test_validator_passes_valid_marathi_output():
    facts = {
        "loan_details": {"emi_amount": 4650, "loan_amount": 50000},
        "bank_accounts": [
            {"account_last4": "9012", "bank_name": "HDFC"},
            {"account_last4": "4521", "bank_name": "SBI"}
        ]
    }
    allowed_actions = ["retry_mandate", "book_callback"]
    
    llm_output = {
        "explanation": "तुमच्या HDFC खात्यात शिल्लक नसल्याने अडचण झाली. आपण SBI खात्यावरून पुन्हा प्रयत्न करू शकता.",
        "proposed_action": "retry_mandate",
        "action_label": "SBI खात्यावरून प्रयत्न करा",
        "confidence": 0.95
    }
    
    res = validate_llm_output(llm_output, facts, allowed_actions, expected_language="mr")
    assert res.passed is True
    assert len(res.errors) == 0

def test_validator_rejects_ungrounded_amount():
    facts = {
        "loan_details": {"emi_amount": 4650, "loan_amount": 50000}
    }
    allowed_actions = ["retry_mandate"]
    
    # Model hallucinated ₹99,999 which does not exist in facts
    llm_output = {
        "explanation": "तुमचे ₹99999 चे कर्ज मंजूर झाले आहे.",
        "proposed_action": "retry_mandate",
        "action_label": "पुढे जा"
    }
    
    res = validate_llm_output(llm_output, facts, allowed_actions, expected_language="mr")
    assert res.passed is False
    assert any("Ungrounded amount" in err for err in res.errors)

def test_validator_rejects_banned_phrases():
    facts = {"loan_details": {"loan_amount": 50000}}
    allowed_actions = ["retry_mandate"]
    
    # Model used banned phrase "guaranteed"
    llm_output = {
        "explanation": "Your loan approval is guaranteed once you retry.",
        "proposed_action": "retry_mandate",
        "action_label": "Retry"
    }
    
    res = validate_llm_output(llm_output, facts, allowed_actions, expected_language="en")
    assert res.passed is False
    assert any("Banned phrase detected" in err for err in res.errors)

def test_validator_rejects_unauthorized_action():
    facts = {"loan_details": {"loan_amount": 50000}}
    allowed_actions = ["retry_mandate"]
    
    # Model proposed "move_money" or "waive_charges"
    llm_output = {
        "explanation": "We will waive all charges for you.",
        "proposed_action": "waive_charges",
        "action_label": "Waive"
    }
    
    res = validate_llm_output(llm_output, facts, allowed_actions, expected_language="en")
    assert res.passed is False
    assert any("not in allowed actions" in err for err in res.errors)
