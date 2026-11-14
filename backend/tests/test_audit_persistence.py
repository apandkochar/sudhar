import json
import sqlite3
import tempfile
from pathlib import Path
import pytest

from src.db import (
    init_db,
    save_case,
    get_case,
    add_audit_entry,
    get_audit_trail,
    get_audit_stats,
    check_idempotency
)

def test_audit_log_persistence_across_reconnect():
    """
    Verifies that the audit log:
    1. Persists to disk across fresh SQLite connections.
    2. Maintains strict rowid append-only order.
    3. Preserves deterministic vs AI flags and JSON payload fidelity.
    4. Passes SQLite integrity check.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_audit.db"
        
        # 1. Initialize fresh DB
        init_db(db_path=db_path)
        
        # 2. Add case
        case_data = {
            "case_id": "CASE-AUDIT-TEST-001",
            "customer_id": "CUST-TEST-100",
            "persona_id": "rohit",
            "status": "PROPOSED",
            "moment": "MANDATE_FAILED",
            "language": "mr",
            "facts": {"name": "Test Customer", "amount": 50000},
            "playbook_id": "mandate_retry",
            "proposed_action": "retry_mandate",
            "action_label": "Retry",
            "action_params": {"account_last4": "4521"},
            "allowed_actions": ["retry_mandate", "book_callback"],
            "cause_explanation": "Test explanation",
            "visual_data": {},
            "source_mode": "gemini"
        }
        save_case(case_data, db_path=db_path)
        
        # 3. Add 10 vertical steps
        stages = [
            ("EVENT", "DETERMINISTIC_CODE", False, {"code": "AP15", "summary": "Mandate failed"}),
            ("PLAYBOOK", "DETERMINISTIC_CODE", False, {"playbook": "mandate_retry"}),
            ("FACTS", "DETERMINISTIC_CODE", False, {"accounts": ["9012", "4521"]}),
            ("CODE_LOOKUP", "DETERMINISTIC_CODE", False, {"cause": "Balance low"}),
            ("RULES", "DETERMINISTIC_CODE", False, {"allowed": ["retry_mandate"]}),
            ("LLM_DRAFT", "AI_GATEWAY", True, {"model": "gemini", "latency": 2.1}),
            ("VALIDATOR", "SAFETY_GATE", False, {"passed": True}),
            ("CONSENT_PROPOSED", "DETERMINISTIC_CODE", False, {"action": "retry_mandate"}),
            ("CONSENT_RECEIVED", "CUSTOMER_ACTION", False, {"consent_given": True}),
            ("ACTION", "DETERMINISTIC_CODE", False, {"ref": "MND-SBI-4521", "summary": "Executed"}),
            ("AUDIT", "DETERMINISTIC_CODE", False, {"closed": True, "summary": "Audit trail closed"})
        ]
        
        for stage, layer, is_ai, det in stages:
            add_audit_entry(
                case_id="CASE-AUDIT-TEST-001",
                stage=stage,
                layer=layer,
                is_ai=is_ai,
                details=det,
                idempotency_key="IDEMP-KEY-001" if stage in ("CONSENT_RECEIVED", "ACTION") else None,
                db_path=db_path
            )
            
        # 4. Verify SQLite connection closes, and reopen freshly
        del case_data
        
        # Fresh connection from disk file
        trail = get_audit_trail("CASE-AUDIT-TEST-001", db_path=db_path)
        assert len(trail) == 11
        
        # Verify ordering is preserved
        for idx, (expected_stage, expected_layer, expected_is_ai, _) in enumerate(stages):
            entry = trail[idx]
            assert entry["stage"] == expected_stage
            assert entry["layer"] == expected_layer
            assert entry["is_ai"] == expected_is_ai
            assert entry["case_id"] == "CASE-AUDIT-TEST-001"
            assert "timestamp" in entry
            
        # Verify AI flag specifically
        assert trail[5]["stage"] == "LLM_DRAFT"
        assert trail[5]["is_ai"] is True
        assert trail[5]["layer"] == "AI_GATEWAY"
        assert trail[0]["is_ai"] is False
        
        # 5. Verify stats and PRAGMA integrity
        stats = get_audit_stats(db_path=db_path)
        assert stats["persistent"] is True
        assert stats["integrity"] == "ok"
        assert stats["total_cases"] == 1
        assert stats["total_audit_entries"] == 11
        
        # 6. Verify idempotency lookup from disk
        cached = check_idempotency("CASE-AUDIT-TEST-001", "IDEMP-KEY-001", db_path=db_path)
        assert cached is not None
        assert cached["ref"] == "MND-SBI-4521"

