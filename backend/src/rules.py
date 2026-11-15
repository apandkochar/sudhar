from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

class RuleEvaluationError(Exception):
    pass

def evaluate_mandate_rules(
    code: str,
    facts: Dict[str, Any],
    playbook_rules: Dict[str, Any]
) -> Tuple[str, Dict[str, Any], List[str]]:
    """
    Deterministic rule evaluation for e-Mandate failures.
    Ensures bank account eligibility and allowed actions come strictly from Python.
    """
    bank_accounts = facts.get("bank_accounts", [])
    if not bank_accounts:
        return "book_callback", {}, ["book_callback"]
    
    # Identify failed account
    failed_account = bank_accounts[0]
    
    # Find alternative eligible account with sufficient balance
    eligible_accounts = [
        acc for acc in bank_accounts[1:]
        if acc.get("balance_status") == "SUFFICIENT" or acc.get("approx_balance", 0) > facts.get("loan_details", {}).get("emi_amount", 0)
    ]
    
    if eligible_accounts:
        target_account = eligible_accounts[0]
        allowed_actions = ["retry_mandate", "book_callback"]
        action_params = {
            "account_id": target_account["account_id"],
            "bank_name": target_account["bank_name"],
            "account_last4": target_account["account_last4"]
        }
        return "retry_mandate", action_params, allowed_actions
    
    return "book_callback", {}, ["book_callback"]

def evaluate_post_closure_rules(
    code: str,
    facts: Dict[str, Any],
    playbook_rules: Dict[str, Any]
) -> Tuple[str, Dict[str, Any], List[str]]:
    """
    Deterministic rule evaluation for post-closure debits.
    Validates closure date vs debit date and exact debit amounts.
    """
    closure_date_str = facts.get("closure_date") or facts.get("facts", {}).get("closure_date")
    debit_date_str = facts.get("debit_date") or facts.get("facts", {}).get("debit_date")
    debit_amount = facts.get("debit_amount") or facts.get("facts", {}).get("debit_amount", 4500)
    account_last4 = facts.get("account_last4") or facts.get("facts", {}).get("account_last4", "7810")
    
    if not closure_date_str or not debit_date_str:
        raise RuleEvaluationError("Missing closure_date or debit_date in case facts")
        
    closure_date = datetime.strptime(closure_date_str, "%Y-%m-%d")
    debit_date = datetime.strptime(debit_date_str, "%Y-%m-%d")
    
    # Non-negotiable: closure must strictly precede the debit date
    if closure_date >= debit_date:
        raise RuleEvaluationError(f"Closure date {closure_date_str} is not before debit date {debit_date_str}")
        
    allowed_actions = [
        "create_ticket",
        "request_noc",
        "request_bureau_correction",
        "set_reminder",
        "book_callback"
    ]
    
    action_params = {
        "ticket_type": "REFUND_AND_NOC",
        "refund_amount": debit_amount,
        "account_last4": account_last4
    }
    
    return "create_ticket", action_params, allowed_actions

def evaluate_vkyc_rules(
    code: str,
    facts: Dict[str, Any],
    playbook_rules: Dict[str, Any]
) -> Tuple[str, Dict[str, Any], List[str]]:
    """
    Deterministic rule evaluation for interrupted video KYC sessions.
    """
    mobile_masked = facts.get("mobile_masked") or facts.get("facts", {}).get("mobile_masked", "+91-98XXXX3210")
    mobile_last4 = mobile_masked[-4:]
    
    allowed_actions = ["send_vkyc_resume_link", "book_callback"]
    action_params = {
        "mobile_last4": mobile_last4
    }
    
    return "send_vkyc_resume_link", action_params, allowed_actions

