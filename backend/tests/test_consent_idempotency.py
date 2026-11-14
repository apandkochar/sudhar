import pytest
from pathlib import Path
from src.actions import ActionSecurityError, process_consent
from src.db import init_db, save_case, get_case, get_audit_trail

@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_sudhaar.db"
    init_db(db_file)
    return db_file

def test_consent_security_blocks_disallowed_action(temp_db):
    case_data = {
        "case_id": "CASE-TEST-01",
        "customer_id": "CUST-TEST",
        "persona_id": "rohit",
        "status": "PROPOSED",
        "moment": "MANDATE_FAILED",
        "language": "mr",
        "facts": {},
        "playbook_id": "PB-01",
        "allowed_actions": ["retry_mandate", "book_callback"]
    }
    save_case(case_data, db_path=temp_db)
    
    # Attempting an action outside the global allowlist (e.g. move_money, waive_charges)
    with pytest.raises(ActionSecurityError) as exc_info:
        process_consent(
            case_id="CASE-TEST-01",
            action="waive_charges",
            consent_given=True,
            selected_params={},
            db_path=temp_db
        )
    assert "strictly forbidden" in str(exc_info.value)

def test_consent_declined_updates_case_status(temp_db):
    case_data = {
        "case_id": "CASE-TEST-02",
        "customer_id": "CUST-TEST",
        "persona_id": "rohit",
        "status": "PROPOSED",
        "moment": "MANDATE_FAILED",
        "language": "mr",
        "facts": {},
        "playbook_id": "PB-01",
        "allowed_actions": ["retry_mandate", "book_callback"]
    }
    save_case(case_data, db_path=temp_db)
    
    res = process_consent(
        case_id="CASE-TEST-02",
        action="retry_mandate",
        consent_given=False,
        selected_params={},
        db_path=temp_db
    )
    
    assert res["status"] == "DECLINED"
    updated_case = get_case("CASE-TEST-02", db_path=temp_db)
    assert updated_case["status"] == "DECLINED"

def test_idempotency_prevents_duplicate_action_execution(temp_db):
    case_data = {
        "case_id": "CASE-TEST-03",
        "customer_id": "CUST-TEST",
        "persona_id": "rohit",
        "status": "PROPOSED",
        "moment": "MANDATE_FAILED",
        "language": "mr",
        "facts": {},
        "playbook_id": "PB-01",
        "allowed_actions": ["retry_mandate", "book_callback"]
    }
    save_case(case_data, db_path=temp_db)
    
    key = "IDEMP-ROHIT-MANDATE-ATTEMPT-1"
    
    # First execution
    res1 = process_consent(
        case_id="CASE-TEST-03",
        action="retry_mandate",
        consent_given=True,
        selected_params={"account_last4": "4521", "bank_name": "State Bank of India"},
        idempotency_key=key,
        db_path=temp_db
    )
    assert res1["status"] == "SUCCESS"
    ref_id = res1["reference_id"]
    
    # Second execution (e.g. accidental double tap)
    res2 = process_consent(
        case_id="CASE-TEST-03",
        action="retry_mandate",
        consent_given=True,
        selected_params={"account_last4": "4521", "bank_name": "State Bank of India"},
        idempotency_key=key,
        db_path=temp_db
    )
    # Must return identical execution receipt without re-running
    assert res2["reference_id"] == ref_id
    
    # Check audit log: should contain idempotency hit
    trail = get_audit_trail("CASE-TEST-03", db_path=temp_db)
    idemp_hits = [t for t in trail if t["details"].get("idempotency_hit")]
    assert len(idemp_hits) == 1

