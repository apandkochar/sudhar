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

def test_asha_flow_end_to_end_with_three_reference_numbers():
    # 1. Trigger Event (EMI debited post-closure)
    event_payload = {
        "event_id": "EVT-ASHA-001",
        "event_type": "EMI_DEBITED_AFTER_CLOSURE",
        "customer_id": "CUST-ASHA-102",
        "timestamp": "2026-11-05T06:30:00Z",
        "payload": {
            "code": "LMS_POST_CLOSURE_DEBIT",
            "loan_id": "LN-ASHA-PERSONAL-150K",
            "closure_date": "2026-11-04",
            "debit_date": "2026-11-05",
            "excess_debit_amount": 4500,
            "bank_account_masked": "ICICI Bank ending 7810"
        }
    }
    
    resp = client.post("/api/events", json=event_payload)
    assert resp.status_code == 200, resp.text
    case = resp.json()
    
    case_id = case["case_id"]
    assert case["persona_id"] == "asha"
    assert case["language"] == "hi"
    assert case["status"] == "PROPOSED"
    assert case["proposed_action"] == "create_ticket"
    assert case["action_params"]["refund_amount"] == 4500
    assert case["action_params"]["account_last4"] == "7810"
    
    # Check visual data side-by-side closure vs debit
    assert "closure_event" in case["visual_data"]
    assert "erroneous_debit" in case["visual_data"]
    assert "04" in case["visual_data"]["closure_event"]["date"]
    assert "05" in case["visual_data"]["erroneous_debit"]["date"]
    assert "4,500" in case["visual_data"]["erroneous_debit"]["amount"]
    
    # 2. Customer confirms consent
    consent_payload = {
        "case_id": case_id,
        "action": "create_ticket",
        "consent_given": True,
        "selected_params": {
            "ticket_type": "REFUND_AND_NOC",
            "refund_amount": 4500,
            "account_last4": "7810"
        },
        "idempotency_key": "IDEMP-ASHA-001"
    }
    
    consent_resp = client.post("/api/consent", json=consent_payload)
    assert consent_resp.status_code == 200, consent_resp.text
    receipt = consent_resp.json()
    
    assert receipt["status"] == "SUCCESS"
    assert receipt["action"] == "create_ticket"
    
    # Verify all 3 reference IDs exist and are distinct
    ref_refund = receipt.get("refund_reference") or receipt.get("reference_id")
    ref_noc = receipt.get("noc_reference")
    ref_bureau = receipt.get("bureau_reference")
    
    assert ref_refund is not None and ref_refund.startswith("TKT-REF-")
    assert ref_noc is not None and ref_noc.startswith("NOC-REQ-")
    assert ref_bureau is not None and ref_bureau.startswith("BUR-REM-")
    assert len({ref_refund, ref_noc, ref_bureau}) == 3, "All 3 reference numbers must be distinct"
    
    # 3. Check case state is EXECUTED
    fetch_resp = client.get(f"/api/cases/{case_id}")
    assert fetch_resp.status_code == 200
    final_case = fetch_resp.json()
    assert final_case["status"] == "EXECUTED"
    assert final_case["receipt"]["refund_reference"] == ref_refund
    assert final_case["receipt"]["noc_reference"] == ref_noc
    assert final_case["receipt"]["bureau_reference"] == ref_bureau