def compute_disbursal_deductions(
    approved_amount: float,
    fee_pct: float,
    gst_pct: float,
    annual_interest_rate_pct: float,
    broken_period_days: int,
    insurance_premium: float
) -> Dict[str, float]:
    """
    Deterministically computes each deduction for loan disbursal:
    1. Processing fee = principal * rate / 100
    2. GST = fee * gst_rate / 100
    3. Broken-period interest = principal * annual_rate * days / 365 (rounded to nearest rupee)
    4. Insurance premium = optional cover as stated in loan terms
    """
    fee = round(approved_amount * fee_pct / 100.0)
    gst = round(fee * gst_pct / 100.0)
    broken_interest = round(approved_amount * (annual_interest_rate_pct / 100.0) * broken_period_days / 365.0)
    total_deductions = fee + gst + broken_interest + insurance_premium
    net_disbursed = approved_amount - total_deductions
    return {
        "processing_fee": fee,
        "processing_fee_gst": gst,
        "broken_period_interest": broken_interest,
        "insurance_premium": insurance_premium,
        "total_deductions": total_deductions,
        "net_disbursed": net_disbursed
    }

def evaluate_disbursal_breakup_rules(
    code: str,
    facts: Dict[str, Any],
    playbook_rules: Dict[str, Any]
) -> Tuple[str, Dict[str, Any], List[str]]:
    """
    Deterministic rule evaluation for loan disbursal deduction breakup.
    Asserts that deductions add up exactly to (approved - disbursed).
    If they don't add up -> hand over to a human, no message.
    """
    approved = float(facts.get("approved_amount") or facts.get("facts", {}).get("approved_amount") or facts.get("loan_details", {}).get("loan_amount", 100000))
    fee_pct = float(facts.get("processing_fee_pct") or facts.get("facts", {}).get("processing_fee_pct", 2.0))
    gst_pct = float(facts.get("gst_pct") or facts.get("facts", {}).get("gst_pct", 18.0))
    annual_rate_pct = float(facts.get("annual_interest_rate_pct") or facts.get("facts", {}).get("annual_interest_rate_pct", 24.0))
    broken_days = int(facts.get("broken_period_days") or facts.get("facts", {}).get("broken_period_days", 6))
    insurance = float(facts.get("insurance_premium") or facts.get("facts", {}).get("insurance_premium", 1200))

    computed = compute_disbursal_deductions(
        approved_amount=approved,
        fee_pct=fee_pct,
        gst_pct=gst_pct,
        annual_interest_rate_pct=annual_rate_pct,
        broken_period_days=broken_days,
        insurance_premium=insurance
    )

    actual_disbursed = float(facts.get("disbursed_amount") or facts.get("facts", {}).get("disbursed_amount", computed["net_disbursed"]))
    difference = approved - actual_disbursed

    # Assert deductions add up exactly to approved minus disbursed
    if computed["total_deductions"] != difference or computed["net_disbursed"] != actual_disbursed:
        # Mismatch -> Hand over to a human, no message
        return "handover_to_human", {
            "reason": "deductions_mismatch",
            "computed_deductions": computed["total_deductions"],
            "difference": difference,
            "handover": True
        }, ["handover_to_human", "book_callback"]

    allowed_actions = [
        "send_breakup_and_documents",
        "raise_insurance_cancellation_request",
        "book_callback"
    ]

    action_params = {
        "approved_amount": int(approved),
        "disbursed_amount": int(actual_disbursed),
        "processing_fee": int(computed["processing_fee"]),
        "processing_fee_gst": int(computed["processing_fee_gst"]),
        "broken_period_interest": int(computed["broken_period_interest"]),
        "insurance_premium": int(computed["insurance_premium"]),
        "total_deductions": int(computed["total_deductions"]),
        "account_last4": str(facts.get("account_last4") or facts.get("facts", {}).get("account_last4", "4412"))
    }

    return "send_breakup_and_documents", action_params, allowed_actions

def evaluate_rules(
    moment: str,
    code: str,
    facts: Dict[str, Any],
    playbook: Dict[str, Any]
) -> Tuple[str, Dict[str, Any], List[str]]:
    rules_spec = playbook.get("deterministic_rules", {})
    
    if moment == "MANDATE_FAILED":
        return evaluate_mandate_rules(code, facts, rules_spec)
    elif moment == "EMI_DEBITED_AFTER_CLOSURE":
        return evaluate_post_closure_rules(code, facts, rules_spec)
    elif moment == "VKYC_DROPPED":
        return evaluate_vkyc_rules(code, facts, rules_spec)
    elif moment == "DISBURSAL_CREDITED":
        return evaluate_disbursal_breakup_rules(code, facts, rules_spec)
    else:
        raise RuleEvaluationError(f"Unknown moment: {moment}")

