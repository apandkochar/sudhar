from fastapi.testclient import TestClient
import pytest
from src.app import app
from src.db import init_db, reset_db

@pytest.fixture(autouse=True)
def setup_clean_db():
    init_db()
    reset_db()
    yield
    reset_db()

client = TestClient(app)

def test_meena_disbursal_breakup_flow_end_to_end():
    # 1. Trigger Disbursal Credited Event
    event_payload = {
        "event_id": "EVT-MEENA-001",
        "event_type": "DISBURSAL_CREDITED",
        "customer_id": "CUST-MEENA-501",
        "timestamp": "2026-11-15T09:00:00Z",
        "payload": {
            "code": "LMS_DISBURSAL_BREAKUP",
            "loan_id": "LN-MEENA-100K",
            "approved_amount": 100000,
            "disbursed_amount": 96045,
            "bank_account_masked": "Bank of Maharashtra ending 4412"
        }
    }

    resp = client.post("/api/events", json=event_payload)
    assert resp.status_code == 200, resp.text
    case = resp.json()

    case_id = case["case_id"]
    assert case["persona_id"] == "meena"
    assert case["language"] == "mr"
    assert case["status"] == "PROPOSED"
    assert case["proposed_action"] == "send_breakup_and_documents"
    assert "send_breakup_and_documents" in case["allowed_actions"]
    assert "raise_insurance_cancellation_request" in case["allowed_actions"]

    # Check action params with computed deductions
    params = case["action_params"]
    assert params["approved_amount"] == 100000
    assert params["disbursed_amount"] == 96045
    assert params["total_deductions"] == 3955
    assert params["processing_fee"] == 2000
    assert params["processing_fee_gst"] == 360
    assert params["broken_period_interest"] == 395
    assert params["insurance_premium"] == 1200
    assert params["account_last4"] == "4412"

    # Check explanation message mentions deductions and no recommendation
    expl = case["cause_explanation"]
    assert "100000" in expl
    assert "96045" in expl
    assert "3955" in expl
    assert "2000" in expl
    assert "360" in expl
    assert "395" in expl
    assert "1200" in expl
    assert "चांगले आहे" not in expl
    assert "you should" not in expl

    # 2. Confirm Consent for primary action: send_breakup_and_documents
    consent_payload = {
        "case_id": case_id,
        "action": "send_breakup_and_documents",
        "consent_given": True,
        "selected_params": params,
        "idempotency_key": "IDEMP-MEENA-001"
    }

    consent_resp = client.post("/api/consent", json=consent_payload)
    assert consent_resp.status_code == 200, consent_resp.text
    receipt = consent_resp.json()

    assert receipt["status"] == "SUCCESS"
    assert receipt["action"] == "send_breakup_and_documents"
    assert receipt["reference_id"].startswith("DOC-BRK-")

    # 3. Check Case EXECUTED & Operator Console Trace line
    fetch_resp = client.get(f"/api/cases/{case_id}")
    assert fetch_resp.status_code == 200
    final_case = fetch_resp.json()
    assert final_case["status"] == "EXECUTED"

    # Check trace line in audit trail: "Support ticket avoided: disbursal amount query"
    audit_trail = final_case["audit_trail"]
    avoided_entry = next(
        (a for a in audit_trail if "Support ticket avoided: disbursal amount query" in a.get("details", {}).get("summary", "")),
        None
    )
    assert avoided_entry is not None, "Console trace must contain 'Support ticket avoided: disbursal amount query'"

def test_meena_secondary_option_insurance_cancellation_request():
    # Test customer choosing second option: raise_insurance_cancellation_request
    event_payload = {
        "event_id": "EVT-MEENA-002",
        "event_type": "DISBURSAL_CREDITED",
        "customer_id": "CUST-MEENA-501",
        "timestamp": "2026-11-15T09:30:00Z",
        "payload": {
            "code": "LMS_DISBURSAL_BREAKUP",
            "loan_id": "LN-MEENA-100K",
            "approved_amount": 100000,
            "disbursed_amount": 96045,
            "bank_account_masked": "Bank of Maharashtra ending 4412"
        }
    }

    resp = client.post("/api/events", json=event_payload)
    assert resp.status_code == 200
    case = resp.json()
    case_id = case["case_id"]

    # Customer chooses second option: raise_insurance_cancellation_request
    consent_payload = {
        "case_id": case_id,
        "action": "raise_insurance_cancellation_request",
        "consent_given": True,
        "selected_params": {
            "insurance_premium": 1200,
            "loan_id": "LN-MEENA-100K"
        },
        "idempotency_key": "IDEMP-MEENA-INS-002"
    }

    consent_resp = client.post("/api/consent", json=consent_payload)
    assert consent_resp.status_code == 200, consent_resp.text
    receipt = consent_resp.json()

    assert receipt["status"] == "SUCCESS"
    assert receipt["action"] == "raise_insurance_cancellation_request"
    assert receipt["reference_id"].startswith("INS-CAN-")
    assert receipt["insurance_premium"] == 1200
    assert "lender review" in receipt["message"].lower()

    # Check trace line in audit trail
    fetch_resp = client.get(f"/api/cases/{case_id}")
    final_case = fetch_resp.json()
    assert final_case["status"] == "EXECUTED"
    avoided_entry = next(
        (a for a in final_case["audit_trail"] if "Support ticket avoided: disbursal amount query" in a.get("details", {}).get("summary", "")),
        None
    )
    assert avoided_entry is not None
