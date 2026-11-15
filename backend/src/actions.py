import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from src.db import add_audit_entry, check_idempotency, get_case, save_case

ALLOWED_ACTIONS = {
    "retry_mandate",
    "send_vkyc_resume_link",
    "create_ticket",
    "request_noc",
    "request_bureau_correction",
    "set_reminder",
    "book_callback",
    "send_breakup_and_documents",
    "raise_insurance_cancellation_request"
}

class ActionSecurityError(Exception):
    pass

def simulate_tool_execution(
    action: str,
    case_id: str,
    customer_id: str,
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Simulates tool execution behind the consent gate.
    All actions are allowlisted and simulated. No money is moved.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    suffix = uuid.uuid4().hex[:6].upper()
    
    if action == "retry_mandate":
        account_last4 = params.get("account_last4", "4521")
        bank_name = params.get("bank_name", "State Bank of India")
        return {
            "status": "SUCCESS",
            "action": action,
            "reference_id": f"MND-SBI-{account_last4}-{suffix}",
            "bank_account": f"{bank_name} ending {account_last4}",
            "registration_status": "ACTIVE",
            "message": "e-Mandate registration successfully initiated on eligible account",
            "executed_at": now_iso
        }
    elif action == "create_ticket":
        ticket_type = params.get("ticket_type", "REFUND_AND_NOC")
        refund_amount = params.get("refund_amount", 4500)
        ref_ticket = f"TKT-REF-{suffix}"
        ref_noc = f"NOC-REQ-{uuid.uuid4().hex[:6].upper()}"
        ref_bureau = f"BUR-REM-{uuid.uuid4().hex[:6].upper()}"
        return {
            "status": "SUCCESS",
            "action": action,
            "reference_id": ref_ticket,
            "refund_reference": ref_ticket,
            "noc_reference": ref_noc,
            "bureau_reference": ref_bureau,
            "ticket_type": ticket_type,
            "refund_amount": refund_amount,
            "refund_sla": "3-5 business days to ICICI Bank ending 7810",
            "noc_status": "QUEUED_FOR_DISPATCH (within 24 hours)",
            "bureau_status": "SCHEDULED (next lender reporting cycle)",
            "bureau_reminder_date": "15 Nov 2026",
            "message": "3 actions authorized: Refund ticket raised, NOC queued, and bureau check scheduled",
            "executed_at": now_iso
        }
    elif action == "send_vkyc_resume_link":
        mobile_last4 = params.get("mobile_last4", "3210")
        return {
            "status": "SUCCESS",
            "action": action,
            "reference_id": f"VKYC-SMS-{suffix}",
            "mobile": f"ending {mobile_last4}",
            "link_validity": "72 hours",
            "channels": ["SMS", "WhatsApp"],
            "message": f"Direct video KYC resume link dispatched to mobile ending {mobile_last4}",
            "executed_at": now_iso
        }
    elif action == "request_noc":
        return {
            "status": "SUCCESS",
            "action": action,
            "reference_id": f"NOC-REQ-{suffix}",
            "dispatch_sla": "24 hours",
            "executed_at": now_iso
        }
    elif action == "request_bureau_correction":
        return {
            "status": "SUCCESS",
            "action": action,
            "reference_id": f"BUR-COR-{suffix}",
            "update_cycle": "Next lender reporting cycle (by 15th)",
            "executed_at": now_iso
        }
    elif action == "set_reminder":
        days = params.get("days", 90)
        return {
            "status": "SUCCESS",
            "action": action,
            "reference_id": f"REM-{suffix}",
            "reminder_days": days,
            "message": f"Eligibility re-check reminder set for {days} days from today",
            "executed_at": now_iso
        }
    elif action == "book_callback":
        slot = params.get("slot", "Earliest available")
        return {
            "status": "SUCCESS",
            "action": action,
            "reference_id": f"CALL-{suffix}",
            "slot": slot,
            "message": "Senior loan specialist will call on your registered mobile number",
            "executed_at": now_iso
        }
    elif action == "send_breakup_and_documents":
        approved_amount = params.get("approved_amount", 100000)
        disbursed_amount = params.get("disbursed_amount", 96045)
        total_deductions = params.get("total_deductions", 3955)
        account_last4 = params.get("account_last4", "4412")
        ref_doc = f"DOC-BRK-{suffix}"
        return {
            "status": "SUCCESS",
            "action": action,
            "reference_id": ref_doc,
            "approved_amount": approved_amount,
            "disbursed_amount": disbursed_amount,
            "total_deductions": total_deductions,
            "account_last4": account_last4,
            "delivery_channel": "Registered Email & App Inbox",
            "message": "Full deduction breakup and official loan documents dispatched to your inbox",
            "executed_at": now_iso
        }
    elif action == "raise_insurance_cancellation_request":
        insurance_premium = params.get("insurance_premium", 1200)
        ref_ins = f"INS-CAN-{suffix}"
        return {
            "status": "SUCCESS",
            "action": action,
            "reference_id": ref_ins,
            "insurance_premium": insurance_premium,
            "decision_policy": "Lender decides within 48-72 hours",
            "message": "Insurance cancellation request submitted to Nimbus Finance. Decision pending lender review.",
            "executed_at": now_iso
        }
    else:
        raise ActionSecurityError(f"Action '{action}' is not in the security allowlist")

def process_consent(
    case_id: str,
    action: str,
    consent_given: bool,
    selected_params: Dict[str, Any],
    idempotency_key: Optional[str] = None,
    db_path: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Executes the consent gate state machine.
    Enforces allowlist, idempotency, server-side customer ID injection, and audit logging.
    """
    case = get_case(case_id, db_path=db_path)
    if not case:
        raise ActionSecurityError(f"Case '{case_id}' not found")
        
    customer_id = case["customer_id"]
    
    # 1. Action Allowlist check
    if action not in ALLOWED_ACTIONS:
        add_audit_entry(
            case_id, "ACTION", "SAFETY_GATE", False,
            {
                "summary": f"Disallowed action '{action}' blocked by safety gate",
                "error": f"Disallowed action '{action}' blocked by security gate"
            },
            idempotency_key=idempotency_key, db_path=db_path
        )
        raise ActionSecurityError(f"Action '{action}' is strictly forbidden by policy allowlist")
        
    # 2. Check if action is in case's allowed_actions
    if action not in case.get("allowed_actions", []):
        raise ActionSecurityError(f"Action '{action}' is not permitted for case {case_id}")

    # 3. Check customer consent
    if not consent_given:
        case["status"] = "DECLINED"
        save_case(case, db_path=db_path)
        add_audit_entry(
            case_id, "CONSENT_RECEIVED", "CUSTOMER_ACTION", False,
            {
                "summary": f"Customer declined {action}",
                "consent_given": False,
                "action": action,
                "note": "Customer declined proposed action"
            },
            idempotency_key=idempotency_key, db_path=db_path
        )
        return {
            "case_id": case_id,
            "status": "DECLINED",
            "action": action,
            "message": "Action cancelled as requested by customer"
        }

    # 4. Consent given: Log consent
    add_audit_entry(
        case_id, "CONSENT_RECEIVED", "CUSTOMER_ACTION", False,
        {
            "summary": f"Customer confirmed {action} via tap",
            "consent_given": True,
            "action": action,
            "selected_params": selected_params,
            "confirmed_at": datetime.now(timezone.utc).isoformat()
        },
        idempotency_key=idempotency_key, db_path=db_path
    )

    # 5. Check Idempotency Key
    effective_idempotency_key = idempotency_key or f"IDEMP-{case_id}-{action}"
    cached_execution = check_idempotency(case_id, effective_idempotency_key, db_path=db_path)
    if cached_execution:
        add_audit_entry(
            case_id, "AUDIT", "DETERMINISTIC_CODE", False,
            {
                "summary": "Duplicate request blocked · Returned cached receipt",
                "idempotency_hit": True,
                "key": effective_idempotency_key,
                "message": "Duplicate request detected; returned existing execution receipt"
            },
            idempotency_key=effective_idempotency_key, db_path=db_path
        )
        return cached_execution

    # 6. Execute simulated tool
    execution_result = simulate_tool_execution(action, case_id, customer_id, selected_params)
    action_summary = f"{action} executed · Ref {execution_result.get('reference_id', 'DONE')}"

    # 7. Record action execution in audit log
    execution_result_with_summary = dict(execution_result)
    execution_result_with_summary["summary"] = action_summary
    add_audit_entry(
        case_id, "ACTION", "DETERMINISTIC_CODE", False,
        execution_result_with_summary,
        idempotency_key=effective_idempotency_key, db_path=db_path
    )

    # 8. Update case status & receipt
    case["status"] = "EXECUTED"
    case["receipt"] = execution_result
    save_case(case, db_path=db_path)

    # 9. Record final audit entry
    add_audit_entry(
        case_id, "AUDIT", "DETERMINISTIC_CODE", False,
        {
            "summary": "Case closed · Receipt logged",
            "final_status": "EXECUTED",
            "reference_id": execution_result.get("reference_id"),
            "audit_closed": True
        },
        idempotency_key=effective_idempotency_key, db_path=db_path
    )

    # Console trace line: when resolved, trace line "Support ticket avoided: disbursal amount query"
    if action in ["send_breakup_and_documents", "raise_insurance_cancellation_request"] or case.get("moment") == "DISBURSAL_CREDITED":
        add_audit_entry(
            case_id, "RESOLUTION", "DETERMINISTIC_CODE", False,
            {
                "summary": "Support ticket avoided: disbursal amount query",
                "ticket_avoided": True,
                "category": "disbursal_amount_query",
                "resolved_at": datetime.now(timezone.utc).isoformat()
            },
            idempotency_key=f"{effective_idempotency_key}-AVOIDED", db_path=db_path
        )

    return execution_result
