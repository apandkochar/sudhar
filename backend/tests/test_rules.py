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

def test_disbursal_deductions_math():
    from src.rules import compute_disbursal_deductions, evaluate_disbursal_breakup_rules
    # Approved ₹1,00,000; processing fee 2% + 18% GST; interest 24% p.a.; 6 broken-period days; insurance ₹1,200
    res = compute_disbursal_deductions(
        approved_amount=100000,
        fee_pct=2.0,
        gst_pct=18.0,
        annual_interest_rate_pct=24.0,
        broken_period_days=6,
        insurance_premium=1200
    )
    assert res["processing_fee"] == 2000
    assert res["processing_fee_gst"] == 360
    assert res["broken_period_interest"] == 395 # round(100000 * 0.24 * 6 / 365) = round(394.52) = 395
    assert res["insurance_premium"] == 1200
    assert res["total_deductions"] == 3955
    assert res["net_disbursed"] == 96045

    # Check deductions add up exactly to approved minus disbursed
    assert res["total_deductions"] == 100000 - res["net_disbursed"]

    facts = {
        "approved_amount": 100000,
        "processing_fee_pct": 2.0,
        "gst_pct": 18.0,
        "annual_interest_rate_pct": 24.0,
        "broken_period_days": 6,
        "insurance_premium": 1200,
        "disbursed_amount": 96045,
        "account_last4": "4412"
    }
    action, params, allowed = evaluate_disbursal_breakup_rules("LMS_DISBURSAL_BREAKUP", facts, {})
    assert action == "send_breakup_and_documents"
    assert params["approved_amount"] == 100000
    assert params["disbursed_amount"] == 96045
    assert params["total_deductions"] == 3955
    assert params["processing_fee"] == 2000
    assert params["processing_fee_gst"] == 360
    assert params["broken_period_interest"] == 395
    assert params["insurance_premium"] == 1200
    assert "send_breakup_and_documents" in allowed
    assert "raise_insurance_cancellation_request" in allowed

def test_disbursal_deductions_mismatch_triggers_human_handover():
    from src.rules import evaluate_disbursal_breakup_rules
    from src.orchestrator import process_event
    from src.schemas import EventRequest

    # Facts where actual disbursed amount does not match computed deductions
    facts = {
        "approved_amount": 100000,
        "processing_fee_pct": 2.0,
        "gst_pct": 18.0,
        "annual_interest_rate_pct": 24.0,
        "broken_period_days": 6,
        "insurance_premium": 1200,
        "disbursed_amount": 95000, # Mismatch: 100000 - 95000 = 5000 != 3955
        "account_last4": "4412"
    }
    action, params, allowed = evaluate_disbursal_breakup_rules("LMS_DISBURSAL_BREAKUP", facts, {})
    assert action == "handover_to_human"
    assert params["handover"] is True
    assert params["reason"] == "deductions_mismatch"
    assert "handover_to_human" in allowed

    # End-to-end check through orchestrator: handover status, no customer message
    evt = EventRequest(
        event_id="EVT-TEST-MISMATCH-01",
        event_type="DISBURSAL_CREDITED",
        customer_id="CUST-MEENA-501",
        timestamp="2026-11-15T09:00:00Z",
        payload={
            "code": "LMS_DISBURSAL_BREAKUP",
            "approved_amount": 100000,
            "disbursed_amount": 95000, # Mismatch
            "bank_account_masked": "Bank of Maharashtra ending 4412"
        }
    )
    case = process_event(evt)
    assert case["status"] == "HANDOVER"
    assert case["proposed_action"] == "handover_to_human"
    assert case["cause_explanation"] == ""
    # Verify audit trail logs human handover with no message
    handover_audit = next((a for a in case["audit_trail"] if a["stage"] == "HUMAN_HANDOVER"), None)
    assert handover_audit is not None
    assert handover_audit["details"]["no_message"] is True


