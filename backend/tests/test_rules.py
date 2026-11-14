import pytest
from src.rules import evaluate_mandate_rules, evaluate_post_closure_rules, evaluate_vkyc_rules, RuleEvaluationError

def test_mandate_rules_selects_sufficient_account():
    facts = {
        "loan_details": {"emi_amount": 4650},
        "bank_accounts": [
            {
                "account_id": "ACC-HDFC-9012",
                "bank_name": "HDFC Bank",
                "account_last4": "9012",
                "balance_status": "INSUFFICIENT",
                "approx_balance": 85
            },
            {
                "account_id": "ACC-SBI-4521",
                "bank_name": "State Bank of India (SBI)",
                "account_last4": "4521",
                "balance_status": "SUFFICIENT",
                "approx_balance": 14200
            }
        ]
    }
    
    action, params, allowed = evaluate_mandate_rules("AP15", facts, {})
    assert action == "retry_mandate"
    assert "retry_mandate" in allowed
    assert "book_callback" in allowed
    assert params["account_last4"] == "4521"
    assert params["bank_name"] == "State Bank of India (SBI)"

def test_mandate_rules_falls_back_to_callback_if_no_account():
    facts = {
        "loan_details": {"emi_amount": 4650},
        "bank_accounts": [
            {
                "account_id": "ACC-HDFC-9012",
                "bank_name": "HDFC Bank",
                "account_last4": "9012",
                "balance_status": "INSUFFICIENT"
            }
        ]
    }
    action, params, allowed = evaluate_mandate_rules("AP15", facts, {})
    assert action == "book_callback"
    assert allowed == ["book_callback"]

def test_post_closure_rules_validates_dates():
    # Valid: closure on Nov 4, debit on Nov 5
    facts = {
        "closure_date": "2026-11-04",
        "debit_date": "2026-11-05",
        "debit_amount": 4500,
        "account_last4": "7810"
    }
    action, params, allowed = evaluate_post_closure_rules("LMS_POST_CLOSURE_DEBIT", facts, {})
    assert action == "create_ticket"
    assert "create_ticket" in allowed
    assert "request_noc" in allowed
    assert params["refund_amount"] == 4500
    assert params["ticket_type"] == "REFUND_AND_NOC"

def test_post_closure_rules_rejects_invalid_date_order():
    # Invalid: closure on Nov 5, debit on Nov 4
    facts = {
        "closure_date": "2026-11-05",
        "debit_date": "2026-11-04",
        "debit_amount": 4500,
        "account_last4": "7810"
    }
    with pytest.raises(RuleEvaluationError):
        evaluate_post_closure_rules("LMS_POST_CLOSURE_DEBIT", facts, {})

def test_vkyc_rules_extracts_mobile():
    facts = {
        "mobile_masked": "+91-98XXXX3210"
    }
    action, params, allowed = evaluate_vkyc_rules("VKYC_NET_DROP", facts, {})
    assert action == "send_vkyc_resume_link"
    assert params["mobile_last4"] == "3210"
    assert "send_vkyc_resume_link" in allowed
