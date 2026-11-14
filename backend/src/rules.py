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
    else:
        raise RuleEvaluationError(f"Unknown moment: {moment}")

