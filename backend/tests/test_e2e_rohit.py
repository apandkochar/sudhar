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

def test_rohit_hero_flow_end_to_end():
    # 1. Trigger Event (e-Mandate fails with AP15)
    event_payload = {
        "event_id": "EVT-ROHIT-001",
        "event_type": "MANDATE_FAILED",
        "customer_id": "CUST-ROHIT-401",
        "timestamp": "2026-11-14T10:15:30Z",
        "payload": {
            "code": "AP15",
            "attempt": 1,
            "bank_account_masked": "HDFC Bank ending 9012",
            "loan_id": "LN-ROHIT-50K"
        }
    }
    
    resp = client.post("/api/events", json=event_payload)
    assert resp.status_code == 200, resp.text
    case = resp.json()
    
    case_id = case["case_id"]
    assert case_id == "CASE-EVT-ROHIT-001"
    assert case["persona_id"] == "rohit"
    assert case["language"] == "mr"
    assert case["status"] == "PROPOSED"
    assert case["proposed_action"] == "retry_mandate"
    assert case["action_params"]["account_last4"] == "4521"
    assert "HDFC" in case["cause_explanation"]
    assert "SBI" in case["cause_explanation"]
    assert "retry_mandate" in case["allowed_actions"]
    assert "book_callback" in case["allowed_actions"]
    
    # Check visual data
    assert case["visual_data"]["failed_account"]["last4"] == "9012"
    assert case["visual_data"]["suggested_account"]["last4"] == "4521"
    
    # Check vertical audit trail up to proposal
    stages = [a["stage"] for a in case["audit_trail"]]
    assert stages == [
        "EVENT",
        "PLAYBOOK",
        "FACTS",
        "CODE_LOOKUP",
        "RULES",
        "LLM_DRAFT",
        "VALIDATOR",
        "CONSENT_PROPOSED"
    ]
    
    # Ensure all steps are flagged as deterministic code (not AI model)
    for entry in case["audit_trail"]:
        assert entry["is_ai"] is False
    
    # 2. Customer confirms on the Consent Card
    consent_payload = {
        "case_id": case_id,
        "action": "retry_mandate",
        "consent_given": True,
        "selected_params": {
            "account_last4": "4521",
            "bank_name": "State Bank of India (SBI)"
        },
        "idempotency_key": "IDEMP-ROHIT-MANDATE-001"
    }
    
    consent_resp = client.post("/api/consent", json=consent_payload)
    assert consent_resp.status_code == 200, consent_resp.text
    receipt = consent_resp.json()
    assert receipt["status"] == "SUCCESS"
    assert receipt["action"] == "retry_mandate"
    assert "MND-SBI-4521-" in receipt["reference_id"]
    
    # 3. Fetch Case and verify full trace
    fetch_resp = client.get(f"/api/cases/{case_id}")
    assert fetch_resp.status_code == 200
    final_case = fetch_resp.json()
    assert final_case["status"] == "EXECUTED"
    assert final_case["receipt"]["reference_id"] == receipt["reference_id"]
    
    final_stages = [a["stage"] for a in final_case["audit_trail"]]
    assert "CONSENT_RECEIVED" in final_stages
    assert "ACTION" in final_stages
    assert "AUDIT" in final_stages
